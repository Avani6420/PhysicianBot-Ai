import os
import sys
import time
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
try:
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain.chains import create_retrieval_chain
except ImportError:
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain
    from langchain_classic.chains import create_retrieval_chain

from src.helper import download_hugging_face_embeddings
from src.prompt import system_prompt
from src.logger import logger
from src.exception import MedicalBotException

# Load environment variables
load_dotenv()

# Normalize environment keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") or os.getenv("pinecone")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("Groq_API_KEY")

if not PINECONE_API_KEY:
    logger.critical("PINECONE_API_KEY or 'pinecone' key missing from .env file.")
    raise ValueError("PINECONE_API_KEY or 'pinecone' key not found in .env file.")
if not GROQ_API_KEY:
    logger.critical("GROQ_API_KEY or 'Groq_API_KEY' missing from .env file.")
    raise ValueError("GROQ_API_KEY or 'Groq_API_KEY' not found in .env file.")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

INDEX_NAME = "medical-chatbot"
MODEL_NAME = "Groq (Qwen 3.8-27B)"

app = Flask(__name__)

# Global RAG chain container
rag_chain = None


def init_rag_system():
    global rag_chain
    logger.info("Initializing Medical RAG System...")
    try:
        logger.info("Loading Hugging Face embeddings...")
        embeddings = download_hugging_face_embeddings()

        logger.info(f"Connecting to Pinecone index: '{INDEX_NAME}'...")
        vectorstore = PineconeVectorStore.from_existing_index(
            index_name=INDEX_NAME,
            embedding=embeddings
        )
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )

        logger.info(f"Initializing Groq LLM ({MODEL_NAME})...")
        llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="qwen/qwen3.8-27b",
            temperature=0.3,
            max_tokens=600
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)
        logger.info("Medical RAG Pipeline initialized successfully and ready to serve queries.")
    except Exception as e:
        logger.error(f"Failed to initialize RAG pipeline: {str(e)}")
        raise MedicalBotException(e, sys)


@app.route("/")
def index():
    logger.info("Serving chat interface homepage.")
    return render_template("chat.html")


@app.route("/get", methods=["GET", "POST"])
def chat():
    """
    Primary endpoint supporting both AJAX JSON queries and form data submissions.
    """
    global rag_chain
    start_time = time.time()

    if request.is_json:
        user_input = request.json.get("msg", "").strip()
    else:
        user_input = request.form.get("msg", "").strip()

    if not user_input:
        logger.warning("Empty message received on /get endpoint.")
        return jsonify({"error": "Empty message received."}), 400

    if rag_chain is None:
        logger.error("Query received before RAG pipeline was initialized.")
        return jsonify({"error": "Medical assistant is currently initializing. Please try again shortly."}), 503

    logger.info(f"Received user query: '{user_input[:80]}...' (length: {len(user_input)})")

    try:
        response = rag_chain.invoke({"input": user_input})
        answer = response.get("answer", "I could not locate sufficient medical literature to answer this inquiry.")

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"Query answered successfully in {elapsed}s.")

        return jsonify({
            "answer": answer,
            "response_time": elapsed
        })
    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        logger.error(f"Error during RAG inference after {elapsed}s: {str(e)}")
        exc = MedicalBotException(e, sys)
        return jsonify({"error": "An error occurred while analyzing the clinical literature. Please try again."}), 500


@app.route("/api/status", methods=["GET"])
def status():
    """
    Health check endpoint for service monitoring.
    """
    is_ready = rag_chain is not None
    return jsonify({
        "status": "online" if is_ready else "initializing",
        "service": "MediBot AI Assistant",
        "rag_ready": is_ready
    })


@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 Not Found: {request.url}")
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Internal Server Error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    try:
        init_rag_system()
        logger.info("Starting Flask application on http://127.0.0.1:5000 ...")
        app.run(host="127.0.0.1", port=5000, debug=False)
    except Exception as e:
        logger.critical(f"Application failed to start: {str(e)}")
