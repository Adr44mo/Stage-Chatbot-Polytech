# Passing a Chroma Client into Langchain
import chromadb  # Import the chromadb module

# chroma db
from langchain_chroma import Chroma  # Import the Chroma class from the langchain_chroma module for creating and managing a vector database

# embeddings client
from langchain_openai import OpenAIEmbeddings  # Import the OpenAIEmbeddings class from the langchain_openai module for generating text embeddings using OpenAI's language model
from langchain_openai import ChatOpenAI  # Import the ChatOpenAI class from the langchain_openai module
from langchain.chains import create_history_aware_retriever  # Import the create_history_aware_retriever function

# Chain with chat history
from langchain.chains import create_retrieval_chain  # Import the create_retrieval_chain function from the langchain.chains module
from langchain.chains.combine_documents import create_stuff_documents_chain  # Import the create_stuff_documents_chain function from the langchain.chains.combine_documents module

from pathlib import Path
import sys
# Add the directory containing promptt.py to the Python path
# This assumes promptt.py is in the same directory as this file
sys.path.append(str(Path(__file__).parent))
from .promptt import qa_prompt  # Import the qa_prompt from the prompt module
from .promptt import contextualize_q_prompt  # Import the contextualize_q_prompt from the prompt module

# Vector de Polytech Sorbonne
#persist_directory = Path(__file__).parent.parent.parent / "vectorisation" / "src" / "db"  # Define the directory where the Chroma vector database will be persisted

persist_directory = Path(__file__).parent.parent.parent.parent / "Document_handler" / "Vectorisation" / "vectorstore"  # Define the directory where the Chroma vector database will be persisted

print(f"[INFO] Using persist directory: {persist_directory}")  # Print the persist directory being used

embeddings = OpenAIEmbeddings()  # Create an instance of the OpenAIEmbeddings class (ensure to pass your OpenAI API key as an environment variable named 'OPENAI_API_KEY')


persistent_client = chromadb.PersistentClient(
                        path=str(persist_directory)
                    )  # Create a PersistentClient instance from the chromadb module, specifying the path where the data will be persisted

LANGCHAIN_DEFAULT_COLLECTION_NAME = 'langchain'  # Define the default collection name for the Chroma vector database
collection = persistent_client.get_or_create_collection(LANGCHAIN_DEFAULT_COLLECTION_NAME)  # Get or create a collection with the default name using the PersistentClient instance


# gets the chroma client for data retrieval
db = Chroma(
    client=persistent_client,  # Pass the persistent_client instance created earlier
    collection_name=LANGCHAIN_DEFAULT_COLLECTION_NAME,  # Use the default collection name defined earlier
    embedding_function=embeddings,  # Pass the embeddings instance for generating text embeddings
)
# Print information about the Chroma collection
print(f"[INFO] ChromaDB collection Name: {db._LANGCHAIN_DEFAULT_COLLECTION_NAME}, with collection count {db._collection.count()}")

# intiate the model
llm = ChatOpenAI(model="gpt-4o-mini",
    temperature=0.7)  # Create an instance of the ChatOpenAI class with the specified model name "gpt-4o-mini"

# initiate the db as retriever
retriever = db.as_retriever(
    search_type="similarity",  # Specify the search type as "similarity" for vector similarity search
    search_kwargs={"k": 5}  # Set the number of top results to retrieve (k=3)
)

# Create a history-aware retriever
history_aware_retriever = create_history_aware_retriever(
    llm,  # Pass the language model instance
    retriever,  # Pass the retriever instance
    contextualize_q_prompt  # Pass the prompt for contextualizing the question
)


def initialize_the_rag_chain():
    """
    Initialize the Retrieval-Augmented Generation (RAG) chain.
    
    Returns:
        rag_chain: The RAG chain for question-answering tasks.
    """
    # Create a chain for question-answering using the language model and the question-answering prompt
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # Create a Retrieval-Augmented Generation (RAG) chain
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return rag_chain

def initialize_chroma():
    """Initialize ChromaDB client and collection"""
    persistent_client = chromadb.PersistentClient(path=str(persist_directory))
    return Chroma(
        client=persistent_client,
        collection_name='langchain',
        embedding_function=OpenAIEmbeddings()
    )

def create_rag_chain(db):
    """Create RAG chain with source handling"""
    retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )

    history_aware_retriever = create_history_aware_retriever(
        ChatOpenAI(model="gpt-4o-mini"),
        retriever,
        contextualize_q_prompt
    )

    question_answer_chain = create_stuff_documents_chain(
        ChatOpenAI(model="gpt-4o-mini"),
        qa_prompt
    )

    return create_retrieval_chain(history_aware_retriever, question_answer_chain)
#####################################################################################################
# This script sets up a Retrieval-Augmented Generation (RAG) system using Langchain and ChromaDB.   #
# The __name__ == "__main__" is used uniquely for the test purpose of the SecondSol project.        #
#####################################################################################################

if __name__ == "__main__":
    # Get the default collection from the persistent client
    # LANGCHAIN_DEFAULT_COLLECTION_NAME is a constant representing the name of the default collection
    persistent_collection = persistent_client.get_collection(LANGCHAIN_DEFAULT_COLLECTION_NAME)

    # Create a chain for question-answering using the language model and the question-answering prompt
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # Create a Retrieval-Augmented Generation (RAG) chain
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    from langchain_core.messages import HumanMessage  # Import the HumanMessage class

    chat_history = []  # Initialize an empty list to store the chat history

    # Ask the first question
    first_question = "What is MAIN?"
    ai_response_1 = rag_chain.invoke({"input": first_question, "chat_history": chat_history})  # Invoke the RAG chain with the question and an empty chat history
    print('user query:', first_question) 
    print('ai response:', ai_response_1["answer"])  # Print the answer from the RAG chain
    chat_history.extend([HumanMessage(content=first_question), ai_response_1["answer"]])  # Add the question and answer to the chat history

    # Ask the second question
    second_question = "What are the courses in it?"
    ai_response_2 = rag_chain.invoke({"input": second_question, "chat_history": chat_history})  # Invoke the RAG chain with the second question and the updated chat history
    chat_history.extend([HumanMessage(content=second_question), ai_response_2["answer"]])  # Add the second question and answer to the chat history
    print('user query:', (second_question)) 
    print('ai response:', ai_response_2["answer"])   # Print the answer to the second question

    # Ask the third question
    third_question = "Can you translate your previous response to French?"
    ai_response_3 = rag_chain.invoke({"input": third_question, "chat_history": chat_history})  # Invoke the RAG chain with the third question and the updated chat history
    print('user query:', (third_question)) 
    print('ai response:', ai_response_3["answer"])   # Print the answer from the RAG chain
    chat_history.extend([HumanMessage(content=third_question), ai_response_3["answer"]])  # Add the third question and answer to the chat history

    # Pour accéder au contexte utilisé (c'est déjà formaté comme une chaîne)
    print('\nContexte utilisé pour la réponse:')
    print(ai_response_3["context"])
