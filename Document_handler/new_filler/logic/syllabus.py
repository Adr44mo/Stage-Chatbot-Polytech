import fitz  # PyMuPDF
import re
import json
import os
from ..config import INPUT_DIR

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    return text

def extract_toc_and_courses(text):
    # 1. Trouver la DEUXIÈME occurrence de "Syllabus des enseignements"
    occurrences = list(re.finditer(r'Syllabus des enseignements', text))
    if len(occurrences) < 2:
        # S'il n'y a qu'une occurrence, on la prend quand même
        toc_start_match = occurrences[0] if occurrences else None
    else:
        # Sinon on prend la deuxième occurrence
        toc_start_match = occurrences[1]
    
    if not toc_start_match:
        raise ValueError("Début de la table des matières non trouvé ('Syllabus des enseignements')")
    toc_start = toc_start_match.end()
    
    # 2. Trouver la fin de la table des matières (première fiche)
    fiche_match = re.search(r'Fiche Syllabus', text)
    if not fiche_match:
        raise ValueError("Fin de la table des matières non trouvée ('Fiche Syllabus')")
    toc_end = fiche_match.start()
    
    # 3. Extraire le texte de la table des matières
    toc_text = text[toc_start:toc_end]
    toc_lines = [l.strip() for l in toc_text.splitlines() if l.strip()]
    
    # 3b. Filtrer les lignes de bas de page et en-têtes
    filtered_lines = []
    for line in toc_lines:
        # Ignorer les lignes qui ressemblent à des bas de page/en-têtes
        if any(pattern in line for pattern in [
            "Polytech Sorbonne", "Bâtiment Esclangon", "Tél :", "Fax :", 
            "email :", "http://", "Case Courrier"
        ]):
            continue
        filtered_lines.append(line)
    
    toc_lines = filtered_lines
    
    # 4. Extraire les entrées de la table des matières
    toc_entries = []
    seen_codes = set()  # Pour suivre les codes déjà rencontrés
    
    for line in toc_lines:
        # 1) Cherche codes EPU suivis d'un titre puis des pointillés et un numéro de page
        match = re.search(r'(EPU-[A-Z0-9\-]+)\s*-\s*([^\.]+?)(?:\.{2,}|\s{3,})\s*(\d+)(?:\s|$)', line)
        if match:
            code = match.group(1)
            # Vérifier si ce code a déjà été traité
            if code in seen_codes:
                continue  # Ignorer les doublons
                
            seen_codes.add(code)  # Marquer ce code comme traité
            title = match.group(2).strip()
            page = int(match.group(3))
            toc_entries.append({
                "code": code,
                "title": title,
                "page": page
            })
            continue
        
        # 2) Cherche simplement les codes EPU suivis d'un titre (sans page)
        match = re.search(r'(EPU-[A-Z0-9\-]+)\s*-\s*(.+)', line)
        if match:
            code = match.group(1)
            # Vérifier si ce code a déjà été traité
            if code in seen_codes:
                continue  # Ignorer les doublons
                
            seen_codes.add(code)  # Marquer ce code comme traité
            title = match.group(2).strip()
            toc_entries.append({
                "code": code,
                "title": title,
                "page": 0  # Page inconnue
            })
    
    # 5. Extraire les fiches de cours après "Fiche Syllabus"
    courses_text = text[fiche_match.start():]
    # Trouver toutes les occurrences de "Fiche Syllabus"
    fiche_starts = [m.start() for m in re.finditer(r'Fiche Syllabus', courses_text)]
    
    courses = []
    seen_course_codes = set()  # Pour suivre les codes de cours déjà rencontrés
    
    for i in range(len(fiche_starts)):
        start = fiche_starts[i]
        end = fiche_starts[i+1] if i+1 < len(fiche_starts) else len(courses_text)
        course_text = courses_text[start:end]
        
        # Extraire code et titre du cours
        code_match = re.search(r'(EPU-[A-Z0-9\-]+)\s*-\s*(.+?)\n', course_text)
        if code_match:
            code = code_match.group(1)
            # Vérifier si ce code de cours a déjà été traité
            if code in seen_course_codes:
                continue  # Ignorer les doublons
                
            seen_course_codes.add(code)  # Marquer ce code comme traité
            title = code_match.group(2).strip()
            courses.append({
                "code": code,
                "title": title,
                "content": course_text.strip()
            })
    
    return toc_entries, courses

def extract_syllabus_structure(pdf_path):
    # Extraire la spécialité à partir du nom du dossier parent
    specialite = os.path.basename(os.path.dirname(pdf_path))
    
    text = extract_text_from_pdf(pdf_path)
    toc, courses = extract_toc_and_courses(text)
    
    return {
        "syllabus": str(pdf_path),
        "specialite": specialite,  # Ajout de la spécialité
        "toc": toc,
        "courses": courses
    }

# 🎯 Test interactif
if __name__ == "__main__":
    pdf_path = INPUT_DIR / "pdf_man" / "MAIN" / "syllabus_MAIN.pdf"  # Mets le chemin local ici
    # /srv/partage/Stage-Chatbot-Polytech/Document_handler/Corpus/test/pdf_man/MAIN/syllabus_MAIN.pdf
    # /srv/partage/Stage-Chatbot-Polytech/Document_handler/Corpus/test/pdf_man/MAIN/syllabus_Main.pdf
    print("Extraction du syllabus à partir de :", pdf_path)
    result = extract_syllabus_structure(pdf_path)

    print("\n📘 Table des matières détectée :")
    for toc_entry in result["toc"]:
        print(f"- {toc_entry['code']} : {toc_entry['title']}" + 
              (f" (p. {toc_entry['page']})" if toc_entry['page'] > 0 else ""))

    print("\n📚 Cours extraits :")
    for course in result["courses"]:
        print(f"- {course['code']} : {course['title']}")

    # Optionnel : dump JSON
    json_path = os.path.splitext(pdf_path)[0] + ".json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
