# 🏥 Chatbot RAG — CNAM Tunisie

Assistant intelligent basé sur la **Retrieval-Augmented Generation (RAG)** pour répondre aux questions des assurés de la **Caisse Nationale d'Assurance Maladie** de Tunisie, en français et en arabe.

---

## ✨ Fonctionnalités

- 🔍 **RAG** — Recherche dans les documents officiels CNAM (PDFs)
- 🌐 **Web Search** — Complément via DuckDuckGo si les PDFs ne suffisent pas
- 💬 **Interface Streamlit** — Chat interactif bilingue (FR / AR)
- ⚡ **API REST FastAPI** — Intégration dans d'autres applications
- 🧠 **LLM Groq** — Inférence rapide (lama-3.3-70b-versatile)
- 📦 **VectorStore FAISS** — Recherche sémantique locale

---

## 📁 Structure du projet

```
cnam-chatbot/
├── app/
│   ├── streamlit_app.py        # Interface utilisateur Streamlit
│   └── api.py                  # API REST FastAPI
├── scripts/
│   └── ingest_all.py           # Pipeline d'ingestion (scraping → vectorstore)
├── src/
│   ├── ingestion/
│   │   ├── scraper.py          # Scraping PDFs depuis cnam.nat.tn
│   │   └── pdf_processor.py    # Extraction et chunking du texte
│   ├── retrieval/
│   │   └── vectorstore.py      # Construction et requête FAISS
│   ├── llm/
│   │   └── chain.py            # Chaîne RAG LangChain + Groq
│   ├── search/
│   │   └── web_search.py       # Recherche web DuckDuckGo
│   └── utils/
│       └── config.py           # Configuration et chemins
├── data/
│   ├── raw_pdfs/               # PDFs téléchargés depuis CNAM
│   ├── processed/              # Chunks JSON extraits
│   └── vectorstore/
│       ├── index.faiss         # Index FAISS
│       └── index.pkl           # Métadonnées
├── logo_cnam.jpg
├── requirements.txt
├── .env                        # Variables d'environnement (non versionné)
└── README.md
```

---

## ⚙️ Installation

### 1. Cloner le repo

```bash
git clone https://github.com/TON_USERNAME/cnam-chatbot.git
cd cnam-chatbot
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

Crée un fichier `.env` à la racine :

```env
GROQ_API_KEY=your_groq_api_key_here
```

> Obtiens une clé gratuite sur [console.groq.com](https://console.groq.com)

---

## 🚀 Utilisation

### Étape 1 — Ingestion des documents (une seule fois)

```bash
python scripts/ingest_all.py
```

Options disponibles :

```bash
python scripts/ingest_all.py --force-rescrape    # Re-télécharger les PDFs
python scripts/ingest_all.py --force-reprocess   # Ré-extraire le texte
python scripts/ingest_all.py --force-rebuild     # Reconstruire le VectorStore
python scripts/ingest_all.py --full-rebuild      # Tout reconstruire
```

### Étape 2 — Lancer l'interface Streamlit

```bash
streamlit run app/streamlit_app.py
```

### Étape 3 (optionnel) — Lancer l'API FastAPI

```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

Documentation interactive : [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔌 API REST

### Health check

```http
GET /health
```

### Poser une question

```http
POST /ask
Content-Type: application/json

{
  "question": "Comment se faire rembourser un médicament ?",
  "use_web_search": true
}
```

**Réponse :**

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

## 🛠️ Stack technique

| Composant | Technologie |
|-----------|-------------|
| LLM | Groq (lama-3.3-70b-versatile) |
| Orchestration | LangChain |
| Embeddings | HuggingFace Sentence Transformers |
| Vector Store | FAISS |
| Web Search | DuckDuckGo Search |
| PDF Processing | PyMuPDF, pdfplumber |
| Interface | Streamlit |
| API | FastAPI + Uvicorn |

---

## 📞 Contact CNAM

- **Numéro vert** : 80 100 180
- **Site officiel** : [cnam.nat.tn](https://www.cnam.nat.tn)
- **Email** : contact@cnam.nat.tn

---

## 👤 Auteur

**Sahar Chiha**

---

## ⚠️ Avertissement

Cet assistant fournit des informations générales basées sur les documents officiels CNAM. Pour des situations spécifiques, contactez directement la CNAM au **80 100 180**.
