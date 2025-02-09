package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	"os"
	"time"
)

// Structures pour l'extraction
type ExtractionRequest struct {
	FilePath string `json:"file_path"`
}

type ExtractionResponse struct {
	Text string `json:"text"`
}

// Structures pour la labellisation
type LabellingRequest struct {
	Text string `json:"text"`
}

type Entity struct {
	Text  string `json:"text"`
	Label string `json:"label"`
}

type LabellingResponse struct {
	ExtractedText string   `json:"extracted_text"`
	Entities      []Entity `json:"entities"`
}

// Structures pour l'orchestration (entrée)
type OrchestrateRequest struct {
	FilePath        string   `json:"file_path"`
	ForbiddenLabels []string `json:"forbidden_labels"`
}

// Structure pour le payload envoyé au service de caviardage
type RedactionRequest struct {
	FilePath        string   `json:"file_path"`
	Entities        []Entity `json:"entities"`
	ForbiddenLabels []string `json:"forbidden_labels"`
}

// Structure pour la réponse du service de caviardage
type RedactionResponse struct {
	Message    string `json:"message"`
	OutputFile string `json:"output_file"`
}

// callExtractionAPI appelle le service d'extraction.
func callExtractionAPI(filePath string, extractionAddr string) (*ExtractionResponse, error) {
	reqBody := ExtractionRequest{FilePath: filePath}
	jsonReq, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("erreur lors du marshaling de la requête extraction : %v", err)
	}

	resp, err := http.Post("http://"+extractionAddr+"/extract", "application/json", bytes.NewBuffer(jsonReq))
	if err != nil {
		return nil, fmt.Errorf("erreur lors de l'appel à l'API extraction : %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := ioutil.ReadAll(resp.Body)
		return nil, fmt.Errorf("l'API extraction a renvoyé le statut %d: %s", resp.StatusCode, string(bodyBytes))
	}

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("erreur lors de la lecture de la réponse extraction : %v", err)
	}

	var extractionResp ExtractionResponse
	if err := json.Unmarshal(body, &extractionResp); err != nil {
		return nil, fmt.Errorf("erreur lors du unmarshaling de la réponse extraction : %v", err)
	}
	return &extractionResp, nil
}

// callLabellingAPI appelle le service de labellisation.
func callLabellingAPI(text string, labellingAddr string) (*LabellingResponse, error) {
	reqBody := LabellingRequest{Text: text}
	jsonReq, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("erreur lors du marshaling de la requête labelling : %v", err)
	}

	resp, err := http.Post("http://"+labellingAddr+"/label", "application/json", bytes.NewBuffer(jsonReq))
	if err != nil {
		return nil, fmt.Errorf("erreur lors de l'appel à l'API labelling : %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := ioutil.ReadAll(resp.Body)
		return nil, fmt.Errorf("l'API labelling a renvoyé le statut %d: %s", resp.StatusCode, string(bodyBytes))
	}

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("erreur lors de la lecture de la réponse labelling : %v", err)
	}

	var labellingResp LabellingResponse
	if err := json.Unmarshal(body, &labellingResp); err != nil {
		return nil, fmt.Errorf("erreur lors du unmarshaling de la réponse labelling : %v", err)
	}
	return &labellingResp, nil
}

// callRedactionAPI appelle le service Python de caviardage.
func callRedactionAPI(redactReq RedactionRequest, redactionAddr string) (*RedactionResponse, error) {
	jsonReq, err := json.Marshal(redactReq)
	if err != nil {
		return nil, fmt.Errorf("erreur lors du marshaling de la requête redaction : %v", err)
	}

	resp, err := http.Post("http://"+redactionAddr+"/anonymize", "application/json", bytes.NewBuffer(jsonReq))
	if err != nil {
		return nil, fmt.Errorf("erreur lors de l'appel à l'API redaction : %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := ioutil.ReadAll(resp.Body)
		return nil, fmt.Errorf("l'API redaction a renvoyé le statut %d: %s", resp.StatusCode, string(bodyBytes))
	}

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("erreur lors de la lecture de la réponse redaction : %v", err)
	}

	var redactionResp RedactionResponse
	if err := json.Unmarshal(body, &redactionResp); err != nil {
		return nil, fmt.Errorf("erreur lors du unmarshaling de la réponse redaction : %v", err)
	}
	return &redactionResp, nil
}

