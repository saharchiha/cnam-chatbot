"""
smart_retriever.py - Recherche intelligente dans les PDFs ciblés selon la question
"""
import re
from pathlib import Path
from loguru import logger
import fitz  # PyMuPDF
import pdfplumber

from src.utils.config import RAW_PDFS_DIR

# ── Mapping mots-clés → PDFs ciblés ─────────────────────────────────────────
# Quand la question contient un mot-clé, on cherche EN PRIORITÉ dans ces PDFs
KEYWORD_TO_PDFS = {
    # Imagerie / Radiologie
    "irm":           ["Liste des actes médicaux et paramédicaux", "Tarifs conventionnels", "Av 1", "Av 7"],
    "imagerie":      ["Liste des actes médicaux et paramédicaux", "Tarifs conventionnels", "Av 1"],
    "scanner":       ["Liste des actes médicaux et paramédicaux", "Tarifs conventionnels", "Av 1"],
    "radio":         ["Liste des actes médicaux et paramédicaux", "Tarifs conventionnels", "Av 4"],
    "radiologie":    ["Liste des actes médicaux et paramédicaux", "Tarifs conventionnels"],
    "échographie":   ["Liste des actes médicaux et paramédicaux", "Tarifs conventionnels"],
    "scintigraphie": ["Liste des actes médicaux et paramédicaux", "Tarifs conventionnels"],

    # Consultations
    "consultation":  ["Liste des consultations", "Tarifs conventionnels", "Av 4", "Av 7"],
    "généraliste":   ["Liste des consultations", "Tarifs conventionnels", "Médecins conventionnés"],
    "spécialiste":   ["Liste des consultations", "Tarifs conventionnels"],
    "psychiatre":    ["Liste des consultations", "Tarifs conventionnels", "Av 4"],
    "dentiste":      ["Médecins dentistes", "Tarifs conventionnels"],

    # Médicaments
    "médicament":    ["Guide du pharmacien", "Liste des spécialités pharmaceutiques"],
    "pharmacie":     ["Guide du pharmacien", "Pharmaciens conventionnés"],
    "remboursement": ["Tarifs conventionnels", "Bulletin de remboursement", "Av 4", "Av 7"],

    # Biologie
    "analyse":       ["Laboratoires de biologie", "Liste des actes médicaux et paramédicaux"],
    "biologie":      ["Laboratoires de biologie", "Biologistes"],
    "laboratoire":   ["Laboratoires de biologie", "Biologistes"],

    # Hospitalisation
    "hospitalisation": ["Hospitalisation", "Cliniques privées", "Convention sectorielle"],
    "chirurgie":      ["Hospitalisation", "Cliniques privées", "Liste des actes médicaux"],
    "clinique":       ["Cliniques privées", "Liste des cliniques privées"],

    # Listes conventionnés
    "médecin conventionné":   ["Médecins conventionnés"],
    "pharmacien conventionné":["Pharmaciens conventionnés"],
    "radiologue conventionné":["Radiologues conventionnés"],
    "biologiste conventionné":["Biologistes conventionnés"],
}

# Termes liés aux montants/prix à rechercher dans le texte extrait
PRICE_PATTERNS = [
    r'\d+[\s]?dinars?',           # "30 dinars"
    r'\d+[\s]?DT',                # "30 DT"
    r'\d+[\s]?TND',               # "30 TND"
    r'=[\s]?\d+',                 # "= 400"
    r':\s*\d+',                   # ": 400"
    r'tarif[^\n]*\d+',            # "tarif ... 400"
    r'lettre clé[^\n]*\d+',       # "lettre clé KE = 400"
    r'forfait[^\n]*\d+',          # "forfait 400"
    r'KE\s*=?\s*\d+',             # "KE = 1200"
    r'Kc\s*=?\s*\d+',             # "Kc = 4"
    r'\d+[\.,]\d+\s*(?:DT|dinars?|TND)',  # "1 200 DT"
]


def find_pdfs_for_query(query: str) -> list[Path]:
    """
    Trouve les PDFs les plus pertinents pour une question donnée.
    """
    query_lower = query.lower()
    matched_pdfs = []
    matched_keywords = []

    # Chercher les mots-clés dans la question
    for keyword, pdf_names in KEYWORD_TO_PDFS.items():
        if keyword in query_lower:
            matched_keywords.extend(pdf_names)

    if not matched_keywords:
        return []

    # Trouver les fichiers correspondants dans raw_pdfs
    all_pdfs = list(RAW_PDFS_DIR.glob("*.pdf"))
    for pdf_name_pattern in matched_keywords:
        for pdf_path in all_pdfs:
            if pdf_name_pattern.lower() in pdf_path.stem.lower():
                if pdf_path not in matched_pdfs:
                    matched_pdfs.append(pdf_path)

    logger.info(f"PDFs ciblés pour '{query[:40]}': {[p.name for p in matched_pdfs]}")
    return matched_pdfs


def extract_relevant_chunks(pdf_path: Path, query: str, max_chars: int = 3000) -> str:
    """
    Extrait les passages les plus pertinents d'un PDF pour une question donnée.
    Cherche les paragraphes contenant les mots-clés ET des montants.
    """
    query_words = set(query.lower().split())
    relevant_passages = []

    try:
        # Essai 1 : PyMuPDF
        doc = fitz.open(str(pdf_path))
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        doc.close()

        # Si texte insuffisant, essai pdfplumber (pour tableaux)
        if len(full_text.strip()) < 200:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if row:
                                full_text += " | ".join(str(c or "") for c in row) + "\n"
                    full_text += text + "\n"

        if not full_text.strip():
            logger.warning(f"PDF vide ou scanné : {pdf_path.name}")
            return ""

        # Découper en paragraphes et garder les plus pertinents
        paragraphs = [p.strip() for p in full_text.split('\n') if len(p.strip()) > 20]

        for para in paragraphs:
            para_lower = para.lower()
            # Le paragraphe contient un mot de la question ET un prix
            has_query_word = any(w in para_lower for w in query_words if len(w) > 3)
            has_price = any(re.search(pattern, para, re.IGNORECASE) for pattern in PRICE_PATTERNS)

            if has_query_word and has_price:
                relevant_passages.append(f"✓ {para}")
            elif has_query_word:
                relevant_passages.append(para)

        # Limiter la taille
        result = "\n".join(relevant_passages)
        if len(result) > max_chars:
            result = result[:max_chars] + "..."

        return result

    except Exception as e:
        logger.error(f"Erreur extraction {pdf_path.name}: {e}")
        return ""


def smart_search(query: str) -> str:
    """
    Point d'entrée : recherche intelligente dans les PDFs ciblés.
    Retourne le contexte enrichi pour le LLM.
    """
    targeted_pdfs = find_pdfs_for_query(query)
    if not targeted_pdfs:
        return ""

    context_parts = []
    for pdf_path in targeted_pdfs[:4]:  # Max 4 PDFs ciblés
        content = extract_relevant_chunks(pdf_path, query)
        if content:
            doc_type = pdf_path.stem.split('_')[0]  # Nom sans hash
            context_parts.append(
                f"[Extrait CNAM - {doc_type}]\n{content}"
            )

    if context_parts:
        logger.success(f"Smart search: {len(context_parts)} extraits trouvés")

    return "\n\n---\n\n".join(context_parts)