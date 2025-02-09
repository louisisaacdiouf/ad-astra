package main

import (
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/joho/godotenv"
)

func main() {
	// Charger les variables d'environnement depuis le fichier .env
	if err := godotenv.Load("../.env"); err != nil {
		log.Println("Avertissement: fichier .env non trouvé, utilisation des variables d'environnement du système.")
	}

	// Routes API
	http.Handle("/entry", enableCors(http.HandlerFunc(handlerOrchestrate)))
	http.Handle("/loadfile", enableCors(http.HandlerFunc(handlerLoadFile)))



	// Servir le front-end statique depuis le dossier "www"
	// Serve les sous-dossiers directement pour que le Content-Type soit correctement défini
	http.Handle("/css/", http.StripPrefix("/css/", http.FileServer(http.Dir("www/css"))))
	http.Handle("/js/", http.StripPrefix("/js/", http.FileServer(http.Dir("www/js"))))
	http.Handle("/img/", http.StripPrefix("/img/", http.FileServer(http.Dir("www/img"))))
	http.Handle("/fonts/", http.StripPrefix("/fonts/", http.FileServer(http.Dir("www/fonts"))))
	http.Handle("/output_dir/", http.StripPrefix("/output_dir/", http.FileServer(http.Dir("www/output_dir"))))
	// Pour la racine, on sert index.html et les autres fichiers
	http.Handle("/", http.FileServer(http.Dir("www")))

	// Récupérer l'adresse d'entrée de l'orchestrateur
	entryAddr := os.Getenv("ENTRY_ADDR")
	if entryAddr == "" {
		entryAddr = "127.0.0.1:8080" // valeur par défaut
	}

	fmt.Println("--------------------------------------------------")
	fmt.Println("                   ORCHESTRATION                  ")
	fmt.Println("--------------------------------------------------")
	log.Printf("Serveur orchestrateur en écoute sur %s...\n", entryAddr)
	log.Fatal(http.ListenAndServe(entryAddr, nil))
}
