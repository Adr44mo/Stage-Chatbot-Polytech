import json
import re
from langchain.docstore.document import Document

def chunk_syllabus_for_rag(syllabus_data):
    """
    Transforme un ou plusieurs syllabus en documents compatibles
    
    Args:
        syllabus_data (dict or list): Dictionnaire ou liste de dictionnaires
        
    Returns:
        list: Liste de documents prêts pour la vectorisation
    """
    # Si c'est une liste, traite chaque élément séparément et combine les résultats
    if isinstance(syllabus_data, list):
        print(f"Traitement de {len(syllabus_data)} syllabus")
        all_documents = []
        for item in syllabus_data:
            documents = chunk_syllabus_for_rag(item)  # Appel récursif pour chaque syllabus
            all_documents.extend(documents)
        return all_documents
    
    # Récupérer les métadonnées dynamiques du syllabus
    syllabus_path = syllabus_data.get("syllabus", "chemin inconnu")
    specialite = syllabus_data.get("specialite", "UNKNOWN")
    
    documents = []
    
    # Vérifier que nous avons bien un dictionnaire avec une clé "toc"
    if not isinstance(syllabus_data, dict) or "toc" not in syllabus_data:
        print(f"⚠️ Format de syllabus non reconnu: {type(syllabus_data)}")
        if isinstance(syllabus_data, dict):
            print(f"Clés disponibles: {list(syllabus_data.keys())}")
        return []
    
    # 1. Chunker la TOC par semestre
    toc_by_semester = {}
    for entry in syllabus_data.get("toc", []):
        if not entry.get("code"):
            continue
            
        # Extraire le semestre depuis le code (EPU-N5-XXX -> Semestre 5)
        semester_match = re.search(r'EPU-[A-Z](\d)-', entry.get("code", ""))
        if semester_match:
            semester = semester_match.group(1)
            if semester not in toc_by_semester:
                toc_by_semester[semester] = []
            toc_by_semester[semester].append(entry)
    
    # Créer un document par semestre
    for semester, entries in toc_by_semester.items():
        semester_name = f"Semestre {semester}" if semester != "0" else "Stages et fin d'études"
        
        # Construire le contenu de la TOC
        content = f"# Table des matières - {semester_name}\n\n"
        for entry in entries:
            content += f"- {entry['code']} : {entry['title']}\n"
        
        # Créer un document au format compatible avec métadonnées dynamiques
        documents.append({
            "content": content,
            "document_type": "cours",  # Utiliser "cours" au lieu de "syllabus"
            "metadata": {
                "title": f"Table des matières - {semester_name}",  # Utiliser "title" au lieu de "titre"
                "type": "toc",
                "specialite": specialite,  # Utilisation de la valeur dynamique
                "secteur": specialite,
                "niveau": f"Semestre {semester}"
            },
            "source": {
                "category": "pdf_ajouté_manuellement",  # Standardiser selon le schéma
                "chemin_local": syllabus_path,  # Utilisation de la valeur dynamique
                "site": specialite  # Utiliser specialite comme site
            },
            "tags": ["toc", "syllabus", f"semestre-{semester}", specialite]  # Ajout de la spécialité aux tags
        })
    
    # 2. Chunker les cours en sections
    for course in syllabus_data.get("courses", []):
        course_documents = chunk_course_to_documents(course, syllabus_path, specialite)  # Passage des données dynamiques
        documents.extend(course_documents)
    
    return documents

