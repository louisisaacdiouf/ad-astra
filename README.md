# AD ASTRA

**Hackathon Socium Project**  
*Team: AD ASTRA*

---

## 🚀 Overview

**Anonymouse** est un projet d'anonymisation de documents, reposant sur une architecture en microservices. Le but est de fournir une solution efficace pour extraire, analyser, et anonymiser des informations sensibles dans des documents PDF. Ce projet a été développé lors du **Hackathon Socium**.

---

## 🤝 Architecture

Le projet est composé de **quatre services principaux** qui communiquent entre eux :

1. **Extraction des données (Rust)**  
   Extrait le texte des fichiers PDF.

2. **Labélisation des données (Python)**  
   Identifie les entités sensibles grâce à [Wikineural](https://huggingface.co/Babelscape/wikineural-multilingual-ner).

3. **Masquage des informations (Python)**  
   Anonymise les données choisies dans le PDF avec **PyMuPDF**.

4. **Orchestration (Go)**  
   Coordonne l'interaction entre les services pour un processus fluide.

---

## 🌐 Labels d'Anonymisation

Le service de labélisation renvoie une combinaison d'entités extraites par le modèle et celles détectées via des expressions régulières.

### Labels issus du modèle (après mapping) :
- **PERSON**  👤  
  *Entités marquées comme « PER » par le modèle.*

- **GPE**  🌏  
  *Entités géopolitiques, renommées à partir de « LOC ».*

- **ORG**  📏  
  *Organisations détectées.*

- **MISC**  🔢  
  *Entités diverses non classées autrement.*

### Labels ajoutés par expressions régulières :
- **EMAIL**  📧  
  *Adresses e-mail.*

- **PHONE**  📱  
  *Numéros de téléphone.*

- **ADDRESS**  🏡  
  *Adresses physiques.*

- **CARD**  💳  
  *Numéros de carte (bancaires, identité, etc.).*

---

## 🚫 API Documentation

### 🔗 Point d'Entrée :
L'anonymisation se fait via une requête **POST** à **`ENTRY_ADDR/entry`** (voir fichier **`.env`**).

**Requête :**
```json
{
    "file_path": "/chemin/vers/fichier.pdf",
    "forbidden_labels": [
        "PHONE",
        "ADDRESS",
        "CARD",
        "EMAIL"
    ]
}
```

---

### 🔹 1. Service d'Extraction (Rust)

**Requête :**
```json
{
    "file_path": "chemin/vers/le/fichier.pdf"
}
```

**Réponse :**
```json
{
    "text": "Contenu textuel extrait du PDF."
}
```

---

### 🔹 2. Service de Labélisation (Python)

**Requête :**
```json
{
    "text": "Texte à analyser pour la labélisation."
}
```

**Réponse :**
```json
{
    "extracted_text": "Texte original fourni.",
    "entities": [
        {
            "text": "Entité reconnue",
            "label": "LABEL_ASSOCIÉ"
        },
        {
            "text": "Autre entité",
            "label": "AUTRE_LABEL"
        }
    ]
}
```

---

### 🔹 3. Service d'Anonymisation (Python)

**Requête :**
```json
{
    "file_path": "chemin/vers/le/fichier.pdf",
    "entities": [
        {
            "text": "Entité à anonymiser",
            "label": "LABEL_ASSOCIÉ"
        }
    ],
    "forbidden_labels": ["LABEL_INTERDIT_1", "LABEL_INTERDIT_2"]
}
```

**Réponse :**
```json
{
    "message": "Statut de l'anonymisation.",
    "output_file": "chemin/vers/le/fichier_anonymisé.pdf"
}
```

---

### 🔹 4. Service d'Orchestration (Go)

**Requête :**
```json
{
    "file_path": "chemin/vers/le/fichier.pdf",
    "forbidden_labels": ["LABEL_INTERDIT_1", "LABEL_INTERDIT_2"]
}
```

**Réponse :**
```json
{
    "message": "Statut global du processus.",
    "output_file": "chemin/vers/le/fichier_final.pdf"
}
```

---

## 🔧 Installation & Lancement

### Prérequis :
- Rust
- Python 3.x (avec **PyMuPDF** et **HuggingFace Transformers**)
- Go

### Instructions :
1. Clonez le dépôt :
   ```bash
   git clone https://github.com/votre-repo/ad-astra.git
   ```

2. Configurez l'environnement :
   - Créez un fichier **`.env`** avec les adresses des services.

3. Lancez chaque service :
   - Extraction : `cargo run`
   - Labélisation : `python labeling_service.py`
   - Anonymisation : `python anonymization_service.py`
   - Orchestration : `go run orchestrator.go`

---

## 🖊️ Contributeurs

- **AD ASTRA Team**  
  Passionnés par la sécurité des données et l'optimisation des processus d'anonymisation. **Talents chez Zone01 Dakar**.

---

## 🌟 Remerciements

Merci à **Socium** pour cette opportunité de repousser les limites de la technologie et de la collaboration.

---

## 📄 Licence

Ce projet est sous licence **MIT**. Voir le fichier **LICENSE** pour plus de détails.
