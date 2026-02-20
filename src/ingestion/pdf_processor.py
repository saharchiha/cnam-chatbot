"""
pdf_processor.py - Extraction de texte + chunking des PDFs CNAM
Supporte l'arabe et le français.
"""
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from loguru import logger

import fitz  # PyMuPDF
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.utils.config import RAW_PDFS_DIR, PROCESSED_DIR, CHUNK_SIZE, CHUNK_OVERLAP


@dataclass
class DocumentChunk:
    content: str
    metadata: dict

    def to_dict(self) -> dict:
        return asdict(self)


def extract_text_pymupdf(pdf_path: Path) -> str:
    """Extraction rapide avec PyMuPDF (meilleur pour les PDFs textuels)."""
    text_parts = []
    try:
        doc = fitz.open(str(pdf_path))
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                text_parts.append(f"[Page {page_num + 1}]\n{text}")
        doc.close()
    except Exception as e:
        logger.warning(f"PyMuPDF erreur sur {pdf_path.name}: {e}")
    return "\n\n".join(text_parts)


def extract_text_pdfplumber(pdf_path: Path) -> str:
    """Extraction avec pdfplumber (meilleur pour les tableaux)."""
    text_parts = []
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extraire texte normal
                text = page.extract_text() or ""
                # Extraire tableaux
                tables = page.extract_tables()
                table_text = ""
                for table in tables:
                    for row in table:
                        if row:
                            row_clean = [str(c).strip() if c else "" for c in row]
                            table_text += " | ".join(row_clean) + "\n"
                combined = text + ("\n[TABLE]\n" + table_text if table_text else "")
                if combined.strip():
                    text_parts.append(f"[Page {page_num + 1}]\n{combined}")
    except Exception as e:
        logger.warning(f"pdfplumber erreur sur {pdf_path.name}: {e}")
    return "\n\n".join(text_parts)


def extract_text(pdf_path: Path) -> str:
    """
    Tente d'abord PyMuPDF, puis pdfplumber si résultat insuffisant.
    """
    text = extract_text_pymupdf(pdf_path)
    if len(text.strip()) < 100:
        logger.debug(f"PyMuPDF insuffisant pour {pdf_path.name}, essai pdfplumber")
        text = extract_text_pdfplumber(pdf_path)
    if len(text.strip()) < 50:
        logger.warning(f"⚠️  PDF possiblement scanné (image) : {pdf_path.name}")
    return text


def chunk_text(text: str, pdf_path: Path) -> list[DocumentChunk]:
    """
    Découpe le texte en chunks avec métadonnées.
    Utilise RecursiveCharacterTextSplitter compatible arabe/français.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", "،", " ", ""],  # "،" = virgule arabe
        length_function=len,
    )
    chunks_text = splitter.split_text(text)
    chunks = []
    for i, chunk_content in enumerate(chunks_text):
        if len(chunk_content.strip()) < 30:
            continue  # Ignorer les chunks trop petits
        chunk = DocumentChunk(
            content=chunk_content.strip(),
            metadata={
                "source": pdf_path.name,
                "source_path": str(pdf_path),
                "chunk_index": i,
                "total_chunks": len(chunks_text),
                "doc_type": classify_document(pdf_path.name),
            },
        )
        chunks.append(chunk)
    return chunks


def classify_document(filename: str) -> str:
    """
    Classifie le type de document CNAM selon le nom de fichier.
    """
    filename_lower = filename.lower()
    if any(k in filename_lower for k in ["medicament", "médicament", "pharmacie", "dawa"]):
        return "medicaments"
    elif any(k in filename_lower for k in ["tarif", "remboursement", "nomenclature", "prix"]):
        return "tarification"
    elif any(k in filename_lower for k in ["radiologie", "radio", "imagerie", "scanner"]):
        return "radiologie"
    elif any(k in filename_lower for k in ["consultation", "medecin", "médecin", "praticien"]):
        return "consultation"
    elif any(k in filename_lower for k in ["convention", "conventionné", "agrément"]):
        return "conventions"
    elif any(k in filename_lower for k in ["formulaire", "demande", "dossier"]):
        return "formulaires"
    elif any(k in filename_lower for k in ["chirurgie", "hospitalisation", "hopital"]):
        return "hospitalisation"
    else:
        return "general"


def process_pdf(pdf_path: Path) -> list[DocumentChunk]:
    """Pipeline complet : extraction + chunking d'un seul PDF."""
    logger.info(f"Traitement de : {pdf_path.name}")
    text = extract_text(pdf_path)
    if not text.strip():
        logger.error(f"Aucun texte extrait de {pdf_path.name}")
        return []
    chunks = chunk_text(text, pdf_path)
    logger.success(f"  ✅ {len(chunks)} chunks créés depuis {pdf_path.name}")
    return chunks


def process_all_pdfs(
    pdf_dir: Path = RAW_PDFS_DIR,
    output_dir: Path = PROCESSED_DIR,
) -> list[DocumentChunk]:
    """
    Traite tous les PDFs dans pdf_dir et sauvegarde les chunks.
    """
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"Aucun PDF trouvé dans {pdf_dir}")
        return []

    logger.info(f"Traitement de {len(pdf_files)} PDFs...")
    all_chunks = []

    for pdf_path in pdf_files:
        chunks = process_pdf(pdf_path)
        all_chunks.extend(chunks)

    # Sauvegarder en JSON pour inspection / réutilisation
    output_path = output_dir / "all_chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([c.to_dict() for c in all_chunks], f, ensure_ascii=False, indent=2)

    logger.success(f"✅ Total : {len(all_chunks)} chunks → {output_path}")
    return all_chunks


if __name__ == "__main__":
    chunks = process_all_pdfs()
    print(f"Total chunks: {len(chunks)}")
    # Aperçu du premier chunk
    if chunks:
        print(f"\nExemple:\n{chunks[0].content[:300]}")
        print(f"Metadata: {chunks[0].metadata}")