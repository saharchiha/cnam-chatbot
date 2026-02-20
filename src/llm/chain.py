"""
chain.py - Chaîne RAG principale : RAG (FAISS) + Web Search → LLM
"""
from loguru import logger
from langchain_groq import ChatGroq
from langchain.schema import Document
from langchain_community.vectorstores import FAISS

from src.utils.config import (
    GROQ_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    TOP_K_DOCS,
    SCORE_THRESHOLD,
)
from src.search.web_search import search_cnam_web, format_web_results
from src.retrieval.vectorstore import load_vectorstore, vectorstore_exists


# ── Prompt System CNAM ───────────────────────────────────────────────────────
SYSTEM_PROMPT = """Tu es un assistant virtuel officiel de la CNAM (Caisse Nationale d'Assurance Maladie) de Tunisie.
Tu aides les assurés et professionnels de santé à comprendre :
- Les remboursements de médicaments, consultations, analyses et radiologies
- Les médecins et cliniques conventionnés
- Les procédures administratives et formulaires
- Les droits et conditions de prise en charge
- Le Système de Soins Ambulatoires (SSA) et le Régime des Soins Libres (RSL)

RÈGLES IMPORTANTES :
1. Réponds TOUJOURS en français (sauf si la question est en arabe, alors réponds en arabe)
2. Base-toi PRIORITAIREMENT sur les documents officiels CNAM fournis dans le contexte
3. Ne cite JAMAIS les noms de fichiers internes (ex: Av4_xxx.pdf, _5cf0ed8d, document 1, document 2, etc.) - dis simplement "selon le barème officiel CNAM" ou "selon la réglementation CNAM"
4. Si une information vient du web, dis simplement "selon le site officiel cnam.nat.tn"
5. Si tu ne connais pas la réponse, dis-le clairement et oriente vers www.cnam.nat.tn ou le numéro vert
6. Sois précis sur les taux de remboursement et les procédures
7. Ne donne JAMAIS d'informations médicales (diagnostic, traitement) - uniquement administratives
8. Réponds UNIQUEMENT aux questions relatives à la CNAM Tunisie - pour tout autre sujet réponds : "Je suis uniquement dédié aux services CNAM Tunisie. Pour toute autre question, je ne suis pas en mesure de vous aider."

Numéro vert CNAM : 80 100 180
Site officiel : www.cnam.nat.tn
"""

USER_PROMPT_TEMPLATE = """CONTEXTE DOCUMENTS CNAM:
{rag_context}

{web_context}

QUESTION DE L'ASSURÉ:
{question}

Réponds de manière claire, précise et structurée. Si pertinent, indique les étapes à suivre."""


class CNAMChatbot:
    """
    Chatbot CNAM avec RAG + Web Search.
    """

    def __init__(self):
        self.vectorstore: FAISS | None = None
        self.llm = None
        self._initialize()

    def _initialize(self):
        """Initialise le LLM Groq et charge le vectorstore si disponible."""
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY manquant dans le fichier .env")

        self.llm = ChatGroq(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            groq_api_key=GROQ_API_KEY,
        )
        logger.info(f"LLM Groq initialisé : {LLM_MODEL}")

        # Vectorstore
        if vectorstore_exists():
            try:
                self.vectorstore = load_vectorstore()
            except Exception as e:
                logger.error(f"Impossible de charger le vectorstore: {e}")
        else:
            logger.warning(
                "Vectorstore non trouvé. Lancez : python scripts/ingest_all.py\n"
                "Le chatbot fonctionnera uniquement avec la recherche web."
            )

    def retrieve_from_rag(self, query: str) -> tuple[list[Document], str]:
        """
        Recherche les documents pertinents dans FAISS.
        Returns: (documents, contexte formaté)
        """
        if not self.vectorstore:
            return [], ""

        try:
            # Recherche par similarité avec score
            docs_with_scores = self.vectorstore.similarity_search_with_score(
                query, k=TOP_K_DOCS
            )
            # Filtrer par score de pertinence (distance L2 - plus petit = mieux)
            relevant_docs = [
                doc for doc, score in docs_with_scores
                if score <= (1 - SCORE_THRESHOLD)  # Convertir threshold
            ]
            if not relevant_docs:
                relevant_docs = [doc for doc, _ in docs_with_scores[:3]]

            # Formater le contexte
            context_parts = []
            for i, doc in enumerate(relevant_docs, 1):
                source = doc.metadata.get("source", "Document CNAM")
                doc_type = doc.metadata.get("doc_type", "general")
                context_parts.append(f"[Source officielle CNAM - {doc_type}]\n{doc.page_content}")

            context = "\n\n---\n\n".join(context_parts)
            logger.info(f"RAG: {len(relevant_docs)} documents pertinents trouvés")
            return relevant_docs, context

        except Exception as e:
            logger.error(f"Erreur RAG: {e}")
            return [], ""

    def ask(self, question: str, use_web_search: bool = True) -> dict:
        """
        Point d'entrée principal du chatbot.
        
        Args:
            question: Question de l'assuré
            use_web_search: Activer la recherche web complémentaire
            
        Returns:
            dict avec "answer", "sources_rag", "sources_web"
        """
        logger.info(f"Question reçue : {question[:80]}...")

        # 1. RAG - Recherche dans les PDFs
        rag_docs, rag_context = self.retrieve_from_rag(question)

        # 2. Web Search - Recherche en ligne
        web_results = []
        web_context = ""
        if use_web_search:
            web_results = search_cnam_web(question)
            if web_results:
                web_context = format_web_results(web_results)

        # 3. Construire le prompt
        if not rag_context and not web_context:
            rag_context = "Aucun document spécifique trouvé. Répondre avec les connaissances générales sur la CNAM Tunisie."

        user_message = USER_PROMPT_TEMPLATE.format(
            rag_context=rag_context or "Aucun document RAG disponible.",
            web_context=web_context,
            question=question,
        )

        # 4. Appel LLM
        from langchain.schema import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]

        try:
            response = self.llm.invoke(messages)
            answer = response.content
        except Exception as e:
            logger.error(f"Erreur LLM Groq: {e}")
            answer = (
                "Désolé, une erreur s'est produite. "
                "Vérifiez votre clé GROQ_API_KEY dans .env\n"
                "Contactez la CNAM au 80 100 180 ou visitez www.cnam.nat.tn"
            )

        # 5. Préparer les sources
        sources_rag = list({
            doc.metadata.get("source", "") for doc in rag_docs
            if doc.metadata.get("source")
        })
        sources_web = [
            {"title": r["title"], "url": r["url"]}
            for r in web_results
        ]

        result = {
            "answer": answer,
            "sources_rag": sources_rag,
            "sources_web": sources_web,
            "rag_docs_count": len(rag_docs),
            "web_results_count": len(web_results),
        }

        logger.success(f"Réponse générée ({len(answer)} chars)")
        return result


# Singleton pour éviter de recharger le modèle à chaque requête
_chatbot_instance: CNAMChatbot | None = None


def get_chatbot() -> CNAMChatbot:
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = CNAMChatbot()
    return _chatbot_instance