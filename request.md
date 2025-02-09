## REQUÊTES

Voici les formats des requêtes et des réponses des échanges avec les différents serveurs :

### 1. Service d'Extraction

**Requête :**

```json
{
    "file_path": "chemin/vers/le/fichier.pdf"
}
```

- `file_path` : Chemin du fichier PDF à extraire.

**Réponse :**

```json
{
    "text": "Contenu textuel extrait du PDF."
}
```

- `text` : Texte extrait du fichier PDF.

### 2. Service de Labellisation

**Requête :**

```json
{
    "text": "Texte à analyser pour la labellisation."
}
```

- `text` : Texte à analyser.

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
        // ... autres entités reconnues
    ]
}
```

- `extracted_text` : Texte original fourni pour la labellisation.
- `entities` : Liste des entités reconnues avec leur texte et le label associé.

### 3. Service d'Anonymisation

**Requête :**

```json
{
    "file_path": "chemin/vers/le/fichier.pdf",
    "entities": [
        {
            "text": "Entité à anonymiser",
            "label": "LABEL_ASSOCIÉ"
        },
        {
            "text": "Autre entité à anonymiser",
            "label": "AUTRE_LABEL"
        }
        // ... autres entités à anonymiser
    ],
    "forbidden_labels": ["LABEL_INTERDIT_1", "LABEL_INTERDIT_2"]
}
```

- `file_path` : Chemin du fichier PDF à anonymiser.
- `entities` : Liste des entités à anonymiser avec leur texte et le label associé.
- `forbidden_labels` : Liste des labels à ne pas anonymiser.

**Réponse :**

```json
{
    "message": "Statut de l'anonymisation.",
    "output_file": "chemin/vers/le/fichier_anonymisé.pdf"
}
```

- `message` : Statut ou message concernant l'anonymisation.
- `output_file` : Chemin vers le fichier PDF anonymisé.

### 4. Service d'Orchestration

**Requête :**

```json
{
    "file_path": "chemin/vers/le/fichier.pdf",
    "forbidden_labels": ["LABEL_INTERDIT_1", "LABEL_INTERDIT_2"]
}
```

- `file_path` : Chemin du fichier PDF à traiter.
- `forbidden_labels` : Liste des labels à ne pas anonymiser.

**Réponse :**

```json
{
    "message": "Statut global du processus.",
    "output_file": "chemin/vers/le/fichier_final.pdf"
}
```

- `message` : Statut ou message concernant le processus global.
- `output_file` : Chemin vers le fichier PDF final après traitement.

Ces structures JSON permettent aux différents services de communiquer efficacement en s'échangeant les informations nécessaires à chaque étape du processus. 