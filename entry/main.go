package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/joho/godotenv"
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

// Structures pour l'orchestration
type OrchestrateRequest struct {
	FilePath string `json:"file_path"`
}

type OrchestrateResponse struct {
	ExtractedText string   `json:"extracted_text"`
	Entities      []Entity `json:"entities"`
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

// handlerOrchestrate reçoit la requête contenant le chemin du fichier,
// appelle successivement le service d'extraction et le service de labellisation,
// puis renvoie le dictionnaire de tous les termes labellisés.
func handlerOrchestrate(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	var req OrchestrateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Requête invalide", http.StatusBadRequest)
		return
	}

	// Récupérer les adresses des services depuis les variables d'environnement
	extractionAddr := os.Getenv("EXTRACTION_SERVICE_ADDR")
	labellingAddr := os.Getenv("LABELLING_SERVICE_ADDR")

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

	orchestrateResp := OrchestrateResponse{
		ExtractedText: extractionResp.Text,
		Entities:      labellingResp.Entities,
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(orchestrateResp); err != nil {
		http.Error(w, "Erreur lors de l'encodage de la réponse", http.StatusInternalServerError)
	}

	fileInfo, err := os.Stat(req.FilePath)
	if err != nil {
		http.Error(w, fmt.Sprintf("Erreur récupération des informations du fichier : %v", err), http.StatusInternalServerError)
		return
	}
	fmt.Printf("\n--\n\nFile: %s\nSize: %v bytes\nProcessing duration: %s\n", fileInfo.Name(), fileInfo.Size(), time.Since(start))
}

func main() {
	// Charger les variables d'environnement depuis le fichier .env
	if err := godotenv.Load("../.env"); err != nil {
		log.Println("Avertissement: fichier .env non trouvé, utilisation des variables d'environnement du système.")
	}

	// Récupérer le port de l'orchestrateur depuis la variable d'environnement
	entry_addr := os.Getenv("ENTRY_ADDR")
	if entry_addr == "" {
		entry_addr = "127.0.0.1:8080" // entry_addr par défaut si non défini
	}

	http.HandleFunc("/entry", handlerOrchestrate)
	log.Printf("Serveur orchestrateur en écoute sur %s...\n", entry_addr)
	log.Fatal(http.ListenAndServe(entry_addr, nil))
}
