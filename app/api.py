"""
api.py - API REST FastAPI pour intégrer le chatbot CNAM dans d'autres applications
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
from src.llm.chain import get_chatbot

app = FastAPI(
    title="CNAM Tunisie Chatbot API",
    description="API du chatbot RAG pour la Caisse Nationale d'Assurance Maladie",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str
    use_web_search: bool = True


class AnswerResponse(BaseModel):
    answer: str
    sources_rag: list[str]
    sources_web: list[dict]
    rag_docs_count: int
    web_results_count: int


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "CNAM Chatbot API"}


@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    """Pose une question au chatbot CNAM."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide")
    if len(request.question) > 1000:
        raise HTTPException(status_code=400, detail="Question trop longue (max 1000 caractères)")

    try:
        chatbot = get_chatbot()
        result = chatbot.ask(request.question, use_web_search=request.use_web_search)
        return AnswerResponse(**result)
    except Exception as e:
        logger.error(f"Erreur API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)