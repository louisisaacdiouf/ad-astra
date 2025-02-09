from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from dotenv import load_dotenv
import os
import re

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer l'adresse et le port à partir des variables d'environnement
HOST = os.getenv("LABELLING_HOST", "0.0.0.0")
PORT = int(os.getenv("LABELLING_PORT", "5000"))

app = Flask(__name__)
CORS(app, resources={r"/label": {"origins": "http://127.0.0.1:8080"}})

# Charger le modèle préentraîné et le tokenizer
tokenizer = AutoTokenizer.from_pretrained("Babelscape/wikineural-multilingual-ner")
model = AutoModelForTokenClassification.from_pretrained("Babelscape/wikineural-multilingual-ner")
# Utilisation du pipeline NER avec une stratégie d'agrégation simple pour fusionner les tokens en entités
ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

# Fonctions de détection par regex
def detect_emails(text):
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(pattern, text)

def detect_phone_numbers(text):
    # Regex simplifiée pour les numéros de téléphone
    pattern = r"\+?\d[\d\s\-\(\)]{7,}\d"
    return re.findall(pattern, text)

def detect_addresses(text):
    # Regex simple pour les adresses (exemple : "123 rue de la paix")
    # Remarque : ce pattern peut nécessiter des ajustements en fonction des formats rencontrés.
    addr_pattern = re.compile(
        r"\d{1,4}\s+(?:rue|avenue|boulevard|impasse|chemin|allée|place)\s+[A-Za-zÀ-ÖØ-öø-ÿ'\- ]+",
        re.IGNORECASE
    )
    return [m.group(0) for m in addr_pattern.finditer(text)]

def detect_card_numbers(text):
    # Regex pour détecter une séquence de chiffres (avec espaces ou tirets) de longueur plausible pour des numéros de carte
    pattern = r"\b(?:\d[ -]*?){12,19}\b"
    return re.findall(pattern, text)

@app.route('/label', methods=['POST'])
def label_text():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Requête invalide. Le champ 'text' est requis."}), 400

    text = data["text"]
    # Utiliser le pipeline pour détecter les entités dans le texte
    results = ner_pipeline(text)

    entities = []
    for res in results:
        # Le modèle renvoie des entités avec le champ "entity_group"
        label = res.get("entity_group", "")
        # Mapper certains labels pour coller aux conventions attendues
        if label == "PER":
            label = "PERSON"
        elif label == "LOC":
            label = "GPE"
        entities.append({
            "text": res.get("word", ""),
            "label": label
        })

    # Détection supplémentaire via regex
    for email in detect_emails(text):
        entities.append({
            "text": email,
            "label": "EMAIL"
        })

    for phone in detect_phone_numbers(text):
        entities.append({
            "text": phone,
            "label": "PHONE"
        })

    for address in detect_addresses(text):
        entities.append({
            "text": address,
            "label": "ADDRESS"
        })

    for card in detect_card_numbers(text):
        entities.append({
            "text": card,
            "label": "CARD"
        })

    response = {
        "extracted_text": text,
        "entities": entities
    }
    
    return jsonify(response)

if __name__ == '__main__':
    print("--------------------------------------------------")
    print("             SERVICE DE LABELLISATION            ")
    print("--------------------------------------------------")
    print(f"Service de labellisation en écoute sur {HOST}:{PORT}...")
    app.run(host=HOST, port=PORT)
