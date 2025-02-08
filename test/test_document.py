import pytesseract
from PIL import Image
import spacy
import re
import logging
from pathlib import Path

class DocumentPpwdrocessor:
    def __init__(self):
        try:
            self.nlp = spacy.load("fr_core_news_md")
        except OSError:
            logging.warning("Modèle français non trouvé. Installation en cours...")
            from spacy.cli import download
            download("fr_core_news_md")
            self.nlp = spacy.load("fr_core_news_md")

        # Entités nommées à anonymiser
        self.SENSITIVE_ENTITIES = {
            'PER': '[NOM]',
            'LOC': '[LIEU]',
            'ORG': '[ORGANISATION]'
        }

        # Patterns étendus pour les données sensibles
        self.patterns = {
            'email': (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
            'phone': (r'(?:(?:\+|00)(?:\d{1,3})?|0)\s*[1-9](?:[\s.-]*\d{2}){4}\b', '[TÉLÉPHONE]'),
            'date': (r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '[DATE]'),
            
            # Nouveaux patterns
            'carte_bancaire': (r'\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b', '[CARTE_BANCAIRE]'),
            'carte_exp': (r'\b(?:exp|expiration)?\s*:\s*\d{2}/\d{2}\b', '[DATE_EXPIRATION]'),
            'cvv': (r'\b(?:cvv|cvc|ccv|cid|cvv2|cvc2)?\s*:?\s*\d{3,4}\b', '[CVV]'),
            
            'secu': (r'\b[1-2]\s*\d{2}\s*\d{2}\s*\d{2,3}\s*\d{3}\s*\d{3}\s*\d{2}\b', '[NUMÉRO_SÉCU]'),
            'passport': (r'\b[A-Z0-9]{2,3}[0-9]{6,7}\b', '[NUMÉRO_PASSEPORT]'),
            
            'iban': (r'\b[A-Z]{2}\d{2}\s*(?:\d{4}\s*){4,6}\d{1,4}\b', '[IBAN]'),
            'swift': (r'\b[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b', '[CODE_SWIFT]'),
            
            'address': (r'\b\d+\s+(?:rue|avenue|boulevard|impasse|allée|place|route|voie)\s+[a-zA-Z\s]+\b', '[ADRESSE]'),
            'code_postal': (r'\b\d{5}\b', '[CODE_POSTAL]'),
            
            # Données d'identification supplémentaires
            'nir': (r'\b\d{13,15}\b', '[NUMÉRO_IDENTIFICATION]'),
            'permis': (r'\b[A-Z0-9]{2,3}-\d{6,7}\b', '[NUMÉRO_PERMIS]')
        }

    def extract_text_from_image(self, image_path):
        """Extraire le texte d'une image"""
        try:
            # Configuration de Tesseract pour le français avec amélioration de la précision
            custom_config = r'--oem 3 --psm 6 -l fra'
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, config=custom_config)
            return text.strip()
        except Exception as e:
            logging.error(f"Erreur lors de l'extraction du texte: {str(e)}")
            return None

    def anonymize_text(self, text):
        """Anonymiser les données sensibles dans le texte"""
        try:
            # Traitement du texte avec spaCy
            doc = self.nlp(text)
            
            # Copier le texte pour le modifier
            anonymized_text = text

            # Anonymiser les entités nommées (dans l'ordre inverse pour éviter les problèmes de décalage)
            for ent in reversed(doc.ents):
                if ent.label_ in self.SENSITIVE_ENTITIES:
                    anonymized_text = anonymized_text[:ent.start_char] + \
                                    self.SENSITIVE_ENTITIES[ent.label_] + \
                                    anonymized_text[ent.end_char:]

            # Anonymiser les patterns réguliers (du plus spécifique au plus général)
            for pattern_name, (pattern, replacement) in self.patterns.items():
                anonymized_text = re.sub(pattern, replacement, anonymized_text, flags=re.IGNORECASE)

            return anonymized_text

        except Exception as e:
            logging.error(f"Erreur lors de l'anonymisation: {str(e)}")
            return text

    def process_document(self, image_path):
        """Traiter un document complet"""
        if not Path(image_path).exists():
            logging.error(f"Le fichier {image_path} n'existe pas.")
            return None

        extracted_text = self.extract_text_from_image(image_path)
        if not extracted_text:
            return None

        anonymized_text = self.anonymize_text(extracted_text)

        return {
            'original_text': extracted_text,
            'anonymized_text': anonymized_text
        }

# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(level=logging.INFO)
    
    # Créer une instance du processeur
    processor = DocumentPpwdrocessor()
    
    # Utiliser le chemin correct vers votre image
    image_path = "hackathon.png"  # Assurez-vous que ce fichier existe
    
    print("Traitement du document en cours...")
    results = processor.process_document(image_path)
    
    if results:
        print("\nTexte original:")
        print("-" * 50)
        print(results['original_text'])
        
        print("\nTexte anonymisé:")
        print("-" * 50)
        print(results['anonymized_text'])