// handlerOrchestrate reçoit la requête d'entrée, enchaîne extraction, labellisation, puis caviardage.
func handlerOrchestrate(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	var req OrchestrateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Requête invalide", http.StatusBadRequest)
		return
	}

	// Récupérer les adresses des services depuis les variables d'environnement
	extractionAddr := os.Getenv("EXTRACTION_SERVICE_ADDR")
	labellingAddr := os.Getenv("LABELLING_HOST") + ":" + os.Getenv("LABELLING_PORT")
	redactionAddr := os.Getenv("FLASK_SERVER_ADDR") + ":" + os.Getenv("FLASK_SERVER_PORT")

	// Appel au service d'extraction
	extractionResp, err := callExtractionAPI(req.FilePath, extractionAddr)
	if err != nil {
		http.Error(w, fmt.Sprintf("Erreur Extraction API : %v", err), http.StatusInternalServerError)
		return
	}

	// Appel au service de labellisation avec le texte extrait
	labellingResp, err := callLabellingAPI(extractionResp.Text, labellingAddr)
	if err != nil {
		http.Error(w, fmt.Sprintf("Erreur Labelling API : %v", err), http.StatusInternalServerError)
		return
	}

	// Construire le payload pour le service de caviardage
	redactPayload := RedactionRequest{
		FilePath:        req.FilePath,
		Entities:        labellingResp.Entities,
		ForbiddenLabels: req.ForbiddenLabels,
	}

	// Appel au service de caviardage (redaction) avec le payload construit
	redactionResp, err := callRedactionAPI(redactPayload, redactionAddr)
	if err != nil {
		http.Error(w, fmt.Sprintf("Erreur Redaction API : %v", err), http.StatusInternalServerError)
		return
	}

	// Retourner la réponse du service de caviardage
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(redactionResp); err != nil {
		http.Error(w, "Erreur lors de l'encodage de la réponse", http.StatusInternalServerError)
	}

	fmt.Printf("\n--\n\nFile: %s\nProcessing duration: %s\n", req.FilePath, time.Since(start))
}

// handlerLoadFile permet d'uploader un fichier et de l'enregistrer dans "../temp"
func handlerLoadFile(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Parse le formulaire multipart (limite de 10MB)
	err := r.ParseMultipartForm(10 << 20)
	if err != nil {
		http.Error(w, "Erreur lors du parsing du formulaire", http.StatusBadRequest)
		return
	}

	file, fileHeader, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "Erreur lors de la récupération du fichier", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Créer le répertoire "../temp" s'il n'existe pas
	tempDir := "../temp"
	err = os.MkdirAll(tempDir, 0755)
	if err != nil {
		http.Error(w, "Erreur lors de la création du répertoire de destination", http.StatusInternalServerError)
		return
	}

	// Chemin de destination pour le fichier uploadé
	destPath := tempDir + "/" + fileHeader.Filename
	dst, err := os.Create(destPath)
	if err != nil {
		http.Error(w, "Erreur lors de la création du fichier destination", http.StatusInternalServerError)
		return
	}
	defer dst.Close()

	// Copier le contenu du fichier uploadé vers le fichier destination
	_, err = io.Copy(dst, file)
	if err != nil {
		http.Error(w, "Erreur lors de la sauvegarde du fichier", http.StatusInternalServerError)
		return
	}

	// Répondre avec un statut de succès
	response := map[string]interface{}{
		"status":   "success",
		"message":  "Fichier uploadé avec succès",
		"filename": fileHeader.Filename,
		"filepath": destPath,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func enableCors(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Autorise uniquement l'origine souhaitée (ici, http://127.0.0.1:8080)
		w.Header().Set("Access-Control-Allow-Origin", "http://127.0.0.1:8080")
		// Autorise les méthodes GET, POST et OPTIONS
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		// Autorise le header Content-Type, etc.
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

		// Pour une requête préflight (OPTIONS), on peut répondre ici directement
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}
