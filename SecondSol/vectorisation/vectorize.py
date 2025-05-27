# load env variables
from dotenv import load_dotenv  # Import the load_dotenv function from the dotenv module
load_dotenv('../.env')  # Load environment variables from the ../.env file

# imports
import os # Import the os module for interacting with the operating system
# Set up env variables
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')  # Set the OPENAI_API_KEY environment variable

import glob  # Import the glob module for finding pathnames matching a specified pattern
import os
import json
from langchain_core.documents import Document
from itertools import groupby
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

def load_jsonl(file_path):
    """Load JSONL file into a list of Documents with metadata."""
    documents = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            content = data.get('content', '')
            metadata = {
                'source': data.get('source', ''),
                'file_name': data.get('file_name', ''),
                'url': data.get('url', ''),
                **data.get('metadata', {})
            }
            documents.append(Document(page_content=content, metadata=metadata))
    return documents

def process_jsonl_files(file_paths, persist_path):
    embeddings = OpenAIEmbeddings()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    all_splits = []
    all_ids = []
    
    try:
        for file_path in file_paths:
            print(f'[INFO] (Started) Processing file: {os.path.basename(file_path)}')
            docs = load_jsonl(file_path)
            for json_index, doc in enumerate(docs):
                # Split the document's content into chunks
                splits = text_splitter.split_documents([doc])
                
                # Generate source filename
                source = doc.metadata.get('file_name')
                if not source:
                    source_path = doc.metadata.get('source', '')
                    source = os.path.basename(source_path) if source_path else 'unknown_source'
                
                # Generate IDs for each chunk
                for chunk_index, split in enumerate(splits):
                    chunk_id = f"{source}_{json_index}_{chunk_index}"
                    all_ids.append(chunk_id)
                all_splits.extend(splits)
            
            print(f'[INFO] (Complete) File ingested: {os.path.basename(file_path)}')
        
        # Load all splits into ChromaDB
        db = Chroma.from_documents(
            documents=all_splits,
            embedding=embeddings,
            persist_directory=persist_path,
            ids=all_ids
        )
        print(f'[INFO] All files ingested successfully. Total chunks: {len(all_splits)}')
        print(f"[INFO] ChromaDB collection count: {db._collection.count()}")
    
    except Exception as e:
        print(f'[ERROR] Failed to process files: {e}')
    
    return db


if __name__ == "__main__":
    # Set the data source and persist paths
    print(f"[INFO] Starting vectorization process...")  # Print a message indicating the start of the vectorization process

    data_source = 'src'  # Path to the directory containing the data files
    persist_path = 'src/db'  # Path to the directory where data will be persisted

    # Specify the directory path and file extension
    extension = '*.jsonl'  # Set the file extension to search for (PDF files)

    # Get a list of file paths matching the extension
    file_paths = glob.glob(f'{data_source}/{extension}')  # Use glob.glob to find all file paths in the data_source directory that match the specified extension (*.jsonl)

    print(f'Found {len(file_paths)} files in {data_source}')  # Print the number of files found in the data_source directory

    db = process_jsonl_files(file_paths, persist_path)

    print(f"db._LANGCHAIN_DEFAULT_COLLECTION_NAME: {db._LANGCHAIN_DEFAULT_COLLECTION_NAME}")  # Print the default collection name of the ChromaDB instance
    # Persist the database
    db = None  # Clear the database variable to free up resources
    # Print a message indicating the completion of the vectorization process

    print(f"[INFO] Vectorization complete. Database persisted at: {persist_path}")