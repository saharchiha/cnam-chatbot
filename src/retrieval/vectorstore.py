"""
vectorstore.py - Création et gestion du VectorStore FAISS pour CNAM
"""
from pathlib import Path
from loguru import logger

from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings

from src.utils.config import (
    EMBEDDING_PROVIDER,
    HF_EMBEDDING_MODEL,
    VECTORSTORE_DIR,
    FAISS_INDEX_NAME,
)
from src.ingestion.pdf_processor import DocumentChunk


def get_embeddings():
    """
    Retourne le modèle d'embeddings HuggingFace (multilingue fr/ar).
    Groq ne fournit pas d'API embeddings, on utilise HuggingFace gratuitement.
    """
    logger.info(f"Embeddings HuggingFace : {HF_EMBEDDING_MODEL}")
    return HuggingFaceEmbeddings(
        model_name=HF_EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def chunks_to_documents(chunks: list[DocumentChunk]) -> list[Document]:
    """Convertit les DocumentChunks en Documents LangChain."""
    return [
        Document(page_content=chunk.content, metadata=chunk.metadata)
        for chunk in chunks
    ]


def build_vectorstore(
    chunks: list[DocumentChunk],
    index_dir: Path = VECTORSTORE_DIR,
    index_name: str = FAISS_INDEX_NAME,
) -> FAISS:
    """
    Crée un index FAISS depuis les chunks et le sauvegarde sur disque.
    """
    if not chunks:
        raise ValueError("Aucun chunk fourni pour construire le vectorstore.")

    logger.info(f"Construction du vectorstore avec {len(chunks)} chunks...")
    embeddings = get_embeddings()
    documents = chunks_to_documents(chunks)

    # Créer le vectorstore par batch pour éviter les timeouts API
    BATCH_SIZE = 500
    vectorstore = None

    for i in range(0, len(documents), BATCH_SIZE):
        batch = documents[i : i + BATCH_SIZE]
        logger.info(f"  Batch {i // BATCH_SIZE + 1}: {len(batch)} documents")

        if vectorstore is None:
            vectorstore = FAISS.from_documents(batch, embeddings)
        else:
            batch_vs = FAISS.from_documents(batch, embeddings)
            vectorstore.merge_from(batch_vs)

    # Sauvegarder sur disque
    save_path = index_dir / index_name
    vectorstore.save_local(str(save_path))
    logger.success(f"✅ Vectorstore sauvegardé : {save_path}")
    return vectorstore


def load_vectorstore(
    index_dir: Path = VECTORSTORE_DIR,
    index_name: str = FAISS_INDEX_NAME,
) -> FAISS:
    """
    Charge un index FAISS existant depuis le disque.
    """
    index_path = index_dir / index_name
    if not (index_path / "index.faiss").exists():
        raise FileNotFoundError(
            f"Index FAISS introuvable : {index_path}\n"
            "Lancez d'abord : python scripts/ingest_all.py"
        )
    logger.info(f"Chargement du vectorstore : {index_path}")
    embeddings = get_embeddings()
    vectorstore = FAISS.load_local(
        str(index_path),
        embeddings,
        allow_dangerous_deserialization=True,
    )
    logger.success(f"✅ Vectorstore chargé ({vectorstore.index.ntotal} vecteurs)")
    return vectorstore


def vectorstore_exists(
    index_dir: Path = VECTORSTORE_DIR,
    index_name: str = FAISS_INDEX_NAME,
) -> bool:
    index_path = index_dir / index_name
    return (index_path / "index.faiss").exists()