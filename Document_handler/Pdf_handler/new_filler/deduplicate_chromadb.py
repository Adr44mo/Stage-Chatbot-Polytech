#!/usr/bin/env python3
"""
Script de déduplication pour ChromaDB - Résout le problème des chunks dupliqués
"""

import os
import hashlib
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from config import OPENAI_API_KEY

# Configuration
VECTORSTORE_DIR = Path(__file__).parent / "Vectorisation" / "vectorstore_Syllabus"
BACKUP_DIR = Path(__file__).parent / "Vectorisation" / "vectorstore_backup"

def deduplicate_chromadb():
    """
    Déduplique la base ChromaDB en supprimant les chunks avec contenu identique
    """
    print("🔍 Démarrage de la déduplication ChromaDB...")
    
    try:
        # Initialiser les embeddings
        embeddings = OpenAIEmbeddings()
        
        # Charger la base vectorielle
        db = Chroma(persist_directory=str(VECTORSTORE_DIR), embedding_function=embeddings)
        
        # Obtenir tous les documents
        collection = db._collection
        all_docs = collection.get()
        
        print(f"📊 Documents avant déduplication: {len(all_docs['ids'])}")
        
        # Créer un mapping hash -> premier ID
        content_to_first_id = {}
        duplicates_to_remove = []
        
        for i, (doc_id, content, metadata) in enumerate(zip(
            all_docs['ids'], 
            all_docs['documents'], 
            all_docs['metadatas']
        )):
            # Créer un hash du contenu + métadonnées principales
            content_hash = create_content_hash(content, metadata)
            
            if content_hash in content_to_first_id:
                # C'est un doublon
                original_id = content_to_first_id[content_hash]
                duplicates_to_remove.append({
                    'id': doc_id,
                    'hash': content_hash,
                    'original_id': original_id,
                    'content_preview': content[:100] + "..." if len(content) > 100 else content
                })
                print(f"🔄 Doublon détecté: {doc_id} (original: {original_id})")
            else:
                # Premier exemplaire de ce contenu
                content_to_first_id[content_hash] = doc_id
        
        print(f"📋 Doublons identifiés: {len(duplicates_to_remove)}")
        
        if duplicates_to_remove:
            # Créer une sauvegarde avant suppression
            backup_chromadb()
            
            # Supprimer les doublons
            ids_to_remove = [dup['id'] for dup in duplicates_to_remove]
            
            print(f"🗑️ Suppression de {len(ids_to_remove)} doublons...")
            collection.delete(ids=ids_to_remove)
            
            # Vérifier le résultat
            remaining_docs = collection.get()
            print(f"✅ Documents après déduplication: {len(remaining_docs['ids'])}")
            print(f"📉 Doublons supprimés: {len(all_docs['ids']) - len(remaining_docs['ids'])}")
            
            # Sauvegarder les détails des doublons supprimés
            save_deduplication_report(duplicates_to_remove)
            
        else:
            print("✅ Aucun doublon détecté - base déjà propre")
            
    except Exception as e:
        print(f"❌ Erreur lors de la déduplication: {e}")
        raise

def create_content_hash(content: str, metadata: dict) -> str:
    """
    Crée un hash unique basé sur le contenu et certaines métadonnées clés
    """
    # Utiliser le contenu + quelques métadonnées clés pour la déduplication
    key_metadata = {
        'title': metadata.get('metadata.title', ''),
        'type': metadata.get('metadata.type', ''),
        'niveau': metadata.get('metadata.niveau', ''),
        'specialite': metadata.get('metadata.specialite', '')
    }
    
    # Créer une chaîne combinée
    combined = content + str(sorted(key_metadata.items()))
    
    # Hash SHA256
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def backup_chromadb():
    """
    Crée une sauvegarde de la base ChromaDB avant déduplication
    """
    import shutil
    
    if VECTORSTORE_DIR.exists():
        # Créer le dossier de sauvegarde avec timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"backup_{timestamp}"
        
        print(f"💾 Création sauvegarde: {backup_path}")
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(VECTORSTORE_DIR, backup_path)
        print(f"✅ Sauvegarde créée: {backup_path}")

def save_deduplication_report(duplicates):
    """
    Sauvegarde un rapport détaillé des doublons supprimés
    """
    import json
    from datetime import datetime
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_duplicates_removed": len(duplicates),
        "duplicates": duplicates
    }
    
    report_path = Path(__file__).parent / "deduplication_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📊 Rapport sauvegardé: {report_path}")

def analyze_duplicates_before_removal():
    """
    Analyse les doublons avant suppression pour diagnostic
    """
    print("🔍 Analyse des doublons (mode diagnostic)...")
    
    try:
        embeddings = OpenAIEmbeddings()
        db = Chroma(persist_directory=str(VECTORSTORE_DIR), embedding_function=embeddings)
        collection = db._collection
        all_docs = collection.get()
        
        # Analyser les doublons par hash
        content_groups = {}
        
        for i, (doc_id, content, metadata) in enumerate(zip(
            all_docs['ids'], 
            all_docs['documents'], 
            all_docs['metadatas']
        )):
            content_hash = create_content_hash(content, metadata)
            
            if content_hash not in content_groups:
                content_groups[content_hash] = []
            
            content_groups[content_hash].append({
                'id': doc_id,
                'content_preview': content[:100] + "..." if len(content) > 100 else content,
                'metadata': metadata
            })
        
        # Identifier les groupes de doublons
        duplicate_groups = {k: v for k, v in content_groups.items() if len(v) > 1}
        
        print(f"📊 Analyse des doublons:")
        print(f"  - Total documents: {len(all_docs['ids'])}")
        print(f"  - Groupes de contenu unique: {len(content_groups)}")
        print(f"  - Groupes avec doublons: {len(duplicate_groups)}")
        
        # Détails des groupes de doublons
        for i, (content_hash, group) in enumerate(duplicate_groups.items()):
            print(f"\n🔄 Groupe doublon #{i+1} (hash: {content_hash[:12]}...):")
            print(f"  - Nombre d'exemplaires: {len(group)}")
            print(f"  - Contenu: {group[0]['content_preview']}")
            for doc in group:
                print(f"    ID: {doc['id']}")
        
        return len(all_docs['ids']) - len(content_groups)  # Nombre de doublons
        
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")
        return 0

if __name__ == "__main__":
    print("🧹 Script de Déduplication ChromaDB")
    print("=" * 50)
    
    # 1. Analyser d'abord
    duplicates_count = analyze_duplicates_before_removal()
    
    if duplicates_count > 0:
        print(f"\n⚠️ {duplicates_count} doublons détectés")
        
        # Demander confirmation
        response = input("\n🤔 Procéder à la déduplication ? (y/N): ").strip().lower()
        
        if response in ['y', 'yes', 'oui']:
            print("\n🚀 Lancement de la déduplication...")
            deduplicate_chromadb()
            print("\n✅ Déduplication terminée!")
        else:
            print("❌ Déduplication annulée")
    else:
        print("\n✅ Aucun doublon détecté - base propre!")