def chunk_course_to_documents(course, syllabus_path, specialite):
    """
    Divise un cours en documents compatibles avec convert_to_documents()
    """
    documents = []
    code = course.get("code", "")
    title = course.get("title", "")
    content = course.get("content", "")
    
    # Extraire le semestre
    semester_match = re.search(r'EPU-[A-Z](\d)-', code)
    semester = semester_match.group(1) if semester_match else "0"
    
    # Tags communs pour tous les documents de cours
    common_tags = ["cours", "syllabus", f"semestre-{semester}", code, specialite, title]
    
    # 1. Informations générales
    info_content = extract_general_info(content, title, code)
    documents.append({
        "content": info_content,
        "document_type": "cours",  # Utiliser "cours" au lieu de "syllabus"
        "metadata": {
            "title": title,  # Utiliser "title" au lieu de "titre"
            "code": code,
            "type": "fiche_cours",
            "section": "information_generale",
            "specialite": specialite,  # Utilisation de la valeur dynamique
            "secteur": specialite,
            "niveau": f"Semestre {semester}"
        },
        "source": {
            "category": "pdf_ajouté_manuellement",  # Standardiser selon le schéma
            "chemin_local": syllabus_path,  # Utilisation de la valeur dynamique
            "site": specialite  # Utiliser specialite comme site
        },
        "tags": common_tags  # Ajout des tags communs
    })
    
    # 2. Objectifs pédagogiques
    objectives = extract_objectives(content)
    if objectives:
        documents.append({
            "content": f"# Objectifs pédagogiques - {title} ({code})\n\n{objectives}",
            "document_type": "cours",  # Utiliser "cours" au lieu de "syllabus"
            "metadata": {
                "title": title,  # Utiliser "title" au lieu de "titre"
                "code": code,
                "type": "fiche_cours",
                "section": "objectifs",
                "specialite": specialite,  # Utilisation de la valeur dynamique
                "secteur": specialite,
                "niveau": f"Semestre {semester}"
            },
            "source": {
                "category": "pdf_ajouté_manuellement",  # Standardiser selon le schéma
                "chemin_local": syllabus_path,  # Utilisation de la valeur dynamique
                "site": specialite  # Utiliser specialite comme site
            },
            "tags": common_tags  # Ajout des tags communs
        })
    
    # 3. Programme détaillé
    program = extract_program(content)
    if program:
        documents.append({
            "content": f"# Programme - {title} ({code})\n\n{program}",
            "document_type": "cours",  # Utiliser "cours" au lieu de "syllabus"
            "metadata": {
                "title": title,  # Utiliser "title" au lieu de "titre"
                "code": code,
                "type": "fiche_cours",
                "section": "programme",
                "specialite": specialite,  # Utilisation de la valeur dynamique
                "secteur": specialite,
                "niveau": f"Semestre {semester}"
            },
            "source": {
                "category": "pdf_ajouté_manuellement",  # Standardiser selon le schéma
                "chemin_local": syllabus_path,  # Utilisation de la valeur dynamique
                "site": specialite  # Utiliser specialite comme site
            },
            "tags": common_tags  # Ajout des tags communs
        })
    
    # Ajoutez d'autres sections selon besoin...
    
    return documents

def extract_general_info(content, title, code):
    """Extrait les informations générales du cours"""
    info_sections = ["UE", "Spécialité", "Volume horaire", "Crédits"]
    info_text = f"# {title} ({code})\n\n"
    
    for section in info_sections:
        pattern = re.compile(f"{section}.*?:(.*?)(?={section}|$)", re.DOTALL | re.IGNORECASE)
        match = pattern.search(content)
        if match:
            info_text += f"**{section}**: {match.group(1).strip()}\n\n"
    
    return info_text

def extract_objectives(content):
    """Extrait les objectifs pédagogiques"""
    # Cherche après "Volume horaire" et avant "Prérequis" ou "Programme"
    pattern = re.compile(r"(?:compétences|objectifs).*?\n(.*?)(?:Prérequis|Programme)", re.DOTALL | re.IGNORECASE)
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return ""

def extract_program(content):
    """Extrait le programme du cours"""
    pattern = re.compile(r"(?:Programme|Contenu).*?\n(.*?)(?:Prérequis|Compétences|Évaluation)", re.DOTALL | re.IGNORECASE)
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return ""


if __name__ == "__main__":
    # Charger le syllabus
    with open("/srv/partage/Stage-Chatbot-Polytech/Document_handler/Pdf_handler/new_filler/logic/syllabus_MAIN.json", "r") as f:
        syllabus_data = json.load(f)

    # Générer les chunks pour RAG
    chunks = chunk_syllabus_for_rag(syllabus_data)

    # Afficher quelques statistiques
    print(f"Nombre total de chunks générés: {len(chunks)}")
    print(f"Types de chunks: {set(chunk['metadata']['type'] for chunk in chunks if 'type' in chunk.get('metadata', {}))}")
    
    sections = set(chunk['metadata'].get('section', '') for chunk in chunks if 'section' in chunk.get('metadata', {}))
    print(f"Sections: {sections}")

    # affiche tout les chunck de type toc en entier
    toc_chunks = [chunk for chunk in chunks if chunk.get('metadata', {}).get('type') == 'toc']
    print(f"Nombre de chunks de type 'toc': {len(toc_chunks)}")
    for toc in toc_chunks:
        print(f"TOC: {toc['content'][:5000]}")  # Affiche les 5000 premiers caractères

    ## Test affichage de tous les chunks
    #for chunk in chunks:
    #    print(f"Document type: {chunk.get('document_type', 'N/A')}")
    #    if 'metadata' in chunk:
    #        print(f"Type: {chunk['metadata'].get('type', 'N/A')}")
    #        print(f"Section: {chunk['metadata'].get('section', 'N/A')}")
    #        print(f"Titre: {chunk['metadata'].get('titre', 'N/A')}")
    #    print(f"Contenu: {chunk['content'][:10000]}...")  # Affiche les 10000 premiers caractères
    #    print("-" * 40)
#
    # Exemple d'insertion dans ChromaDB
    # import chromadb
    # client = chromadb.Client()
    # collection = client.create_collection("syllabus_polytech")
    # 
    # for chunk in chunks:
    #     collection.add(
    #         ids=[chunk["id"]],
    #         documents=[chunk["content"]],
    #         metadatas=[chunk["metadata"]]
    #     )