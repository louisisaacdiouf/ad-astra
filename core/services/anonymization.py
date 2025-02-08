import spacy
from spacy.pipeline import EntityRuler
from pdfminer.high_level import extract_text
import fitz
from langdetect import detect
from pdfminer.high_level import extract_text


MODEL_MAP = {
    "fr": "fr_core_news_lg",
    "en": "en_core_web_lg",
    "es": "es_core_news_lg"
}

def detect_language(text):
    print(text)
    try:
        return MODEL_MAP[detect(text)]
    except Exception:
        return "unknown"


def words_to_anonymize(model: str, text: str) -> list[str]:
    nlp = spacy.load(model)
    doc = nlp(text)
    words = []

    for ent in doc.ents:
        if ent.label_ in ["PERSON", "EMAIL", "PHONE_NUMBER", "ADDRESS", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "WORK_OF_ART"]:
            words.append(ent.text)

    print("Words to anonymize:", words)

    return words


def anonymize_text(words: list[str], document: str):
    doc = fitz.open(document)

    for w in words:
        for page in doc:
            text_instances = page.search_for(w) 

            for inst in text_instances:
                page.add_redact_annot(inst, fill=(0, 0, 0))
            page.apply_redactions()

    doc.save("document_anonymized.pdf")


def process_anonymization(document: str):
    text = extract_text(document)
    model = detect_language(text)
    print(f"Document language: {model}")
    words = words_to_anonymize(model, text)
    anonymize_text(words, document)


if __name__ == "__main__":
    process_anonymization("cv.pdf")
