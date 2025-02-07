from document_anonymizer import DocumentAnonymizer

def test_anonymizer():
    # Initialiser l'anonymiseur
    anonymizer = DocumentAnonymizer()
    
    # Cas de test 1: Document complet
    print("\n=== Test 1: Document Complet ===")
    document = """
    CURRICULUM VITAE
    
    Jean-Pierre Dupont
    123 rue de la République
    75001 Paris, France
    
    Tél: 06.12.34.56.78
    Email: jean.dupont@gmail.com
    N° Sécu: 1 85 12 75 123 456 78
    
    Expérience:
    - Microsoft France (2018-2022)
    - Google Paris (2015-2018)
    
    IBAN: FR76 3000 6000 0112 3456 7890 189
    """
    
    result = anonymizer.anonymize(document)
    print("Original:")
    print(document)
    print("\nAnonymisé:")
    print(result['anonymized_text'])
    print("\nStatistiques:")
    print(result['statistics'])

    # Cas de test 2: Numéros de téléphone
    print("\n=== Test 2: Numéros de téléphone ===")
    phones = """
    Contacts:
    06 12 34 56 78
    +33 6 12 34 56 78
    01.23.45.67.89
    """
    result = anonymizer.anonymize(phones)
    print("Original:", phones)
    print("Anonymisé:", result['anonymized_text'])

    # Cas de test 3: Emails et adresses
    print("\n=== Test 3: Emails et adresses ===")
    contacts = """
    Contacts:
    jean.dupont@example.com
    marie.martin@societe.fr
    45 avenue des Champs-Élysées, 75008 Paris
    """
    result = anonymizer.anonymize(contacts)
    print("Original:", contacts)
    print("Anonymisé:", result['anonymized_text'])

    # Cas de test 4: Entités nommées
    print("\n=== Test 4: Entités nommées ===")
    entities = """
    Pierre Martin travaille chez Apple à Paris.
    Il collabore souvent avec Microsoft France et Google.
    """
    result = anonymizer.anonymize(entities)
    print("Original:", entities)
    print("Anonymisé:", result['anonymized_text'])

    # Cas de test 5: Pattern personnalisé
    print("\n=== Test 5: Pattern personnalisé ===")
    anonymizer.add_custom_pattern(
        name="PROJET",
        pattern=r'PRJ-\d{4}',
        replacement="[PROJET]",
        priority=1
    )
    
    custom_text = "Projet référence: PRJ-2024"
    result = anonymizer.anonymize(custom_text)
    print("Original:", custom_text)
    print("Anonymisé:", result['anonymized_text'])

if __name__ == "__main__":
    test_anonymizer()