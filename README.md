# ad-astra

## **Architecture du Pipeline**

1. **Extracteur** (Rust) : Extraction du texte et des coordonnées depuis le PDF.  
2. **Analyseur** (Python) : Détection des données sensibles via ML/NLP.  
3. **Caviardeur** (Go) : Modification du PDF pour masquer les zones sensibles.  
4. **Orchestrateur** (Go) : Coordination du workflow et gestion des communications.  

![Schema Architecture](https://i.imgur.com/K7vY7Ql.png)

---

### **1. Extracteur (Rust) : Extraction des Textes et Coordonnées**

**Rôle** :  

- Identifier si le PDF est textuel ou scanné.  
- Extraire les zones de texte avec leurs coordonnées (en points PDF ou pixels).  

**Outils** :  

- **PDF textuel** : Bibliothèque `pdf-extract` ou `lopdf` pour extraire le texte et les métadonnées de position.  
- **PDF scanné/Image** :  
  - Conversion PDF → images avec `pdfium-render` (liaison Rust de PDFium).  
  - Prétraitement avec `imageproc` (rotation, contraste).  
  - OCR via `tesseract-rs` (wrapper Rust de Tesseract) pour détecter le texte et ses boîtes englobantes.  

**Sortie** :  
Un fichier JSON structuré comme :  

```json
{
  "pages": [
    {
      "page_number": 1,
      "width": 595.0,
      "height": 842.0,
      "units": "points",
      "content": [
        {
          "text": "John Doe",
          "x_min": 100.2,
          "y_min": 200.5,
          "x_max": 150.5,
          "y_max": 215.0
        }
      ]
    }
  ]
}
```

**Pourquoi Rust** :  

- Performances élevées pour le traitement d’images et l’OCR parallélisé.  
- Gestion mémoire sécurisée pour éviter les fuites avec des PDF volumineux.  

---

### **2. Analyseur (Python) : Détection des Données Sensibles**

**Rôle** :  

- Identifier les données sensibles (noms, numéros de sécurité sociale, etc.) dans le JSON.  
- Combiner règles regex, modèles de NLP (spaCy, Flair), et LLMs (optionnel).  

**Outils** :  

- **Regex** : Validation basique (e-mails, numéros de téléphone).  
- **ML/NLP** :  
  - `spaCy` avec modèle `fr_core_news_lg` pour la NER (reconnaissance d'entités).  
  - `transformers` (Hugging Face) pour des modèles spécialisés (ex: `dslim/bert-base-NER`).  
- **LLMs** :  
  - Appel à l'API GPT-4 ou exécution locale de Mistral-7B via `llama.cpp` pour des cas ambigus.  

**Sortie** :  
Un JSON enrichi avec les flags `is_sensitive` :  

```json
{
  "pages": [
    {
      "content": [
        {
          "text": "John Doe",
          "is_sensitive": true,
          "sensitivity_type": "person_name"
        }
      ]
    }
  ]
}
```

**Pourquoi Python** :  

- Écosystème mature pour le NLP/ML et intégration simple avec les LLMs.  

---

### **3. Caviardeur (Go) : Modification du PDF**

**Rôle** :  

- Superposer des rectangles noirs sur les zones sensibles en utilisant les coordonnées extraites.  

**Outils** :  

- Bibliothèque `unidoc` (Go) pour manipuler les PDF :  
  - Ajout de formes vectorielles (rectangles noirs) aux positions spécifiées.  
  - Suppression permanente du texte sous-jacent (pour éviter les fuites).  

**Exemple de Code Go** :  

```go
package main

import (
    "github.com/unidoc/unipdf/v3/model"
)

func redactPDF(inputPath string, outputPath string, sensitiveRegions []Region) error {
    pdf, _ := model.OpenPdfFile(inputPath)
    for _, region := range sensitiveRegions {
        page, _ := pdf.GetPage(region.PageNumber)
        // Dessiner un rectangle noir
        pdfDrawer := model.NewPdfPageResourcesDrawer(page)
        pdfDrawer.DrawRectangle(region.XMin, region.YMin, region.XMax-region.XMin, region.YMax-region.YMin)
        pdfDrawer.SetFillColor(0, 0, 0) // Noir
        pdfDrawer.Fill()
    }
    pdf.WriteToFile(outputPath)
    return nil
}
```

**Pourquoi Go** :  

- Compilation rapide et exécution légère pour des microservices.  
- Bibliothèques PDF fiables comme `unidoc` (version commerciale) ou `gofpdf` (open-source).  

---

### **4. Orchestrateur (Go) : Gestion du Workflow**

**Rôle** :  

- Exposer une API REST pour uploader le PDF.  
- Coordonner l’enchaînement Extracteur → Analyseur → Caviardeur.  
- Gérer les erreurs et les logs.  

**Outils** :  

- Framework web `Gin` ou `Echo` pour l’API.  
- Communication inter-services via gRPC (pour la performance) ou RabbitMQ (pour l’async).  

**Exemple d’Endpoint** :  

```go
// Gin example
router.POST("/process-pdf", func(c *gin.Context) {
    file, _ := c.FormFile("document")
    // 1. Appel à l'Extracteur (Rust via gRPC)
    extractedData, _ := rustExtractorClient.Process(file)
    // 2. Appel à l'Analyseur (Python via HTTP/REST)
    analyzedData, _ := pythonAnalyzerClient.Analyze(extractedData)
    // 3. Appel au Caviardeur (Go direct)
    redactPDF("input.pdf", "output.pdf", analyzedData.SensitiveRegions)
    c.File("output.pdf")
})
```

---

### **Optimisations Clés**

1. **Parallélisation** :  
   - Traiter chaque page du PDF en parallèle (Rust avec `rayon`, Go avec des goroutines).  
   - Pour l’OCR, utiliser Tesseract avec le mode `--psm 1` (segmentation automatique de page).  

2. **Cache** :  
   - Mettre en cache les modèles de NLP (ex: chargement unique de spaCy en mémoire).  

3. **Validation des Coordonnées** :  
   - Convertir les coordonnées pixels → points PDF si nécessaire (dépend de la résolution d’OCR).  

4. **Sécurité** :  
   - Chiffrement des PDF temporaires sur le disque.  
   - Suppression garantie des fichiers après traitement.  

---

### **Alternative pour le Caviardage (Rust)**

Si la manipulation PDF en Go est limitée, remplacer le Caviardeur par du Rust avec `lopdf` :  

```rust
use lopdf::{Document, Object, Rectangle};

fn redact_pdf(path: &str, regions: Vec<Region>) {
    let mut doc = Document::load(path).unwrap();
    for region in regions {
        doc.get_page(region.page_number)
            .add_redaction(Region::to_rectangle(), 0.0, 0.0, 0.0); // RGBA noir
    }
    doc.save("output.pdf").unwrap();
}
```

---

### **Stack Technique Résumée**

| Étape          | Technologie | Outils Principaux                     |  
|----------------|-------------|----------------------------------------|  
| **Extraction** | Rust        | Tesseract-rs, pdf-extract, imageproc   |  
| **Analyse**    | Python      | spaCy, Hugging Face, FastAPI           |  
| **Caviardage** | Go/Rust     | unidoc (Go) / lopdf (Rust)             |  
| **Orchestre**  | Go          | Gin, gRPC                              |  

---

### **Prochaines Étapes**

1. **Prototypage de l’Extracteur** :  
   - Démarrer avec un PDF textuel → valider l’extraction des coordonnées via `lopdf`.  
2. **Intégration OCR** :  
   - Ajouter `tesseract-rs` avec prétraitement OpenCV (débruitage).  
3. **Test End-to-End** :  
   - Caviarder un PDF simple avec une zone sensible connue.  

Je peux fournir des exemples de code détaillés pour chaque module si besoin ! 🛠️
