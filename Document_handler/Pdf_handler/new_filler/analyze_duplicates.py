#!/usr/bin/env python3
"""
Script pour analyser les doublons dans ChromaDB
"""

import os
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from config import OPENAI_API_KEY
import hashlib

# Configuration
VECTORSTORE_DIR = Path(__file__).parent / "Vectorisation" / "vectorstore_Syllabus"

def analyze_duplicates():
    """Analyse les doublons dans ChromaDB"""
    print("🔍 Analyse des doublons dans ChromaDB...")
    
    try:
        # Initialiser les embeddings
        embeddings = OpenAIEmbeddings()
        
        # Charger la base vectorielle
        db = Chroma(persist_directory=str(VECTORSTORE_DIR), embedding_function=embeddings)
        
        # Obtenir tous les documents
        collection = db._collection
        all_docs = collection.get()
        
        print(f"📊 Total documents: {len(all_docs['ids'])}")
        
        # Identifier les doublons par hash du contenu
        content_hashes = {}
        duplicates = []
        
        for i, (doc_id, content, metadata) in enumerate(zip(all_docs['ids'], all_docs['documents'], all_docs['metadatas'])):
            # Créer un hash du contenu
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            if content_hash in content_hashes:
                # C'est un doublon
                duplicates.append({
                    'hash': content_hash,
                    'duplicate_id': doc_id,
                    'original_id': content_hashes[content_hash]['id'],
                    'content': content[:200] + "..." if len(content) > 200 else content,
                    'metadata': metadata
                })
            else:
                # Premier exemplaire
                content_hashes[content_hash] = {
                    'id': doc_id,
                    'content': content,
                    'metadata': metadata
                }
        
        print(f"📋 Doublons identifiés: {len(duplicates)}")
        
        # Afficher les détails des doublons
        for i, dup in enumerate(duplicates):
            print(f"\n{'='*60}")
            print(f"DOUBLON #{i+1}")
            print(f"{'='*60}")
            print(f"Hash: {dup['hash']}")
            print(f"ID Original: {dup['original_id']}")
            print(f"ID Doublon: {dup['duplicate_id']}")
            print(f"Métadonnées: {dup['metadata']}")
            print(f"Contenu: {dup['content']}")
            print()
        
        # Statistiques sur les doublons
        if duplicates:
            print(f"\n📊 Statistiques:")
            print(f"  - Documents uniques: {len(all_docs['ids']) - len(duplicates)}")
            print(f"  - Documents dupliqués: {len(duplicates)}")
            print(f"  - Taux de duplication: {len(duplicates)/len(all_docs['ids'])*100:.1f}%")
            
            # Analyser les types de doublons
            toc_duplicates = [d for d in duplicates if d['metadata'] and 'toc' in d['metadata'].get('tags', '')]
            print(f"  - Doublons TOC: {len(toc_duplicates)}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    analyze_duplicates()
