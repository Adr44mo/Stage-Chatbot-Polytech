from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # Import the ChatPromptTemplate and MessagesPlaceholder classes

# Define the system prompt for contextualizing the question
contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""

# Create a ChatPromptTemplate for contextualizing the question
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),  # Set the system prompt
        MessagesPlaceholder("chat_history"),  # Placeholder for the chat history
        ("human", "{input}"),  # Placeholder for the user's input question
    ]
)

# Define the system prompt for the question-answering task
qa_system_prompt = """You are an assistant for question-answering tasks. \
Use the following pieces of retrieved context to answer the question. \
If you don't know the answer, just say that you don't know. \
Use three sentences maximum and keep the answer concise.\

{context}"""  # This placeholder will be replaced with the retrieved context

# Create a ChatPromptTemplate for the question-answering task
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),  # Set the system prompt
        MessagesPlaceholder("chat_history"),  # Placeholder for the chat history
        ("human", "{input}"),  # Placeholder for the user's input question
    ]
)