import re
import numpy as np
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging

logger = logging.getLogger(__name__)

class IntelligentSemanticChunker:
    """
    Chunker sémantique intelligent qui distingue les vraies listes des fausses listes (mise en page).
    Logique : 
    - Vraies listes (items courts) → préservées intactes
    - Fausses listes (items = gros paragraphes) → chunking par similarité sémantique
    """
    
    def __init__(self, similarity_threshold: float = 0.65):
        self.model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        self.similarity_threshold = similarity_threshold
        self.fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=['\n\n', '\n', '. ', '! ', '? ', '; ', ', ', ' ', '']
        )
    
    def chunk_text(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """
        Chunking intelligent avec détection des vraies vs fausses listes.
        """
        # Étape 1: Identifier les sections structurelles
        sections = self._identify_complete_sections(text)
        
        if not sections:
            # Pas de structure → chunking sémantique classique
            return self._fallback_semantic_chunk(text, max_chunk_size)
        
        # Étape 2: Traiter chaque section intelligemment
        final_chunks = []
        for section in sections:
            section_chunks = self._process_section_intelligently(section, max_chunk_size)
            final_chunks.extend(section_chunks)
        
        return final_chunks
    
    def _identify_complete_sections(self, text: str) -> List[str]:
        """
        Identifie les sections complètes avec leurs titres et tout leur contenu.
        """
        sections = []
        
        # Pattern pour les sections avec titre en gras
        pattern = r'(\*\*[^*]+\*\*\s*:.*?)(?=\*\*[^*]+\*\*\s*:|$)'
        
        matches = list(re.finditer(pattern, text, re.DOTALL))
        
        if not matches:
            return []  # Pas de structure détectée
        
        last_end = 0
        
        # Traiter le texte avant la première section
        if matches[0].start() > 0:
            before_section = text[:matches[0].start()].strip()
            if before_section:
                sections.append(before_section)
        
        # Traiter chaque section complète
        for match in matches:
            section_content = match.group(1).strip()
            if section_content:
                sections.append(section_content)
            last_end = match.end()
        
        # Traiter le texte après la dernière section
        if last_end < len(text):
            after_section = text[last_end:].strip()
            if after_section:
                sections.append(after_section)
        
        return sections
    
    def _process_section_intelligently(self, section: str, max_chunk_size: int) -> List[str]:
        """
        Traite une section en distinguant vraies vs fausses listes.
        """
        # Vérifier si c'est une section avec liste
        if not self._has_list_structure(section):
            # Pas de liste → traitement normal
            if len(section) <= max_chunk_size * 1.3:
                return [section]
            else:
                return self._fallback_semantic_chunk(section, max_chunk_size)
        
        # Analyser le type de liste
        list_analysis = self._analyze_list_type(section)
        
        if list_analysis['type'] == 'true_list':
            # Vraie liste → préserver intacte si possible
            return self._handle_true_list(section, max_chunk_size)
        
        elif list_analysis['type'] == 'false_list':
            # Fausse liste → chunking sémantique par items
            return self._handle_false_list(section, max_chunk_size, list_analysis['items'])
        
        else:
            # Cas ambigu → traitement conservateur
            return self._fallback_semantic_chunk(section, max_chunk_size)
    
    def _has_list_structure(self, text: str) -> bool:
        """
        Vérifie si le texte contient une structure de liste.
        """
        return text.count(' - ') >= 2 or text.count('• ') >= 2
    
    def _analyze_list_type(self, section: str) -> dict:
        """
        Analyse si c'est une vraie liste ou une fausse liste (mise en page).
        
        Critères :
        - Vraie liste : items courts (< 200 chars en moyenne), sujets similaires
        - Fausse liste : items longs (> 300 chars en moyenne), sujets différents
        """
        # Extraire le titre
        title_match = re.search(r'(\*\*[^*]+\*\*\s*:)', section)
        title = title_match.group(1) if title_match else ""
        
        # Extraire les items de la liste
        content_start = title_match.end() if title_match else 0
        content = section[content_start:].strip()
        
        # Diviser par items
        items = re.split(r'(?=\s*[-•]\s+)', content)
        items = [item.strip() for item in items if item.strip() and ('-' in item or '•' in item)]
        
        if len(items) < 2:
            return {'type': 'unknown', 'items': []}
        
        # Analyser la longueur des items
        item_lengths = [len(item) for item in items]
        avg_length = sum(item_lengths) / len(item_lengths)
        max_length = max(item_lengths)
        
        logger.info(f"Analyse de liste : {len(items)} items, longueur moyenne : {avg_length:.0f}, max : {max_length}")
        
        # Critères de classification
        if avg_length < 200 and max_length < 400:
            # Items courts → probablement une vraie liste
            return {
                'type': 'true_list',
                'items': items,
                'title': title,
                'avg_length': avg_length
            }
        
        elif avg_length > 300 or max_length > 600:
            # Items longs → probablement une fausse liste (mise en page)
            return {
                'type': 'false_list',
                'items': items,
                'title': title,
                'avg_length': avg_length
            }
        
        else:
            # Cas ambigu → analyse sémantique pour décider
            return self._analyze_semantic_coherence(items, title, avg_length)
    
    def _analyze_semantic_coherence(self, items: List[str], title: str, avg_length: float) -> dict:
        """
        Analyse la cohérence sémantique des items pour déterminer le type de liste.
        """
        if len(items) < 3:
            return {'type': 'true_list', 'items': items, 'title': title}
        
        try:
            # Calculer les embeddings des items (limiter à 10 pour la performance)
            sample_items = items[:10]
            embeddings = self.model.encode(sample_items, show_progress_bar=False)
            
            # Calculer la similarité moyenne entre tous les items
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                    similarities.append(sim)
            
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0
            
            logger.info(f"Similarité sémantique moyenne : {avg_similarity:.3f}")
            
            # Si les items sont sémantiquement similaires → vraie liste
            if avg_similarity > 0.6:
                return {
                    'type': 'true_list',
                    'items': items,
                    'title': title,
                    'semantic_score': avg_similarity
                }
            else:
                return {
                    'type': 'false_list',
                    'items': items,
                    'title': title,
                    'semantic_score': avg_similarity
                }
                
        except Exception as e:
            logger.warning(f"Erreur lors de l'analyse sémantique: {e}")
            # En cas d'erreur, être conservateur
            return {'type': 'true_list', 'items': items, 'title': title}
    
    def _handle_true_list(self, section: str, max_chunk_size: int) -> List[str]:
        """
        Traite une vraie liste en essayant de la préserver intacte.
        """
        # Si la section entière est raisonnable → la garder intacte
        if len(section) <= max_chunk_size * 2:  # Tolérance généreuse pour les vraies listes
            logger.info(f"Vraie liste préservée intacte : {len(section)} chars")
            return [section]
        
        # Si trop longue → diviser intelligemment mais garder le contexte
        logger.info(f"Vraie liste trop longue, division avec contexte...")
        return self._split_long_true_list(section, max_chunk_size)
    
    def _handle_false_list(self, section: str, max_chunk_size: int, items: List[str]) -> List[str]:
        """
        Traite une fausse liste en appliquant le chunking sémantique par items.
        """
        logger.info(f"Fausse liste détectée, chunking sémantique par items...")
        
        # Extraire le titre pour le contexte
        title_match = re.search(r'(\*\*[^*]+\*\*\s*:)', section)
        title = title_match.group(1) if title_match else ""
        
        # Appliquer le chunking sémantique sur les items
        return self._semantic_chunk_items(items, title, max_chunk_size)
    
    def _semantic_chunk_items(self, items: List[str], title: str, max_chunk_size: int) -> List[str]:
        """
        Applique le chunking sémantique sur les items d'une fausse liste.
        """
        if len(items) <= 1:
            return [title + " " + " ".join(items)] if title else items
        
        try:
            # Calculer les embeddings
            embeddings = self.model.encode(items, show_progress_bar=False)
            
            chunks = []
            used = set()
            
            for i, item in enumerate(items):
                if i in used:
                    continue
                
                # Commencer un nouveau chunk
                current_chunk = [item]
                current_length = len(title) + len(item) if title else len(item)
                used.add(i)
                
                # Chercher des items similaires
                for j in range(i + 1, len(items)):
                    if j in used:
                        continue
                    
                    # Vérifier la similarité
                    similarity = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                    
                    if similarity >= self.similarity_threshold:
                        # Vérifier si on peut l'ajouter sans dépasser la taille
                        item_length = len(items[j])
                        if current_length + item_length <= max_chunk_size * 1.2:
                            current_chunk.append(items[j])
                            current_length += item_length
                            used.add(j)
                
                # Créer le chunk final avec le titre pour le contexte
                chunk_text = title + " " + " ".join(current_chunk) if title else " ".join(current_chunk)
                
                # Si le chunk est trop gros, le redécouper
                if len(chunk_text) > max_chunk_size * 1.3:
                    sub_chunks = self.fallback_splitter.split_text(chunk_text)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(chunk_text)
            
            logger.info(f"Fausse liste divisée en {len(chunks)} chunks sémantiques")
            return chunks
            
        except Exception as e:
            logger.warning(f"Erreur lors du chunking sémantique des items: {e}")
            # Fallback : un chunk par item avec titre
            return [f"{title} {item}" if title else item for item in items]
    
    def _split_long_true_list(self, section: str, max_chunk_size: int) -> List[str]:
        """
        Divise une vraie liste trop longue en gardant le contexte.
        """
        title_match = re.search(r'(\*\*[^*]+\*\*\s*:)', section)
        title = title_match.group(1) if title_match else ""
        
        content_start = title_match.end() if title_match else 0
        content = section[content_start:].strip()
        
        items = re.split(r'(?=\s*[-•]\s+)', content)
        items = [item.strip() for item in items if item.strip()]
        
        chunks = []
        current_chunk = title
        current_length = len(title)
        
        for item in items:
            item_length = len(item)
            
            if current_length + item_length > max_chunk_size and current_chunk != title:
                chunks.append(current_chunk.strip())
                current_chunk = title + " " + item
                current_length = len(current_chunk)
            else:
                current_chunk += " " + item
                current_length += item_length
        
        if current_chunk.strip() and current_chunk.strip() != title.strip():
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [section]
    
    def _fallback_semantic_chunk(self, text: str, max_chunk_size: int) -> List[str]:
        """
        Chunking sémantique classique pour les textes sans structure particulière.
        """
        if len(text) <= max_chunk_size * 1.2:
            return [text]
        
        return self.fallback_splitter.split_text(text)


# Instance globale pour éviter de recharger le modèle
_intelligent_chunker = None

def adaptive_semantic_chunk(text: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> List[str]:
    """
    Chunking sémantique intelligent qui distingue les vraies des fausses listes.
    """
    global _intelligent_chunker
    if _intelligent_chunker is None:
        _intelligent_chunker = IntelligentSemanticChunker()
    
    return _intelligent_chunker.chunk_text(text, max_chunk_size=chunk_size)