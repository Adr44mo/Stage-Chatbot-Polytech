#!/usr/bin/env python3
"""
Script to extract and display all documents with 'toc' tag from the vectorstore
"""
import sys
import os
from pathlib import Path
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage

# Import only what we need from existing modules
from ...app.keys_file import OPENAI_API_KEY
from ...app.llmm import initialize_the_rag_chain, llm, db
from ...app.chat import get_sources

def extract_toc_documents():
    """Extract all documents with 'toc' tag and display their content and metadata"""
    
    print("=== Extracting TOC Documents ===\n")
    
    try:
        # Strategy 1: Try to search for documents with 'toc' in tags using similarity search
        print("Strategy 1: Searching for documents with 'toc' keyword...")
        toc_search_results = db.similarity_search("table of contents toc syllabus", k=100)
        
        toc_documents = []
        
        # Filter documents that have 'toc' in their tags
        for doc in toc_search_results:
            tags = doc.metadata.get("tags", "")
            if "toc" in str(tags).lower():
                toc_documents.append(doc)
                print(f"✓ Found TOC document: {doc.metadata.get('metadata.title', 'No title')}")
        
        print(f"\nFound {len(toc_documents)} documents with 'toc' tag using similarity search\n")
        
        if not toc_documents:
            print("No documents found with 'toc' tag. Let's try broader searches...\n")
            
            # Strategy 2: Search for documents with MAIN speciality
            print("Strategy 2: Searching for MAIN speciality documents...")
            main_results = db.similarity_search("MAIN specialite cours", k=50)
            
            for doc in main_results:
                tags = doc.metadata.get("tags", "")
                specialite = doc.metadata.get("metadata.specialite", "")
                
                if ("MAIN" in str(tags) or "MAIN" in str(specialite)) and "toc" in str(tags).lower():
                    toc_documents.append(doc)
                    print(f"✓ Found MAIN TOC document: {doc.metadata.get('metadata.title', 'No title')}")
            
            print(f"\nTotal TOC documents found: {len(toc_documents)}\n")
        
        # Display all TOC documents
        if toc_documents:
            print("=" * 80)
            print("TOC DOCUMENTS DETAILS")
            print("=" * 80)
            
            for i, doc in enumerate(toc_documents, 1):
                print(f"\n--- TOC Document {i} ---")
                print(f"Title: {doc.metadata.get('metadata.title', 'N/A')}")
                print(f"Document Type: {doc.metadata.get('document_type', 'N/A')}")
                print(f"Source: {doc.metadata.get('source.chemin_local', 'N/A')}")
                print(f"Specialite: {doc.metadata.get('metadata.specialite', 'N/A')}")
                print(f"Type: {doc.metadata.get('metadata.type', 'N/A')}")
                print(f"Section: {doc.metadata.get('metadata.section', 'N/A')}")
                print(f"Tags: {doc.metadata.get('tags', 'N/A')}")
                print(f"Full Metadata: {doc.metadata}")
                print(f"\nContent Preview (first 500 chars):")
                print("-" * 40)
                print(doc.page_content[:500])
                if len(doc.page_content) > 500:
                    print("... (truncated)")
                print("-" * 40)
                
                if i < len(toc_documents):
                    print("\n" + "=" * 60)
        else:
            print("❌ No documents with 'toc' tag were found.")
            print("This suggests that TOC documents are either:")
            print("1. Not properly tagged during vectorization")
            print("2. Not present in the vectorstore")
            print("3. Tagged differently than expected")
            
            # Let's check what tags are actually available
            print("\n=== Checking available document types and tags ===")
            sample_docs = db.similarity_search("", k=20)  # Get some sample documents
            
            unique_tags = set()
            unique_types = set()
            unique_specialites = set()
            
            for doc in sample_docs:
                tags = doc.metadata.get("tags", "")
                doc_type = doc.metadata.get("document_type", "")
                specialite = doc.metadata.get("metadata.specialite", "")
                
                if tags:
                    unique_tags.update([tag.strip() for tag in str(tags).split(",")])
                if doc_type:
                    unique_types.add(doc_type)
                if specialite:
                    unique_specialites.add(specialite)
            
            print(f"\nUnique document types found: {list(unique_types)}")
            print(f"Unique specialites found: {list(unique_specialites)}")
            print(f"Sample tags found: {list(unique_tags)[:20]}...")  # Show first 20 tags
            
    except Exception as e:
        print(f"❌ Error during TOC extraction: {e}")
        import traceback
        traceback.print_exc()

def search_for_specific_patterns():
    """Search for documents that might be TOC documents using different patterns"""
    
    print("\n=== Searching for potential TOC documents using different patterns ===\n")
    
    search_patterns = [
        "table des matières",
        "table of contents", 
        "syllabus",
        "cours programme",
        "semestre",
        "MAIN"
    ]
    
    for pattern in search_patterns:
        print(f"Searching for pattern: '{pattern}'")
        try:
            results = db.similarity_search(pattern, k=10)
            print(f"  Found {len(results)} documents")
            
            # Check if any have TOC-like metadata
            for doc in results[:3]:  # Just check first 3
                metadata = doc.metadata
                tags = metadata.get("tags", "")
                doc_type = metadata.get("document_type", "")
                title = metadata.get("metadata.title", "")
                
                if any(keyword in str(tags).lower() for keyword in ["toc", "table", "syllabus"]):
                    print(f"  ✓ Potential TOC: {title} (tags: {tags})")
                elif any(keyword in str(title).lower() for keyword in ["table", "matières", "syllabus"]):
                    print(f"  ✓ Potential TOC by title: {title}")
                    
        except Exception as e:
            print(f"  ❌ Error searching for '{pattern}': {e}")
        
        print()

if __name__ == "__main__":
    print("Starting TOC Document Extraction...")
    print(f"Working directory: {os.getcwd()}")
    print(f"Script location: {Path(__file__).parent}\n")
    
    # Extract TOC documents
    extract_toc_documents()
    
    # Search for potential TOC documents
    search_for_specific_patterns()
    
    print("\n🔍 TOC Document Extraction Complete!")
