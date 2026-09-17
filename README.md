# MediBot AI — Medical RAG Chatbot

An intelligent medical assistant web application built with **Flask**, **LangChain**, **HuggingFace Embeddings**, **Pinecone Vector Database**, and **Groq LLM**. It utilizes **Retrieval-Augmented Generation (RAG)** to provide grounded clinical answers directly from medical textbook literature with transparent source citations.

---

## 🌟 Key Features

- **Document Ingestion & Chunking**: Extracts and splits medical textbooks (`.pdf`) into semantically rich chunks using LangChain's `PyPDFLoader` and `RecursiveCharacterTextSplitter`.
- **Dense Vector Embeddings**: Generates 384-dimensional embeddings locally using HuggingFace's `sentence-transformers/all-MiniLM-L6-v2`.
- **Pinecone Vector Store**: Stores dense vectors in a serverless Pinecone index (`medical-chatbot`) for low-latency cosine similarity search.
- **Groq LLM Reasoning**: Powers high-speed clinical responses with `qwen/qwen3.8-27b` via Groq's high-throughput inference engine.
- **Grounded Clinical Answers**: Strictly grounds responses in retrieved context to avoid hallucinations and provides automatic medical safety disclaimers.
- **Source Citations**: Displays referenced pages and book excerpts for clinical verification.
- **Modern Glassmorphic Web UI**: Dark-mode interface with live system status indicators, starter inquiry chips, and animated typing feedback.

---

## 🏛️ System Architecture

```
[ dataset/Medical_book.pdf ]
            │
            ▼ (LangChain PyPDFLoader)
    [ Document Chunks ]
            │
            ▼ (HuggingFace sentence-transformers/all-MiniLM-L6-v2)
   [ 384-dim Dense Vectors ]
            │
            ▼ (store_index.py)
   [ Pinecone Vector Store ] (Index: medical-chatbot)
            │
            ▲ (Cosine Similarity Search)
            │
[ User Query via Flask UI ] ──► [ LangChain Retrieval Chain ] ──► [ Groq LLM (Qwen 3.8-27B) ] ──► [ Structured Answer + Citations ]
```

---

## 📁 Project Structure

```
medical_chatboats/
├── dataset/
│   └── Medical_book.pdf           # Medical reference textbook
├── logs/                          # Daily timestamped application log files
├── src/
│   ├── __init__.py                # Package exports (logger, MedicalBotException)
│   ├── logger.py                  # Dual-stream rotating logging engine
│   ├── exception.py               # Custom exception handler with traceback extraction
│   ├── helper.py                  # PDF loader, text chunker, HuggingFace embeddings
│   └── prompt.py                  # Clinical prompt template with safety rules
├── static/
│   ├── css/
│   │   └── style.css              # Glassmorphic dark-mode clinical UI styling
│   └── js/
│       └── script.js              # Interactive chat logic, citations toggle, API calls
├── templates/
│   └── chat.html                  # Realistic medical assistant chat interface
├── .env                           # Environment keys (PINECONE_API_KEY, GROQ_API_KEY)
├── app.py                         # Flask web application & RAG query API
├── store_index.py                 # Pinecone index creation and vector ingestion script
├── test_rag.py                    # Verification script for end-to-end RAG pipeline
├── requirements.txt               # Pinned project dependencies
├── setup.py                       # Python setup configuration
└── README.md                      # Project documentation
```

---

## ⚙️ Prerequisites & Setup

### 1. Clone or Open Project
```powershell
cd d:\LLM_project\medical_chatboats
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create or edit your `.env` file in the project root:
```env
PINECONE_API_KEY="your-pinecone-api-key"
GROQ_API_KEY="your-groq-api-key"
```
> **Tip:** You can obtain a free Pinecone key at [app.pinecone.io](https://app.pinecone.io) and a free Groq key at [console.groq.com](https://console.groq.com).

---

## 🚀 How to Run

### Step 1: Ingest Data into Pinecone Vector Database
Process your medical PDF and populate the Pinecone index:
```powershell
# Ingest first 50 pages (fast indexing for testing)
python store_index.py --max-pages 50

# Ingest all pages from the medical book
python store_index.py --max-pages 0
```

### Step 2: Start the Flask Application
Run the Flask server:
```powershell
python app.py
```

### Step 3: Open the Web Chatbot
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Renders the web chat interface. |
| `/get` | `POST` | Primary RAG endpoint. Accepts JSON `{"msg": "query"}` or form data. Returns `{ "answer": "...", "sources": [...] }`. |
| `/api/status` | `GET` | Health check endpoint returning status, active index, and model. |

---

## 📋 Technology Stack

- **Framework**: Flask 3.x
- **LLM Orchestration**: LangChain, LangChain-Groq, LangChain-Pinecone
- **LLM Model**: Groq `qwen/qwen3.8-27b`
- **Embeddings**: HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Vector Database**: Pinecone (Serverless)
- **PDF Extraction**: `pypdf`
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism), JavaScript (Fetch API)

---

## ⚠️ Medical Disclaimer

*This application is strictly for educational, informational, and research purposes. It is not intended to serve as professional medical advice, clinical diagnosis, or a treatment plan. Always seek the advice of a qualified physician or healthcare provider with any medical questions or emergencies.*
