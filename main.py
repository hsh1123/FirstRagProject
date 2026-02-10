import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

retrieval_chain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG pipeline on server startup."""
    global retrieval_chain

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set in .env file.")

    # ChromaDB connection
    chroma_host = os.getenv("CHROMA_HOST", "localhost")
    chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
    chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", google_api_key=api_key
    )

    # Indexing
    print("--- Indexing ---")
    loader = TextLoader("dummy_document.txt", encoding="utf-8")
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)

    Chroma.from_documents(
        documents=texts, embedding=embeddings, client=chroma_client,
        collection_name="rag_collection"
    )

    # Retrieval chain setup
    vectordb = Chroma(
        client=chroma_client, embedding_function=embeddings,
        collection_name="rag_collection"
    )
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", google_api_key=api_key, temperature=0
    )

    prompt = ChatPromptTemplate.from_template(
        """Please answer the following question using the given context:

<context>
{context}
</context>

Question: {input}"""
    )

    document_chain = create_stuff_documents_chain(llm, prompt)
    retriever = vectordb.as_retriever()
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    print("--- RAG Ready ---")
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    response = retrieval_chain.invoke({"input": req.message})
    return ChatResponse(answer=response["answer"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
