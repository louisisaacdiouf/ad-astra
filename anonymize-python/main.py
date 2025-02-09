import os
import fitz  # PyMuPDF
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

FLASK_SERVER_ADDR = os.getenv("FLASK_SERVER_ADDR", "127.0.0.1")
FLASK_SERVER_PORT = int(os.getenv("FLASK_SERVER_PORT", "5000"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/home/lijsd/repositories/hackathon-socium/ad-astra/entry-go/www/output_dir")

# Créer le répertoire de sortie s'il n'existe pas
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

app = Flask(__name__)
CORS(app, resources={r"/anonymize": {"origins": "http://127.0.0.1:8080"}})

@app.route('/anonymize', methods=['POST'])
def redact_pdf():
    # La requête doit être de la forme :
    # {"file_path": "/path/to/file.pdf", "entities": [{"text": "Isaac", "label": "PERSON"}, {"text": "Norway", "label": "GPE"}], "forbidden_labels": ["PERSON", "GPE"]}
    data = request.get_json()
    if not data:
        return jsonify({"error": "Aucune donnée JSON reçue"}), 400

    file_path = data.get("file_path")
    entities = data.get("entities", [])
    forbidden_labels = data.get("forbidden_labels", [])

    if not file_path:
        return jsonify({"error": "Le champ 'file_path' est requis"}), 400

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        return jsonify({"error": f"Impossible d'ouvrir le fichier PDF: {e}"}), 500

    # Parcourir toutes les pages du document
    for page in doc:
        # Pour chaque entité donnée, si son label fait partie des forbidden_labels, on recherche le texte sur la page
        for entity in entities:
            text_to_redact = entity.get("text")
            label = entity.get("label")
            if label in forbidden_labels and text_to_redact:
                # La méthode search_for retourne une liste de rectangles où se trouve l'occurrence du texte
                rects = page.search_for(text_to_redact)
                for rect in rects:
                    # Ajouter une annotation de redaction (rectangle noir)
                    page.add_redact_annot(rect, fill=(0, 0, 0))
        # Appliquer toutes les redactions sur la page
        page.apply_redactions()

    # Sauvegarder le document caviardé dans le répertoire de sortie
    base_filename = os.path.basename(file_path)
    name, ext = os.path.splitext(base_filename)
    output_filename = f"{name}_redacted{ext}"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    try:
        doc.save(output_path)
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la sauvegarde du PDF caviardé: {e}"}), 500

    return jsonify({
        "message": "PDF caviardé avec succès",
        "output_file": output_path
    }), 200

if __name__ == '__main__':
    print("--------------------------------------------------")
    print("                     ANONYMIZE                    ")
    print("--------------------------------------------------")
    print(f"Serveur Python écoute sur {FLASK_SERVER_ADDR}:{FLASK_SERVER_PORT}")
    app.run(host=FLASK_SERVER_ADDR, port=FLASK_SERVER_PORT)
