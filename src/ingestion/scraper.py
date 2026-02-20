"""
scraper.py - Scrape et télécharge tous les PDFs depuis le site CNAM Tunisie
"""
import time
import hashlib
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from loguru import logger
from src.utils.config import RAW_PDFS_DIR, CNAM_SITE_URL, CNAM_PS_PAGE

# Pages à scraper (ajouter d'autres si nécessaire)
TARGET_PAGES = [
    "https://www.cnam.nat.tn/espace_ps.jsp",
    "https://www.cnam.nat.tn/espace_assure.jsp",
    "https://www.cnam.nat.tn/tarification.jsp",
    "https://www.cnam.nat.tn/medicaments.jsp",
    "https://www.cnam.nat.tn/index.jsp",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def get_all_pdf_links(page_url: str, session: requests.Session) -> list[dict]:
    """
    Parse une page HTML et retourne tous les liens vers des PDFs.
    Returns: liste de dicts {"url": ..., "name": ...}
    """
    pdf_links = []
    try:
        resp = session.get(page_url, headers=HEADERS, timeout=30, verify=False)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Impossible d'accéder à {page_url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.lower().endswith(".pdf"):
            full_url = urljoin(page_url, href)
            name = tag.get_text(strip=True) or Path(urlparse(full_url).path).stem
            pdf_links.append({"url": full_url, "name": name, "source_page": page_url})

    logger.info(f"Trouvé {len(pdf_links)} PDFs sur {page_url}")
    return pdf_links


def download_pdf(pdf_info: dict, session: requests.Session, dest_dir: Path) -> Path | None:
    """
    Télécharge un PDF et le sauvegarde localement.
    Utilise un hash de l'URL pour éviter les doublons.
    Returns: chemin local du fichier ou None si échec
    """
    url = pdf_info["url"]
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in pdf_info["name"])
    filename = f"{safe_name}_{url_hash}.pdf"
    dest_path = dest_dir / filename

    if dest_path.exists():
        logger.debug(f"Déjà téléchargé : {filename}")
        return dest_path

    try:
        resp = session.get(url, headers=HEADERS, timeout=60, verify=False, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
            logger.warning(f"Pas un PDF ({content_type}): {url}")
            return None

        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.success(f"Téléchargé : {filename} ({dest_path.stat().st_size // 1024} KB)")
        return dest_path

    except requests.RequestException as e:
        logger.error(f"Erreur téléchargement {url}: {e}")
        return None


def scrape_all(pages: list[str] = None, dest_dir: Path = RAW_PDFS_DIR) -> list[Path]:
    """
    Point d'entrée principal : scrape toutes les pages et télécharge les PDFs.
    Returns: liste des chemins locaux des PDFs téléchargés
    """
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    pages = pages or TARGET_PAGES
    session = requests.Session()
    all_pdf_links = []

    # Collecter tous les liens PDF
    for page_url in pages:
        logger.info(f"Scraping de la page : {page_url}")
        links = get_all_pdf_links(page_url, session)
        all_pdf_links.extend(links)
        time.sleep(1)  # Politesse envers le serveur

    # Dédupliquer par URL
    seen_urls = set()
    unique_links = []
    for link in all_pdf_links:
        if link["url"] not in seen_urls:
            seen_urls.add(link["url"])
            unique_links.append(link)

    logger.info(f"Total PDFs uniques à télécharger : {len(unique_links)}")

    # Télécharger
    downloaded = []
    for i, pdf_info in enumerate(unique_links, 1):
        logger.info(f"[{i}/{len(unique_links)}] {pdf_info['name']}")
        path = download_pdf(pdf_info, session, dest_dir)
        if path:
            downloaded.append(path)
        time.sleep(0.5)

    logger.success(f"✅ {len(downloaded)}/{len(unique_links)} PDFs téléchargés dans {dest_dir}")
    return downloaded


if __name__ == "__main__":
    downloaded = scrape_all()
    print(f"\n{len(downloaded)} PDFs téléchargés.")