"""
ingest_all.py - Pipeline complet d'ingestion : Scraping → Extraction → Vectorstore
Lance ce script UNE SEULE FOIS (ou quand les PDFs changent).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from src.utils.config import RAW_PDFS_DIR, PROCESSED_DIR, VECTORSTORE_DIR
from src.ingestion.scraper import scrape_all
from src.ingestion.pdf_processor import process_all_pdfs
from src.retrieval.vectorstore import build_vectorstore, vectorstore_exists


def run_ingestion(
    force_rescrape: bool = False,
    force_reprocess: bool = False,
    force_rebuild: bool = False,
):
    logger.info("=" * 60)
    logger.info("🏥 CNAM Chatbot - Pipeline d'ingestion")
    logger.info("=" * 60)

    # ── Étape 1 : Scraping des PDFs ──────────────────────────────────────────
    existing_pdfs = list(RAW_PDFS_DIR.glob("*.pdf"))

    if force_rescrape or not existing_pdfs:
        logger.info("\n📥 Étape 1/3 : Téléchargement des PDFs depuis cnam.nat.tn...")
        downloaded = scrape_all()
        logger.info(f"  → {len(downloaded)} PDFs téléchargés")
    else:
        logger.info(f"\n📁 Étape 1/3 : {len(existing_pdfs)} PDFs déjà présents (skip scraping)")
        logger.info("  (Utilisez --force-rescrape pour re-télécharger)")

    # Vérifier qu'on a des PDFs
    pdf_files = list(RAW_PDFS_DIR.glob("*.pdf"))
    if not pdf_files:
        logger.error("❌ Aucun PDF disponible ! Vérifiez la connectivité au site CNAM.")
        logger.info(
            "\n💡 CONSEIL : Téléchargez manuellement les PDFs depuis :\n"
            "   https://www.cnam.nat.tn/espace_ps.jsp\n"
            f"   et placez-les dans : {RAW_PDFS_DIR}"
        )
        sys.exit(1)

    # ── Étape 2 : Extraction et chunking ─────────────────────────────────────
    chunks_file = PROCESSED_DIR / "all_chunks.json"

    if force_reprocess or not chunks_file.exists():
        logger.info(f"\n📄 Étape 2/3 : Extraction du texte de {len(pdf_files)} PDFs...")
        chunks = process_all_pdfs()
        logger.info(f"  → {len(chunks)} chunks créés")
    else:
        import json
        logger.info("\n📄 Étape 2/3 : Chunks déjà existants, chargement...")
        from src.ingestion.pdf_processor import DocumentChunk
        with open(chunks_file, encoding="utf-8") as f:
            data = json.load(f)
        chunks = [DocumentChunk(**d) for d in data]
        logger.info(f"  → {len(chunks)} chunks chargés")

    if not chunks:
        logger.error("❌ Aucun chunk extrait des PDFs !")
        sys.exit(1)

    # ── Étape 3 : Construction du VectorStore ─────────────────────────────────
    if force_rebuild or not vectorstore_exists():
        logger.info(f"\n🔢 Étape 3/3 : Construction du VectorStore FAISS ({len(chunks)} chunks)...")
        logger.info("  ⏳ Cela peut prendre quelques minutes...")
        vectorstore = build_vectorstore(chunks)
        logger.success("  ✅ VectorStore construit et sauvegardé")
    else:
        logger.info("\n🔢 Étape 3/3 : VectorStore déjà existant (skip rebuild)")

    logger.info("\n" + "=" * 60)
    logger.success("🎉 Ingestion terminée ! Le chatbot est prêt.")
    logger.info("   Lancez l'interface : streamlit run app/streamlit_app.py")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline d'ingestion CNAM Chatbot")
    parser.add_argument("--force-rescrape", action="store_true", help="Re-télécharger les PDFs")
    parser.add_argument("--force-reprocess", action="store_true", help="Ré-extraire le texte")
    parser.add_argument("--force-rebuild", action="store_true", help="Reconstruire le VectorStore")
    parser.add_argument("--full-rebuild", action="store_true", help="Tout reconstruire")
    args = parser.parse_args()

    run_ingestion(
        force_rescrape=args.force_rescrape or args.full_rebuild,
        force_reprocess=args.force_reprocess or args.full_rebuild,
        force_rebuild=args.force_rebuild or args.full_rebuild,
    )