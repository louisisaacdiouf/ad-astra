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
        # Amélioration des mots-clés avec plus de termes pertinents et leur contexte
        self.categories = {
            'facture': [
                'facture', 'total ttc', 'ht', 'tva', 'montant', 'prix',
                'paiement', 'client', 'numéro de facture', 'bon de commande',
                'règlement', 'devis', 'acompte', 'échéance', 'détail facturation',
                'remise', 'article', 'quantité', 'référence client'
            ],
            'contrat': [
                'contrat', 'entre les soussignés', 'parties', 'conditions',
                'accord', 'signature', 'engagement', 'convention', 'stipule',
                'clause', 'obligations', 'durée', 'résiliation', 'modalités',
                'dispositions', 'contractant', 'validité', 'terme du contrat'
            ],
            'certificat': [
                'certificat', 'atteste', 'certifie', 'délivré à',
                'valable', 'attestation', 'diplôme', 'accréditation',
                'reconnaissance', 'certification', 'validité', 'homologation',
                'authentification', 'décerne', 'titulaire'
            ],
            'cv': [
                'curriculum vitae', 'cv', 'expérience professionnelle',
                'formation', 'compétences', 'diplômes', 'stage', 'profil',
                'langues', 'né le', 'nationalité', 'permis', 'missions',
                'tâches', 'stagiaire', 'études', 'contact', 'téléphone',
                'email', 'adresse', 'parcours', 'professionnel'
            ],
            'lettre_motivation': [
                'lettre de motivation', 'candidature', 'poste',
                'madame', 'monsieur', 'je soussigné', 'recrutement',
                'sollicite', 'motivation', 'entretien', 'démarche',
                'présentation', 'disponible', 'rejoindre', 'équipe',
                'entreprise', 'intérêt', 'à l attention de'
            ]
        }
        
        # Amélioration du pipeline avec des paramètres optimisés
        self.classifier = Pipeline([
            ('vectorizer', TfidfVectorizer(
                ngram_range=(1, 3),  # Prend en compte les groupes de 1 à 3 mots
                min_df=2,            # Ignore les termes trop rares
                max_df=0.95,         # Ignore les termes trop fréquents
                sublinear_tf=True    # Applique une échelle logarithmique
            )),
            ('classifier', LinearSVC(
                C=1.0,               # Paramètre de régularisation
                class_weight='balanced'  # Gestion des classes déséquilibrées
            ))
        ])
        
        self.is_trained = False

    def extract_text_from_pdf(self, pdf_path):
        """Extraire le texte d'un fichier PDF avec gestion améliorée du texte"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    # Extraction du texte avec nettoyage basique
                    page_text = page.extract_text()
                    if page_text:
                        # Normalisation du texte
                        page_text = ' '.join(page_text.split())  # Normalise les espaces
                        text += page_text + "\n"
                return text.lower()
        except Exception as e:
            print(f"Erreur lors de la lecture du PDF {pdf_path}: {str(e)}")
            return ""

    def create_training_data(self):
        """Créer des données d'entraînement plus réalistes"""
        texts = []
        labels = []
        
        for category, keywords in self.categories.items():
            # Augmentation du nombre d'exemples par catégorie
            for _ in range(50):  # Plus d'exemples pour un meilleur apprentissage
                # Création de textes plus réalistes
                num_keywords = np.random.randint(5, 10)  # Plus de mots-clés par exemple
                main_keywords = np.random.choice(keywords, size=num_keywords, replace=False)
                
                # Ajout de bruit et de contexte
                filler_words = ['le', 'la', 'les', 'du', 'des', 'un', 'une', 'et', 'pour', 'dans']
                text_parts = []
                
                for keyword in main_keywords:
                    # Ajout de mots de contexte autour des mots-clés
                    if np.random.random() > 0.5:
                        text_parts.append(np.random.choice(filler_words))
                    text_parts.append(keyword)
                    if np.random.random() > 0.5:
                        text_parts.append(np.random.choice(filler_words))
                
                text = ' '.join(text_parts)
                texts.append(text.lower())
                labels.append(category)
        
        return texts, labels

    def predict(self, text):
        """Prédire la catégorie d'un texte avec score de confiance"""
        if not self.is_trained:
            print("Le modèle n'est pas encore entraîné!")
            return None
        
        # Obtenir les scores de décision pour chaque classe
        decision_scores = self.classifier.decision_function([text])
        predicted_class = self.classifier.predict([text])[0]
        
        # Convertir les scores en probabilités via softmax
        scores = np.exp(decision_scores) / np.sum(np.exp(decision_scores), axis=1)[:, None]
        confidence = np.max(scores)
        
        if confidence < 0.4:  # Seuil de confiance
            print(f"Attention: Classification peu fiable (confidence: {confidence:.2f})")
            
        return predicted_class

    def train(self):
        """Entraîner le classificateur"""
        texts, labels = self.create_training_data()
        self.classifier.fit(texts, labels)
        self.is_trained = True
        print("Entraînement terminé!")

    def organize_pdfs(self, input_folder, output_folder):
        """Organiser les PDF dans des dossiers par catégorie"""
        if not self.is_trained:
            print("Entraînement du modèle...")
            self.train()

        os.makedirs(output_folder, exist_ok=True)
        
        for category in self.categories.keys():
            os.makedirs(os.path.join(output_folder, category), exist_ok=True)

        processed_files = 0
        for filename in os.listdir(input_folder):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(input_folder, filename)
                print(f"\nTraitement de {filename}...")
                
                text = self.extract_text_from_pdf(pdf_path)
                if text:
                    category = self.predict(text)
                    destination = os.path.join(output_folder, category, filename)
                    shutil.copy2(pdf_path, destination)
                    
                    print(f"Classé comme: {category}")
                    processed_files += 1

        print(f"\nClassification terminée! {processed_files} fichiers traités.")

if __name__ == "__main__":
    classifier = PDFDocumentClassifier()
    input_folder = "pdfs_input"
    output_folder = "pdfs_classes"
    
    os.makedirs(input_folder, exist_ok=True)
    
    if not os.listdir(input_folder):
        print(f"Aucun fichier trouvé dans {input_folder}")
        print("Veuillez y ajouter des fichiers PDF et relancer le programme")
    else:
        classifier.organize_pdfs(input_folder, output_folder)