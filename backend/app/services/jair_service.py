"""
JAIR (Journal of Artificial Intelligence Research) import service.
Parses article pages from jair.org using citation_* meta tags.
"""
import re
import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class JAIRService:
    """Service for importing papers from JAIR (jair.org)"""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def extract_article_id(self, url: str) -> Optional[str]:
        """Extract numeric article ID from a JAIR URL."""
        match = re.search(r'/article/(?:view|download)/(\d+)', url)
        return match.group(1) if match else None

    def parse_jair_url(self, url: str) -> Dict[str, Any]:
        """Fetch a JAIR article page and extract metadata from citation_* meta tags."""
        if 'jair.org' not in url:
            raise ValueError(f"Not a JAIR URL: {url}")

        logger.info(f"Fetching JAIR page: {url}")
        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        metadata: Dict[str, Any] = {}

        # Title
        tag = soup.find('meta', attrs={'name': 'citation_title'})
        metadata['title'] = tag['content'].strip() if tag else ''

        # Authors + affiliations (paired: each citation_author followed by citation_author_institution)
        author_tags = soup.find_all('meta', attrs={'name': 'citation_author'})
        institution_tags = soup.find_all('meta', attrs={'name': 'citation_author_institution'})

        authors: List[str] = []
        authors_detailed: List[Dict[str, Any]] = []
        for i, atag in enumerate(author_tags):
            name = atag['content'].strip()
            authors.append(name)
            affiliation = institution_tags[i]['content'].strip() if i < len(institution_tags) else ''
            authors_detailed.append({
                'name': name,
                'affiliation': affiliation,
                'position': i,
            })

        metadata['authors'] = ', '.join(authors)
        metadata['authors_list'] = authors
        metadata['authors_detailed'] = authors_detailed

        # Abstract — DC.Description is cleaner than HTML abstract
        dc_desc = soup.find('meta', attrs={'name': 'DC.Description'})
        metadata['abstract'] = dc_desc['content'].strip() if dc_desc else ''

        # PDF URL
        pdf_tag = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        metadata['pdf_url'] = pdf_tag['content'].strip() if pdf_tag else ''

        # DOI
        doi_tag = soup.find('meta', attrs={'name': 'citation_doi'})
        metadata['doi'] = doi_tag['content'].strip() if doi_tag else ''

        # Volume
        vol_tag = soup.find('meta', attrs={'name': 'citation_volume'})
        metadata['volume'] = vol_tag['content'].strip() if vol_tag else ''

        # Date
        date_tag = soup.find('meta', attrs={'name': 'citation_date'})
        if date_tag:
            raw = date_tag['content'].strip()
            metadata['date_raw'] = raw
            try:
                metadata['year'] = int(raw.split('/')[0])
            except (ValueError, IndexError):
                metadata['year'] = None
        else:
            metadata['year'] = None

        # Journal name
        journal_tag = soup.find('meta', attrs={'name': 'citation_journal_title'})
        metadata['journal'] = journal_tag['content'].strip() if journal_tag else 'Journal of Artificial Intelligence Research'

        # Keywords
        kw_tags = soup.find_all('meta', attrs={'name': 'citation_keywords'})
        keywords: List[str] = []
        for kw in kw_tags:
            # Keywords may be semicolon-separated within a single tag
            for k in kw['content'].split(';'):
                k = k.strip()
                if k:
                    keywords.append(k)
        metadata['keywords'] = keywords

        # Article ID
        metadata['jair_article_id'] = self.extract_article_id(url)
        metadata['source_url'] = url

        logger.info(f"Parsed JAIR paper: {metadata.get('title', '?')}")
        return metadata

    def download_pdf(self, pdf_url: str, save_dir: Path, title: str = '') -> str:
        """Download PDF from JAIR and return local file path."""
        save_dir.mkdir(parents=True, exist_ok=True)

        safe_title = re.sub(r'[^\w\s-]', '', title)[:60].strip().replace(' ', '_') or 'jair_paper'
        url_hash = hashlib.md5(pdf_url.encode()).hexdigest()[:8]
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d')
        filename = f"{timestamp}_{url_hash}_{safe_title}.pdf"
        save_path = save_dir / filename

        logger.info(f"Downloading JAIR PDF: {pdf_url}")
        response = self.session.get(pdf_url, timeout=120, stream=True)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = save_path.stat().st_size
        logger.info(f"Downloaded PDF: {save_path} ({file_size / 1024:.0f} KB)")
        return str(save_path)

    def import_paper(self, url: str, save_dir: Path) -> Dict[str, Any]:
        """Parse metadata and download PDF. Returns combined paper data."""
        metadata = self.parse_jair_url(url)

        if not metadata.get('pdf_url'):
            raise ValueError("Could not find PDF URL on JAIR page")

        pdf_path = self.download_pdf(metadata['pdf_url'], save_dir, metadata.get('title', ''))
        metadata['pdf_path'] = pdf_path

        return metadata


# Singleton
jair_service = JAIRService()
