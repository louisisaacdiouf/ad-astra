package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"regexp"
	"strings"

	"github.com/jdkato/prose/v2"
	"github.com/joho/godotenv"
)

// LabellingRequest représente la requête attendue contenant le texte
type LabellingRequest struct {
	Text string `json:"text"`
}

// Entity représente une entité extraite avec son label
type Entity struct {
	Text  string `json:"text"`
	Label string `json:"label"`
}

// LabellingResponse est la structure renvoyée contenant la liste des entités
type LabellingResponse struct {
	ExtractedText string   `json:"extracted_text"`
	Entities      []Entity `json:"entities"`
}

// loadStopWords lit un fichier texte et retourne une map[string]bool contenant chaque stopword en minuscule
func loadStopWords(filename string) (map[string]bool, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	stopWords := make(map[string]bool)
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		word := strings.TrimSpace(scanner.Text())
		if word != "" {
			stopWords[strings.ToLower(word)] = true
		}
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return stopWords, nil
}

// createEntities transforme une liste de chaînes de caractères en une liste d'entités avec le label donné
func createEntities(matches []string, label string) []Entity {
	var entities []Entity
	for _, match := range matches {
		entities = append(entities, Entity{Text: match, Label: label})
	}
	return entities
}

// refineEntities recatégorise les entités en vérifiant si le token fait partie du dictionnaire des stopwords
func refineEntities(entities []Entity, stopWords map[string]bool) []Entity {
	var refined []Entity
	for _, ent := range entities {
		lowered := strings.ToLower(ent.Text)
		if _, exists := stopWords[lowered]; exists {
			ent.Label = "STOPWORD"
		}
		refined = append(refined, ent)
	}
	return refined
}

// Fonctions de détection avec regex
func detectEmails(text string) []string {
	regex := regexp.MustCompile(`[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}`)
	return regex.FindAllString(text, -1)
}

func detectPhoneNumbers(text string) []string {
	regex := regexp.MustCompile(`\+?\d[\d\s\-\(\)]{7,}\d`)
	return regex.FindAllString(text, -1)
}

func detectAddresses(text string) []string {
	regex := regexp.MustCompile(`\d{1,4}\s+(rue|avenue|boulevard|impasse|chemin|allée|place)\s+[A-Za-zÀ-ÖØ-öø-ÿ'\- ]+`)
	return regex.FindAllString(text, -1)
}

func detectAges(text string) []string {
	regex := regexp.MustCompile(`\b\d{1,3}\s*(ans|an)\b`)
	return regex.FindAllString(text, -1)
}

func detectDates(text string) []string {
	regex := regexp.MustCompile(`\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{1,2}-\d{1,2}\b`)
	return regex.FindAllString(text, -1)
}

// labelHandler traite la requête POST sur l'endpoint /label
func labelHandler(w http.ResponseWriter, r *http.Request) {
	// On accepte uniquement la méthode POST
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req LabellingRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Requête invalide", http.StatusBadRequest)
		return
	}

	// Charger les stopwords
	lang := os.Getenv("LANG")
	stopWords, err := loadStopWords("stopwords/" + lang + "_stopwords.txt")
	if err != nil {
		log.Printf("Attention: impossible de charger les stopwords: %v", err)
		stopWords = make(map[string]bool) // Utiliser une map vide en cas d'erreur
	}

	// Utiliser Prose pour la détection d'entités de base
	doc, err := prose.NewDocument(req.Text)
	if err != nil {
		http.Error(w, fmt.Sprintf("Erreur lors du traitement du texte: %v", err), http.StatusInternalServerError)
		return
	}

	var entities []Entity
	for _, ent := range doc.Entities() {
		entities = append(entities, Entity{
			Text:  ent.Text,
			Label: ent.Label,
		})
	}

	// Ajouter les entités détectées par regex
	entities = append(entities, createEntities(detectEmails(req.Text), "EMAIL")...)
	entities = append(entities, createEntities(detectPhoneNumbers(req.Text), "PHONE")...)
	entities = append(entities, createEntities(detectAddresses(req.Text), "ADDRESS")...)
	entities = append(entities, createEntities(detectAges(req.Text), "AGE")...)
	entities = append(entities, createEntities(detectDates(req.Text), "DATE")...)

	// Raffiner les entités avec les stopwords
	entities = refineEntities(entities, stopWords)

	// Filtrer les stopwords de la réponse finale
	var finalEntities []Entity
	for _, ent := range entities {
		if ent.Label != "STOPWORD" {
			finalEntities = append(finalEntities, ent)
		}
	}

	resp := LabellingResponse{ExtractedText: req.Text, Entities: finalEntities}
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		http.Error(w, "Erreur lors de l'encodage de la réponse", http.StatusInternalServerError)
	}
}

func main() {
	// Charger les variables d'environnement depuis le fichier .env
	if err := godotenv.Load("../.env"); err != nil {
		log.Println("Aucun fichier .env trouvé, utilisation des variables d'environnement du système.")
	}

	// Récupérer l'adresse sur laquelle le service doit servir
	labellingAddr := os.Getenv("LABELLING_SERVICE_ADDR")
	if labellingAddr == "" {
		labellingAddr = "127.0.0.1:8082" // valeur par défaut
	}

	http.HandleFunc("/label", labelHandler)

	log.Printf("Service de labellisation en écoute sur %s...\n", labellingAddr)
	log.Fatal(http.ListenAndServe(labellingAddr, nil))
}
