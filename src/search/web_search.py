"""
web_search.py - Recherche web en temps réel sur le site CNAM et sources médicales tunisiennes
"""
from loguru import logger
from duckduckgo_search import DDGS
from src.utils.config import WEB_SEARCH_ENABLED, WEB_SEARCH_MAX_RESULTS, CNAM_SITE_URL


def search_cnam_web(query: str, max_results: int = WEB_SEARCH_MAX_RESULTS) -> list[dict]:
    """
    Recherche sur le site CNAM et sources tunisiennes de santé.
    Returns: liste de dicts {"title": ..., "url": ..., "snippet": ...}
    """
    if not WEB_SEARCH_ENABLED:
        return []

    results = []

    # Recherche ciblée sur le site CNAM
    cnam_query = f"site:cnam.nat.tn {query}"
    # Recherche élargie en tunisien/français
    general_query = f"{query} CNAM Tunisie assurance maladie remboursement"

    with DDGS() as ddgs:
        # 1. Cibler le site officiel
        try:
            for r in ddgs.text(cnam_query, max_results=max_results, region="tn-ar"):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                    "source": "cnam.nat.tn",
                })
        except Exception as e:
            logger.warning(f"Recherche CNAM site: failed - {e}")

        # 2. Si pas assez de résultats, élargir
        if len(results) < max_results:
            try:
                for r in ddgs.text(
                    general_query,
                    max_results=max_results - len(results),
                    region="tn-ar",
                ):
                    # Éviter les doublons
                    if r.get("href") not in {x["url"] for x in results}:
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "snippet": r.get("body", ""),
                            "source": "web",
                        })
            except Exception as e:
                logger.warning(f"Recherche web générale: failed - {e}")

    logger.info(f"Web search '{query[:50]}...' → {len(results)} résultats")
    return results[:max_results]


def format_web_results(results: list[dict]) -> str:
    """Formate les résultats web en texte pour le contexte LLM."""
    if not results:
        return ""
    parts = ["=== RÉSULTATS WEB ==="]
    for i, r in enumerate(results, 1):
        parts.append(
            f"\n[Source {i}] {r['title']}\n"
            f"URL: {r['url']}\n"
            f"{r['snippet']}"
        )
    return "\n".join(parts)