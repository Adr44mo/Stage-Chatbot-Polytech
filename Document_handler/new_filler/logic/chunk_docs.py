import re
from typing import List
from langchain.docstore.document import Document

def split_into_semantic_blocks(text: str) -> List[str]:
    """
    Sépare le texte en blocs sémantiques basés sur la structure du texte : 
    en-têtes, listes, tableaux et paragraphes.
    Gère aussi les textes PDF "aplatis" sans retours à la ligne.
    """
    # On nettoie les espaces en trop
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Pour les textes PDF aplatis, on essaie de recréer la structure
    # en détectant les patterns de listes dans le texte continu
    if '\n' not in text.strip() and len(text) > 500:
        # Texte PDF aplati : on ajoute des retours à la ligne avant les listes
        text = re.sub(r'(\s+)(-\s+[A-Z])', r'\1\n\2', text)  # - BDE, - Robotech, etc.
        text = re.sub(r'(\s+)(\*\*[^*]+\*\*\s*:)', r'\1\n\2', text)  # **Associations :**
        text = re.sub(r'(\s+)(\d+\.\s+[A-Z])', r'\1\n\2', text)  # 1. Something
    
    blocks = []
    current_block = ""
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip les lignes vides entre chaque bloc
        if not line:
            if current_block.strip():
                blocks.append(current_block.strip())
                current_block = ""
            i += 1
            continue
            
        # On détecte les différents types de blocs

        if _is_header(line):
            # On enregistre le bloc précédent
            if current_block.strip():
                blocks.append(current_block.strip())
            # On commence un nouveau bloc avec l'en-tête
            current_block = line + '\n'
            
        elif _is_list_item(line):
            # Pour les listes : on continue à ajouter à current_block
            # même si on était déjà dans une liste pour garder toute la liste ensemble
            if current_block.strip() and not (_is_list_item(current_block.split('\n')[-1]) or 
                                              current_block.split('\n')[-1].strip() == ""):
                # On sauvegarde seulement si on n'était pas dans une liste
                blocks.append(current_block.strip())
                current_block = ""
            current_block += line + '\n'
            
        elif _is_table_row(line):
            # Si on n'est pas déjà dans un tableau, on sauvegarde le bloc précédent
            if current_block.strip() and not _is_table_row(current_block.split('\n')[-1]):
                blocks.append(current_block.strip())
                current_block = ""
            current_block += line + '\n'
            
        else:
            # Paragraphe de texte normal
            if current_block and (_is_list_item(current_block.split('\n')[-1]) or 
                                _is_table_row(current_block.split('\n')[-1]) or
                                _is_header(current_block.split('\n')[-1])):
                blocks.append(current_block.strip())
                current_block = ""
            current_block += line + '\n'
            
        i += 1
    
    # Ajouter le bloc final
    if current_block.strip():
        blocks.append(current_block.strip())
    
    return [block for block in blocks if block.strip()]

def _is_header(line: str) -> bool:
    """Détecte les en-têtes dans du texte PDF normal"""
    stripped = line.strip()
    
    # En-têtes potentiels dans les PDFs :
    return (
        # Lignes courtes en majuscules (titres de sections)
        (stripped.isupper() and 10 <= len(stripped) <= 80) or
        
        # Numérotation de sections (1., 1.1, I., A., etc.)
        re.match(r'^[IVX]+\.?\s+[A-Z]', stripped) or  # Chiffres romains
        re.match(r'^\d+\.?\d*\.?\s+[A-Z]', stripped) or  # 1., 1.1., etc.
        re.match(r'^[A-Z]\.?\s+[A-Z]', stripped) or  # A., B., etc.
        
        # Lignes se terminant par ":" (souvent des titres)
        (stripped.endswith(':') and len(stripped) < 80 and not stripped.startswith('-')) or
        
        # Lignes centrées (beaucoup d'espaces avant/après)
        (len(line) - len(stripped) > 5 and len(stripped) < 80)
    )

def _is_list_item(line: str) -> bool:
    """Détecte les éléments de liste dans du texte PDF normal"""
    stripped = line.strip()
    
    return bool(
        # Puces traditionnelles
        re.match(r'^\s*[-*•·○▪▫]\s+', line) or
        
        # Numérotation simple
        re.match(r'^\s*\d+\.?\s+', line) or
        re.match(r'^\s*\d+\)\s+', line) or  # 1) format
        
        # Lettres pour sous-listes
        re.match(r'^\s*[a-z]\)\s+', line) or
        re.match(r'^\s*[A-Z]\)\s+', line) or
        
        # Indentation significative (souvent liste)
        (line.startswith('    ') or line.startswith('\t')) and len(stripped) > 10
    )

def _is_table_row(line: str) -> bool:
    """Détecte les lignes de tableau dans du texte PDF normal"""
    stripped = line.strip()
    
    # Dans les PDFs, les tableaux peuvent être :
    return (
        # Séparateurs de colonnes explicites
        '|' in stripped and stripped.count('|') >= 2 or
        
        # Plusieurs espaces consécutifs (colonnes alignées)
        re.search(r'\s{3,}', stripped) and len(stripped.split()) >= 3 or
        
        # Lignes avec beaucoup de chiffres/données tabulaires
        re.search(r'\d+\s+\d+\s+\d+', stripped) or
        
        # Lignes de séparation (tirets, underscores)
        re.match(r'^[-_\s]+$', stripped) and len(stripped) > 10
    )

def adaptive_semantic_chunk(text: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> List[str]:
    """
    Creates chunks by grouping semantic blocks for lists/tables/headers,
    but uses traditional splitting for regular paragraphs.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    blocks = split_into_semantic_blocks(text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    # Traditional splitter for regular text paragraphs
    fallback_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
    )
    
    for block in blocks:
        block_length = len(block)
        
        # Check if this block is a regular paragraph (not list/table/header)
        if _is_regular_paragraph(block):
            # For regular paragraphs, save current semantic chunk and use traditional splitting
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            # Split the paragraph traditionally and add each part
            paragraph_chunks = fallback_splitter.split_text(block)
            chunks.extend(paragraph_chunks)
            continue
        
        # For semantic blocks (lists, tables, headers), group them as before
        # Keep them intact even if they're long to preserve semantic meaning
        if current_length + block_length > chunk_size and current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(chunk_text)
            
            # Handle overlap: keep last block if it fits in overlap
            if chunk_overlap > 0 and current_chunk:
                last_block = current_chunk[-1]
                if len(last_block) <= chunk_overlap:
                    current_chunk = [last_block, block]
                    current_length = len(last_block) + block_length
                else:
                    current_chunk = [block]
                    current_length = block_length
            else:
                current_chunk = [block]
                current_length = block_length
        else:
            current_chunk.append(block)
            current_length += block_length
    
    # Add final chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return [chunk for chunk in chunks if chunk.strip()]

def _is_regular_paragraph(block: str) -> bool:
    """
    Détermine si un bloc est un paragraphe de texte normal 
    (pas une liste, table ou header).
    """
    lines = block.strip().split('\n')
    
    # Si le bloc contient principalement des éléments de liste, table ou headers
    semantic_lines = 0
    total_lines = len([line for line in lines if line.strip()])
    
    for line in lines:
        if line.strip() and (_is_list_item(line) or _is_table_row(line) or _is_header(line)):
            semantic_lines += 1
    
    # Si plus de 30% des lignes sont sémantiques, ce n'est pas un paragraphe normal
    if total_lines > 0 and (semantic_lines / total_lines) > 0.3:
        return False
    
    return True
