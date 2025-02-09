from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageFilter
import spacy
import re
import logging
from pathlib import Path
import time
from tqdm import tqdm
import fitz  # PyMuPDF
import tempfile  # Pour stocker temporairement les images

class DocumentProcessor:

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
            'PER': '[NOM]',  # Noms et prénoms
            'LOC': '[LIEU]',  # Lieux et adresses
            'ORG': '[ORGANISATION]',  # Organisations
        }

        # Patterns pour les données sensibles
        self.patterns = {
            'email': (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
            'phone': (r'(?:(?:\+|00)(?:\d{1,3})?|0)\s*[1-9](?:[\s.-]*\d{2}){4}\b', '[TÉLÉPHONE]'),
            'date': (r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '[DATE]'),
            'address': (r'\b\d+\s+(?:rue|avenue|boulevard|route|impasse|allée)\s+[A-Za-zéèêëàâäôöûüç\s-]+\b', '[ADRESSE]'),
        }

    def extract_words_with_coordinates(self, image):
        """Extraire les mots et leurs coordonnées dans l'image"""
        try:
            custom_config = r'--oem 3 --psm 6 -l fra'
            data = pytesseract.image_to_data(image, config=custom_config, output_type=pytesseract.Output.DICT)

            words = []
            for i in range(len(data['text'])):
                word = data['text'][i].strip()
                if word:
                    words.append({
                        'text': word,
                        'left': data['left'][i],
                        'top': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    })
            return words
        except Exception as e:
            logging.error(f"Erreur lors de l'extraction des mots et des coordonnées: {str(e)}")
            return None

    def label_sensitive_words(self, words):
        """Labelliser les mots sensibles dans la liste de mots"""
        try:
            text = " ".join([word['text'] for word in words])
            doc = self.nlp(text)

            sensitive_words = set()
            for ent in doc.ents:
                if ent.label_ in self.SENSITIVE_ENTITIES:
                    sensitive_words.update(ent.text.split())

            for pattern_name, (pattern, _) in self.patterns.items():
                matches = re.finditer(pattern, text, flags=re.IGNORECASE)
                for match in matches:
                    sensitive_words.update(match.group().split())

            for word in words:
                word['sensitive'] = word['text'] in sensitive_words

            return words
        except Exception as e:
            logging.error(f"Erreur lors de la labellisation des mots sensibles: {str(e)}")
            return words

    def blur_sensitive_areas(self, image, words):
        """Flouter les zones sensibles dans l'image"""
        try:
            for word in words:
                if word.get('sensitive', False):
                    left, top, width, height = word['left'], word['top'], word['width'], word['height']
                    region = image.crop((left, top, left + width, top + height))
                    blurred_region = region.filter(ImageFilter.GaussianBlur(radius=10))
                    image.paste(blurred_region, (left, top, left + width, top + height))
            
            return image
        except Exception as e:
            logging.error(f"Erreur lors du floutage des zones sensibles: {str(e)}")
            return None

    def process_document(self, pdf_path, output_pdf_path):
        """Traiter un document complet avec une barre de progression"""
        start_time = time.time()

        if not Path(pdf_path).exists():
            logging.error(f"Le fichier {pdf_path} n'existe pas.")
            return None

        with tqdm(total=100, desc="📄 Traitement en cours", bar_format="{l_bar}{bar} {n_fmt}/{total_fmt} {postfix}") as progress_bar:
            images = convert_from_path(pdf_path)
            progress_bar.update(20)

            pdf_document = fitz.open()

            for image in images:
                words = self.extract_words_with_coordinates(image)
                if not words:
                    continue
                progress_bar.update(10)

                words = self.label_sensitive_words(words)
                progress_bar.update(20)

                anonymized_image = self.blur_sensitive_areas(image, words)
                progress_bar.update(20)

                # Sauvegarde temporaire de l'image
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img:
                    anonymized_image.save(temp_img.name)
                    temp_img_path = temp_img.name

                # Ajout de l'image anonymisée au PDF
                pdf_page = pdf_document.new_page(width=image.width, height=image.height)
                pdf_page.insert_image(fitz.Rect(0, 0, image.width, image.height), filename=temp_img_path)

            pdf_document.save(output_pdf_path)
            pdf_document.close()
            progress_bar.update(30)

        end_time = time.time()
        execution_time = round(end_time - start_time, 4)

        return {
            'output_pdf_path': output_pdf_path,
            'execution_time': execution_time
        }

# Exemple d'utilisation
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    processor = DocumentProcessor()
    pdf_path = "./CV_Jean_Dupont_Image.pdf"
    output_pdf_path = "./anonymized_document.pdf"

    print("\n📌 **Début du traitement du document**")
    results = processor.process_document(pdf_path, output_pdf_path)

    if results:
        print(f"\n✅ **Document anonymisé sauvegardé sous** : {results['output_pdf_path']}")
        print(f"⏳ **Temps d'exécution** : {results['execution_time']} sec")
