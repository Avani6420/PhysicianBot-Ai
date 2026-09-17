import os
import sys
import argparse
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from src.helper import load_pdf_file, text_split, download_hugging_face_embeddings
from src.logger import logger
from src.exception import MedicalBotException

# Load environment variables
load_dotenv()

# Normalize environment keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") or os.getenv("pinecone")

if not PINECONE_API_KEY:
    logger.error("PINECONE_API_KEY not found in environment or .env file.")
    raise ValueError("PINECONE_API_KEY or 'pinecone' key not found in .env file.")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

INDEX_NAME = "medical-chatbot"


def initialize_pinecone_index(index_name: str = INDEX_NAME, dimension: int = 384):
    """
    Initializes Pinecone client and creates index if it doesn't already exist.
    """
    try:
        masked_key = f"{PINECONE_API_KEY[:8]}...****" if len(PINECONE_API_KEY) > 8 else "****"
        logger.info(f"Connecting to Pinecone with API key: {masked_key}")
        pc = Pinecone(api_key=PINECONE_API_KEY)

        existing_indexes = [index.name for index in pc.list_indexes()]
        logger.info(f"Existing Pinecone indexes: {existing_indexes}")

        if index_name not in existing_indexes:
            logger.info(f"Creating Serverless Pinecone index: '{index_name}' (dim={dimension}, metric='cosine')...")
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            logger.info(f"Index '{index_name}' created successfully!")
        else:
            logger.info(f"Index '{index_name}' already exists. Re-using existing index.")

        return pc.Index(index_name)
    except Exception as e:
        logger.error(f"Error initializing Pinecone index '{index_name}': {str(e)}")
        raise MedicalBotException(e, sys)


def main():
    parser = argparse.ArgumentParser(description="Ingest Medical Book PDF into Pinecone Vector Database")
    parser.add_argument("--data-path", type=str, default="dataset/Medical_book.pdf", help="Path to PDF file or directory")
    parser.add_argument("--max-pages", type=int, default=50, help="Maximum pages to ingest (0 for all pages)")
    parser.add_argument("--chunk-size", type=int, default=500, help="Chunk size for text splitter")
    parser.add_argument("--chunk-overlap", type=int, default=20, help="Chunk overlap for text splitter")
    args = parser.parse_args()

    try:
        # Step 1: Initialize Pinecone index
        logger.info("Initializing Pinecone vector store setup...")
        initialize_pinecone_index(INDEX_NAME)

        # Step 2: Load PDF
        logger.info(f"Loading PDF documents from: {args.data_path}")
        if not os.path.exists(args.data_path):
            raise FileNotFoundError(f"Path '{args.data_path}' does not exist.")

        extracted_data = load_pdf_file(args.data_path)
        total_pages = len(extracted_data)
        logger.info(f"Extracted {total_pages} total pages from document.")

        if args.max_pages > 0 and total_pages > args.max_pages:
            logger.info(f"Subsetting to first {args.max_pages} pages for fast indexing.")
            extracted_data = extracted_data[:args.max_pages]

        # Step 3: Chunk Documents
        logger.info(f"Splitting documents into chunks (size={args.chunk_size}, overlap={args.chunk_overlap})...")
        text_chunks = text_split(extracted_data, chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
        logger.info(f"Generated {len(text_chunks)} text chunks.")

        # Step 4: Download Embeddings
        logger.info("Initializing Hugging Face embedding model...")
        embeddings = download_hugging_face_embeddings()

        # Step 5: Upsert to Pinecone
        logger.info(f"Upserting {len(text_chunks)} chunks to Pinecone index '{INDEX_NAME}'...")
        batch_size = 100
        for i in range(0, len(text_chunks), batch_size):
            batch = text_chunks[i:i + batch_size]
            logger.info(f"Upserting batch {i // batch_size + 1}/{(len(text_chunks) + batch_size - 1) // batch_size} ({len(batch)} chunks)...")
            PineconeVectorStore.from_documents(
                documents=batch,
                embedding=embeddings,
                index_name=INDEX_NAME
            )

        logger.info("Vector ingestion completed successfully! Index is ready for querying.")
    except Exception as e:
        logger.error("Failed during vector ingestion workflow.")
        raise MedicalBotException(e, sys)


if __name__ == "__main__":
    main()
