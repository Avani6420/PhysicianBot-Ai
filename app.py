import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from config import UPLOAD_DIR
from rag_pipeline import (
    extract_text_from_pdf,
    chunk_documents,
    create_vector_store,
    generate_answer
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "RAG API Running"}

# Upload PDF
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(
        UPLOAD_DIR,
        file.filename
    )

    with open(file_path, "wb") as f:
        f.write(await file.read())

    docs = extract_text_from_pdf(file_path)
    chunks = chunk_documents(docs)
    create_vector_store(chunks)

    return {
        "message": "PDF uploaded and indexed successfully"
    }

# Ask Question
@app.post("/ask")
def ask_question(query: str):
    result = generate_answer(query)
    return result