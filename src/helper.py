import os
import sys
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.logger import logger
from src.exception import MedicalBotException


def load_pdf_file(data_path: str):
    """
    Extracts text from PDF documents in the given directory or file path.
    """
    logger.info(f"Starting PDF document loading from: {data_path}")
    try:
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Provided path does not exist: {data_path}")

        if os.path.isfile(data_path):
            logger.info(f"Loading single PDF file: {data_path}")
            loader = PyPDFLoader(data_path)
            documents = loader.load()
        else:
            logger.info(f"Loading PDF documents from directory: {data_path}")
            loader = DirectoryLoader(
                data_path,
                glob="*.pdf",
                loader_cls=PyPDFLoader
            )
            documents = loader.load()

        logger.info(f"Successfully loaded {len(documents)} document pages from {data_path}")
        return documents
    except Exception as e:
        logger.error(f"Failed to load PDF file from {data_path}")
        raise MedicalBotException(e, sys)


def text_split(extracted_data, chunk_size: int = 500, chunk_overlap: int = 50):
    """
    Splits loaded documents into smaller overlapping text chunks.
    """
    logger.info(f"Splitting {len(extracted_data)} documents (chunk_size={chunk_size}, chunk_overlap={chunk_overlap})...")
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        text_chunks = text_splitter.split_documents(extracted_data)
        logger.info(f"Document splitting completed: Created {len(text_chunks)} text chunks.")
        return text_chunks
    except Exception as e:
        logger.error("Error occurred during document splitting.")
        raise MedicalBotException(e, sys)


def download_hugging_face_embeddings(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """
    Initializes embeddings for 384-dimensional dense vectors.
    If HUGGINGFACEHUB_API_TOKEN or HF_TOKEN is configured in the environment,
    uses Hugging Face Inference API (zero local RAM overhead, ideal for Render free tier 512MB).
    Otherwise, falls back to local HuggingFaceEmbeddings if PyTorch / sentence-transformers is installed.
    """
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")

    if hf_token:
        logger.info(f"Using Hugging Face Inference Endpoint for '{model_name}' (low memory mode).")
        try:
            from langchain_huggingface import HuggingFaceEndpointEmbeddings
            embeddings = HuggingFaceEndpointEmbeddings(
                model=model_name,
                huggingfacehub_api_token=hf_token
            )
            logger.info("HuggingFace Endpoint embeddings initialized successfully.")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to initialize Hugging Face Endpoint embeddings: {str(e)}")
            raise MedicalBotException(e, sys)

    logger.info(f"HUGGINGFACEHUB_API_TOKEN not detected. Attempting local Hugging Face embeddings for '{model_name}'...")
    try:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"}
        )
        logger.info(f"Local embedding model '{model_name}' successfully loaded.")
        return embeddings
    except Exception as e:
        err_msg = (
            f"Failed to load local embedding model '{model_name}': {str(e)}. "
            "If deploying to Render (512MB RAM limit), set the HUGGINGFACEHUB_API_TOKEN environment variable "
            "in the Render dashboard to use the cloud inference API instead of local PyTorch."
        )
        logger.error(err_msg)
        raise MedicalBotException(err_msg, sys)
