from langdetect import detect


MODEL_MAP = {
    "fr": "fr_core_news_lg",
    "en": "en_core_web_lg",
    "es": "es_core_news_lg"
}

def detect_language(text):
    try:
        return MODEL_MAP[detect(text)]
    except Exception:
        return "unknown"

texts = [
    "Salut les amis, comment vous allez? ", 
    "Hi friends, how are you?",
]

for text in texts:
    model = detect_language(text)  
    print(f"Texte: {text} - model: {model}")
