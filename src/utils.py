from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import configs


def create_embeddings():

    loader_examples = PyPDFLoader("/Users/amaliaseydou/Desktop/RAG_MAIN5/corpusv1/intranet/charte_bons_comportements.pdf")
    docs_examples = loader_examples.load()

    
    loader_products = PyPDFLoader("/Users/amaliaseydou/Desktop/RAG_MAIN5/corpusv1/intranet/reglement_des_etudes.pdf")
    docs_products = loader_products.load()

    
    loader_prospects = PyPDFLoader("/Users/amaliaseydou/Desktop/RAG_MAIN5/corpusv1/intranet/tutoriel_stages.pdf")
    docs_prospects = loader_prospects.load()

    
    docs = docs_examples + docs_products + docs_prospects

    text_splitter = RecursiveCharacterTextSplitter()
    documents = text_splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(openai_api_key=configs.OPENAI_API_KEY)
    vector = FAISS.from_documents(documents, embeddings)

    vector.save_local("faiss_index")

