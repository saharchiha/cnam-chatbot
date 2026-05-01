# 🏥 RAG Chatbot — CNAM Tunisia

An intelligent assistant based on **Retrieval-Augmented Generation (RAG)** to answer questions from insured members of the **Caisse Nationale d'Assurance Maladie** (National Health Insurance Fund) of Tunisia, in French and Arabic.

---

## ✨ Features

- 🔍 **RAG** — Semantic search over official CNAM documents (PDFs)
- 🌐 **Web Search** — DuckDuckGo fallback when PDFs are insufficient
- 💬 **Streamlit Interface** — Bilingual interactive chat (FR / AR)
- ⚡ **REST API (FastAPI)** — Easy integration into other applications
- 🧠 **Groq LLM** — Fast inference with `lama-3.3-70b-versatile`
- 📦 **FAISS VectorStore** — Local semantic search index

---

## 📁 Project Structure

```
cnam-chatbot/
├── app/
│   ├── streamlit_app.py        # Streamlit user interface
│   └── api.py                  # FastAPI REST API
├── scripts/
│   └── ingest_all.py           # Ingestion pipeline (scraping → vectorstore)
├── src/
│   ├── ingestion/
│   │   ├── scraper.py          # PDF scraping from cnam.nat.tn
│   │   └── pdf_processor.py    # Text extraction and chunking
│   ├── retrieval/
│   │   └── vectorstore.py      # FAISS index build and query
│   ├── llm/
│   │   └── chain.py            # RAG chain with LangChain + Groq
│   ├── search/
│   │   └── web_search.py       # DuckDuckGo web search
│   └── utils/
│       └── config.py           # Configuration and paths
├── data/
│   ├── raw_pdfs/               # PDFs downloaded from CNAM
│   ├── processed/              # Extracted JSON chunks
│   └── vectorstore/
│       ├── index.faiss         # FAISS index
│       └── index.pkl           # Metadata
├── logo_cnam.jpg
├── requirements.txt
├── .env                        # Environment variables (not versioned)
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/saharchiha/cnam-chatbot.git
cd cnam-chatbot
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file at the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> Get a free API key at [console.groq.com](https://console.groq.com)

---

## 🚀 Usage

### Step 1 — Ingest documents (run once)

```bash
python scripts/ingest_all.py
```

Available options:

```bash
python scripts/ingest_all.py --force-rescrape    # Re-download PDFs
python scripts/ingest_all.py --force-reprocess   # Re-extract text
python scripts/ingest_all.py --force-rebuild     # Rebuild the VectorStore
python scripts/ingest_all.py --full-rebuild      # Rebuild everything
```

### Step 2 — Launch the Streamlit interface

```bash
streamlit run app/streamlit_app.py
```

### Step 3 (optional) — Launch the FastAPI server

```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔌 REST API

### Health check

```http
GET /health
```

### Ask a question

```http
POST /ask
Content-Type: application/json

{
  "question": "How do I get reimbursed for a medication?",
  "use_web_search": true
}
```

**Response:**

```json
{
  "answer": "...",
  "sources_rag": ["document1.pdf"],
  "sources_web": [{"title": "...", "url": "..."}],
  "rag_docs_count": 3,
  "web_results_count": 2
}
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Groq (lama-3.3-70b-versatile) |
| Orchestration | LangChain |
| Embeddings | HuggingFace Sentence Transformers |
| Vector Store | FAISS |
| Web Search | DuckDuckGo Search |
| PDF Processing | PyMuPDF, pdfplumber |
| Interface | Streamlit |
| API | FastAPI + Uvicorn |

---

## 📞 CNAM Contact

- **Helpline** : 80 100 180
- **Official website** : [cnam.nat.tn](https://www.cnam.nat.tn)
- **Email** : contact@cnam.nat.tn

---

## 👤 Author

**Sahar Chiha**

---

## ⚠️ Disclaimer

This assistant provides general information based on official CNAM documents. For specific situations, please contact CNAM directly at **80 100 180**.
