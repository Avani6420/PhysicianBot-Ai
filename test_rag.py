import os
from dotenv import load_dotenv
load_dotenv()

from src.helper import download_hugging_face_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

try:
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain.chains import create_retrieval_chain
except ImportError:
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain
    from langchain_classic.chains import create_retrieval_chain

from src.prompt import system_prompt

groq_key = os.getenv("GROQ_API_KEY") or os.getenv("Groq_API_KEY")
if not groq_key:
    raise ValueError("GROQ_API_KEY not found in .env")

print("[1] Loading Hugging Face Embeddings...")
embeddings = download_hugging_face_embeddings()

print("[2] Connecting to Pinecone...")
vectorstore = PineconeVectorStore.from_existing_index("medical-chatbot", embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

print("[3] Initializing Groq Chat Model (qwen/qwen3.8-27b)...")
llm = ChatGroq(groq_api_key=groq_key, model_name="qwen/qwen3.8-27b", temperature=0.3)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

query = "What is abdominal pain and what causes it?"
print(f"\n[4] Querying RAG Chain with: '{query}'...")
response = rag_chain.invoke({"input": query})

print("\n--- RAG Answer ---")
print(response.get("answer"))

print("\n--- Sources Retrieved ---")
for i, doc in enumerate(response.get("context", [])):
    print(f"[{i+1}] Source: {doc.metadata.get('source')} | Page: {doc.metadata.get('page')}")
    print(f"    Excerpt: {doc.page_content[:120]}...\n")
