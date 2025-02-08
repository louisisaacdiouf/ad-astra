from transformers import pipeline
from langdetect import detect

def resume_document(texte, max_longueur_resume=150):
    """
    Génère un résumé court d'un document texte en détectant automatiquement la langue.
    
    Args:
        texte (str): Le texte à résumer
        max_longueur_resume (int): Longueur maximale souhaitée pour le résumé en tokens
        
    Returns:
        dict: Dictionnaire contenant le résumé et la langue détectée
    """
    try:
        # Détecter la langue du texte
        langue = detect(texte)
        
        # Utiliser un modèle BART pour le résumé
        summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            min_length=30,
            max_length=max_longueur_resume
        )
        
        # Générer le résumé
        resume = summarizer(texte, truncation=True)[0]['summary_text']
        
        return {
            'resume': resume,
            'langue_detectee': langue
        }
        
    except Exception as e:
        return f"Erreur lors de la génération du résumé: {str(e)}"

if __name__ == "__main__":
    texte = """
    L'invention de la machine à vapeur par James Watt dans les années 1770 a été un élément clé de cette révolution. Elle a permis de mécaniser de nombreuses industries, y compris le textile, l'acier, et plus tard le transport ferroviaire. Les usines sont devenues les centres de production dominants, attirant des travailleurs des campagnes vers les villes pour y trouver du travail. Cette urbanisation rapide a créé de nouveaux défis sociaux, tels que le surpeuplement, la pollution, et la mauvaise qualité de vie dans les zones industrielles.
    """
    
    resultat = resume_document(texte)
    if isinstance(resultat, dict):
        print(f"Résumé: {resultat}")
    else:
        print(resultat)  # Afficher le message d'erreur
    