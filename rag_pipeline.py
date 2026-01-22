import os
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables from .env file
load_dotenv()

def main():
    # Set Google API Key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "YOUR_GOOGLE_API_KEY":
        print("Error: GOOGLE_API_KEY is not set in the .env file.")
        return

    # --- 1. Indexing ---
    print("--- 1. Starting Indexing ---")

    # Load documents
    # To use PDF, uncomment the line below and modify the file path.
    # loader = PyPDFLoader("sample.pdf")
    # Using a text file.
    loader = TextLoader("dummy_document.txt", encoding="utf-8")
    documents = loader.load()
    print("Documents loaded.")

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    print("Documents split into chunks.")

    # Create embeddings model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
    print("Embedding model created.")

    # Store documents in Chroma vector DB
    # By specifying persist_directory, vector data can be saved to disk and reloaded later.
    vectordb = Chroma.from_documents(documents=texts, embedding=embeddings, persist_directory="./chroma_db")
    vectordb.persist()
    print("Stored in vector database.")
    print("--- Indexing Complete ---")
    print()

    # --- 2. Retrieval & 3. Generation ---
    print("--- 2&3. Starting Retrieval and Generation Setup ---")

    # Load the Chroma database from disk
    vectordb = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

    # Create LLM model
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=api_key, temperature=0, convert_system_message_to_human=True)

    # Create a prompt
    prompt = ChatPromptTemplate.from_template("""Please answer the following question using the given context:

<context>
{context}
</context>

Question: {input}""")

    # Create 'stuff' documents chain
    document_chain = create_stuff_documents_chain(llm, prompt)

    # Create a retriever
    retriever = vectordb.as_retriever()

    # Create the retrieval chain
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    print("--- RAG Setup Complete ---")
    print()
    print("You can now ask questions. Type 'exit' to quit.")
    print()

    # User question loop
    while True:
        try:
            query = input("Question: ")
            if query.lower() == 'exit':
                print("Exiting the program.")
                break
            if not query.strip():
                continue

            # Execute the question and get the answer
            response = retrieval_chain.invoke({"input": query})
            print("Answer:", response["answer"])
            print("-" * 20)
        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    main()