import spacy
import re
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
import logging

@dataclass
class SensitivePattern:
    name: str
    pattern: str
    replacement: str
    priority: int

class DocumentAnonymizer:
    def __init__(self, model_name: str = "fr_core_news_md"):
        self.nlp = spacy.load(model_name)
        self.patterns = self._initialize_patterns()
        self.seen_entities: Dict[str, Set[str]] = {}
        logging.basicConfig(level=logging.INFO)
        
    def _initialize_patterns(self) -> List[SensitivePattern]:
        """Initialise les patterns pour la détection d'informations sensibles."""
        return [
            SensitivePattern(
                name="PHONE_FR",
                # This pattern matches French phone numbers, which can start with +33, 0033, or 0, followed by a digit from 1 to 9, and then four groups of two digits separated by spaces, dots, or hyphens.
                pattern=r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}',
                replacement="[TÉLÉPHONE]",
                priority=1
            ),
            SensitivePattern(
                name="EMAIL",
                # This pattern matches email addresses, which consist of a sequence of word characters, dots, or hyphens, followed by an @ symbol, another sequence of word characters, dots, or hyphens, and a domain suffix.
                pattern=r'[\w\.-]+@[\w\.-]+\.\w+',
                replacement="[EMAIL]",
                priority=1
            ),
            SensitivePattern(
                name="INSEE",
                # This pattern matches French social security numbers (INSEE), which start with 1 or 2, followed by groups of digits separated by optional spaces.
                pattern=r'\b[12]\s*\d{2}\s*[0-1]\d\s*\d{2}\s*\d{3}\s*\d{3}\s*\d{2}\b',
                replacement="[NUMÉRO_SÉCU]",
                priority=1
            ),
            SensitivePattern(
                name="IBAN_FR",
                # This pattern matches French IBAN numbers, which start with FR, followed by groups of digits separated by optional spaces.
                pattern=r'FR\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{3}',
                replacement="[IBAN]",
                priority=1
            ),
            SensitivePattern(
                name="ADDRESS",
                # This pattern matches French addresses, which start with a number, followed by a street type (rue, avenue, boulevard, etc.), and end with a postal code.
                pattern=r'\d{1,4}(?:,|\s)\s*(?:rue|avenue|boulevard|impasse|place).*?\d{5}.*?(?:\n|$)',
                replacement="[ADRESSE]",
                priority=2
            ),
            SensitivePattern(
                name="DATE",
                # This pattern matches dates in the format DD-MM-YYYY, DD/MM/YYYY, DD-MM-YY, or DD/MM/YY.
                pattern=r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
                replacement="[DATE]",
                priority=3
            )
        ]

    def _anonymize_entities(self, text: str) -> Tuple[str, Dict[str, Set[str]]]:
        """Anonymise les entités nommées dans le texte."""
        doc = self.nlp(text)
        anonymized = text
        entities_found = {}

        # Mapping des types d'entités
        entity_replacements = {
            'PER': '[PERSONNE]',
            'ORG': '[ORGANISATION]',
            'LOC': '[LIEU]',
            'GPE': '[LIEU]'
        }

        # Trier les entités par longueur (plus longues d'abord)
        entities = sorted(doc.ents, key=lambda x: len(x.text), reverse=True)
        
        for ent in entities:
            if ent.label_ in entity_replacements:
                replacement = entity_replacements[ent.label_]
                
                # Sauvegarder l'entité trouvée
                if ent.label_ not in entities_found:
                    entities_found[ent.label_] = set()
                entities_found[ent.label_].add(ent.text)
                
                # Remplacer toutes les occurrences
                anonymized = anonymized.replace(ent.text, replacement)

        return anonymized, entities_found

    def _anonymize_patterns(self, text: str) -> Tuple[str, Dict[str, Set[str]]]:
        """Anonymise les patterns réguliers dans le texte."""
        anonymized = text
        patterns_found = {}

        # Trier les patterns par priorité
        sorted_patterns = sorted(self.patterns, key=lambda x: x.priority)
        
        for pattern in sorted_patterns:
            matches = re.finditer(pattern.pattern, anonymized, re.IGNORECASE)
            
            # Sauvegarder et remplacer chaque match
            for match in matches:
                if pattern.name not in patterns_found:
                    patterns_found[pattern.name] = set()
                patterns_found[pattern.name].add(match.group(0))
                
                anonymized = anonymized.replace(match.group(0), pattern.replacement)

        return anonymized, patterns_found

    def anonymize(self, text: str, keep_statistics: bool = True) -> Dict[str, any]:
        """
        Anonymise le texte en utilisant à la fois les entités nommées et les patterns.
        """
        try:
            # Première passe : entités nommées
            anonymized, entities = self._anonymize_entities(text)
            
            # Deuxième passe : patterns réguliers
            anonymized, patterns = self._anonymize_patterns(anonymized)
            
            result = {
                'success': True,
                'anonymized_text': anonymized,
            }

            if keep_statistics:
                result.update({
                    'statistics': {
                        'original_length': len(text),
                        'anonymized_length': len(anonymized),
                        'entities_found': {k: len(v) for k, v in entities.items()},
                        'patterns_found': {k: len(v) for k, v in patterns.items()}
                    }
                })

            return result

        except Exception as e:
            logging.error(f"Erreur lors de l'anonymisation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'anonymized_text': text  # Retourne le texte original en cas d'erreur
            }

    def add_custom_pattern(self, name: str, pattern: str, replacement: str, priority: int = 1):
        """Ajoute un nouveau pattern personnalisé."""
        self.patterns.append(SensitivePattern(
            name=name,
            pattern=pattern,
            replacement=replacement,
            priority=priority
        ))