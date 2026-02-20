"""
config.py - Configuration centrale du projet CNAM Chatbot
"""
import os
from pathlib import Path
from dotenv import load_dotenv



# ── Chemins ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# ── Charger .env310 ───────────────────────────────────────
env_path = BASE_DIR / ".env310"
load_dotenv(dotenv_path=env_path, override=True)
DATA_DIR = BASE_DIR / "data"
RAW_PDFS_DIR = DATA_DIR / "raw_pdfs"
PROCESSED_DIR = DATA_DIR / "processed"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"

# Créer les dossiers si inexistants
for d in [RAW_PDFS_DIR, PROCESSED_DIR, VECTORSTORE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── LLM (Groq) ───────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Modèles Groq disponibles :
#   "llama-3.3-70b-versatile"  ← Meilleur (recommandé)
#   "llama-3.1-8b-instant"     ← Ultra rapide / léger
#   "mixtral-8x7b-32768"       ← Bon contexte long
#   "gemma2-9b-it"             ← Alternatif
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

# ── Embeddings ───────────────────────────────────────────────────────────────
# Groq ne fournit PAS d'embeddings → on utilise HuggingFace (gratuit)
# "huggingface" uniquement (recommandé)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "huggingface")
HF_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# ↑ Modèle multilingue : supporte arabe + français

# ── Chunking ─────────────────────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# ── Retrieval ────────────────────────────────────────────────────────────────
TOP_K_DOCS = int(os.getenv("TOP_K_DOCS", "5"))
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.3"))

# ── Web Search ───────────────────────────────────────────────────────────────
WEB_SEARCH_ENABLED = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"
WEB_SEARCH_MAX_RESULTS = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "3"))
CNAM_SITE_URL = "https://www.cnam.nat.tn"
CNAM_PS_PAGE = "https://www.cnam.nat.tn/espace_ps.jsp"

# ── FAISS ────────────────────────────────────────────────────────────────────
FAISS_INDEX_NAME = "cnam_faiss_index"

# ── Streamlit ────────────────────────────────────────────────────────────────
APP_TITLE = "🏥 Chatbot CNAM Tunisie"
APP_DESCRIPTION = "Assistant virtuel pour les assurés et professionnels de santé CNAM"