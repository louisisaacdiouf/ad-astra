import os
from pathlib import Path
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
import numpy as np
import shutil

class PDFDocumentClassifier:
    def __init__(self):
        self.categories = {
            'facture': [
                'facture', 'total ttc', 'ht', 'tva', 'montant', 'prix',
                'paiement', 'client', 'numéro de facture'
            ],
            'contrat': [
                'contrat', 'entre les soussignés', 'parties', 'conditions',
                'accord', 'signature', 'engagement'
            ],
            'certificat': [
                'certificat', 'atteste', 'certifie', 'délivré à',
                'valable', 'attestation'
            ],
            'cv': [
                'curriculum vitae', 'cv', 'expérience professionnelle',
                'formation', 'compétences', 'diplômes'
            ],
            'lettre_motivation': [
                'lettre de motivation', 'candidature', 'poste',
                'madame', 'monsieur', 'je soussigné'
            ]
        }
        
        self.classifier = Pipeline([
            ('vectorizer', TfidfVectorizer(ngram_range=(1, 2))),
            ('classifier', LinearSVC())
        ])
        
        self.is_trained = False

    def extract_text_from_pdf(self, pdf_path):
        """Extraire le texte d'un fichier PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.lower()
        except Exception as e:
            print(f"Erreur lors de la lecture du PDF {pdf_path}: {str(e)}")
            return ""

    def create_training_data(self):
        """Créer des données d'entraînement synthétiques"""
        texts = []
        labels = []
        
        for category, keywords in self.categories.items():
            for _ in range(20):
                selected_keywords = np.random.choice(
                    keywords,
                    size=np.random.randint(3, 6),
                    replace=False
                )
                text = ' '.join(selected_keywords)
                texts.append(text.lower())
                labels.append(category)
        
        return texts, labels

    def train(self):
        """Entraîner le classificateur"""
        texts, labels = self.create_training_data()
        self.classifier.fit(texts, labels)
        self.is_trained = True
        print("Entraînement terminé!")

    def predict(self, text):
        """Prédire la catégorie d'un texte"""
        if not self.is_trained:
            print("Le modèle n'est pas encore entraîné!")
            return None
        
        prediction = self.classifier.predict([text])[0]
        return prediction

    def organize_pdfs(self, input_folder, output_folder):
        """Organiser les PDF dans des dossiers par catégorie"""
        if not self.is_trained:
            print("Entraînement du modèle...")
            self.train()

        # Créer le dossier de sortie s'il n'existe pas
        os.makedirs(output_folder, exist_ok=True)
        
        # Créer un dossier pour chaque catégorie
        for category in self.categories.keys():
            os.makedirs(os.path.join(output_folder, category), exist_ok=True)

        # Traiter chaque PDF dans le dossier d'entrée
        processed_files = 0
        for filename in os.listdir(input_folder):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(input_folder, filename)
                print(f"\nTraitement de {filename}...")
                
                # Extraire le texte
                text = self.extract_text_from_pdf(pdf_path)
                if text:
                    # Classifier le document
                    category = self.predict(text)
                    
                    # Déplacer le fichier dans le bon dossier
                    destination = os.path.join(output_folder, category, filename)
                    shutil.copy2(pdf_path, destination)
                    
                    print(f"Classé comme: {category}")
                    processed_files += 1

        print(f"\nClassification terminée! {processed_files} fichiers traités.")

# Code de test
if __name__ == "__main__":
    # Créer le classificateur
    classifier = PDFDocumentClassifier()
    
    # Définir les dossiers d'entrée et de sortie
    input_folder = "pdfs_input"      # Dossier contenant vos PDF
    output_folder = "pdfs_classes"   # Dossier où seront classés les PDF
    
    # Créer le dossier d'entrée s'il n'existe pas
    os.makedirs(input_folder, exist_ok=True)
    

    
    # Vérifier s'il y a des fichiers à traiter
    if not os.listdir(input_folder):
        print(f"Aucun fichier trouvé dans {input_folder}")
        print("Veuillez y ajouter des fichiers PDF et relancer le programme")
    else:
        # Lancer la classification
        classifier.organize_pdfs(input_folder, output_folder)