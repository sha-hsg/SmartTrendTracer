"""
ACL Anthology import service for parsing papers from aclanthology.org
"""
import re
import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class ACLAnthologyService:
    """Service for importing papers from ACL Anthology"""
    
    BASE_URL = "https://aclanthology.org"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def parse_acl_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Parse an ACL Anthology URL to extract paper metadata
        
        Args:
            url: ACL Anthology paper URL (e.g., https://aclanthology.org/2025.acl-long.5/)
            
        Returns:
            Dictionary containing paper metadata
        """
        try:
            # Validate URL
            if not url.startswith(('http://aclanthology.org', 'https://aclanthology.org')):
                raise ValueError(f"Invalid ACL Anthology URL: {url}")
            
            # Fetch the page
            logger.info(f"Fetching ACL Anthology page: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url)
            
            if not metadata:
                raise ValueError("Could not extract metadata from ACL Anthology page")
            
            # Add PDF URL
            metadata['pdf_url'] = self._get_pdf_url(url, soup)
            metadata['source_url'] = url
            
            logger.info(f"Successfully parsed ACL Anthology paper: {metadata.get('title', 'Unknown')}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error parsing ACL Anthology URL {url}: {e}")
            raise
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from ACL Anthology page"""
        metadata = {}
        
        # Title - usually in <h2> with class "title"
        title_elem = soup.find('h2', class_='title') or soup.find('h1', class_='title')
        if not title_elem:
            # Fallback: look for meta tag
            meta_title = soup.find('meta', {'property': 'og:title'})
            if meta_title:
                metadata['title'] = meta_title.get('content', '').strip()
        else:
            metadata['title'] = title_elem.text.strip()
        
        # Authors - try multiple methods to extract
        authors = []
        
        # Method 1: Look for <p> with class "lead" (common format)
        author_elem = soup.find('p', class_='lead')
        if author_elem:
            # Parse author names from the lead paragraph
            author_text = author_elem.text.strip()
            # Split by comma and "and" for proper parsing
            if ' and ' in author_text:
                # Handle "Author1, Author2, and Author3" format
                parts = author_text.rsplit(' and ', 1)
                if len(parts) == 2:
                    authors = [name.strip() for name in parts[0].split(',')]
                    authors.append(parts[1].strip())
            else:
                # Simple comma-separated
                authors = [name.strip() for name in author_text.split(',')]
        
        # Method 2: Look for author links (fallback)
        if not authors:
            author_links = soup.find_all('a', href=re.compile(r'/people/'))
            authors = [link.text.strip() for link in author_links]
        
        # Method 3: Extract from citation text (another fallback)
        if not authors:
            cite_elem = soup.find(text=re.compile(r'Cite \(ACL\):'))
            if cite_elem:
                # Get the next text which contains the citation
                cite_text = cite_elem.find_next().text if cite_elem.find_next() else ""
                # Extract authors from citation (before year)
                match = re.match(r'^([^.]+?)\.\s*\d{4}', cite_text)
                if match:
                    author_string = match.group(1)
                    # Parse "Author1, Author2, and Author3" format
                    if ' and ' in author_string:
                        parts = author_string.rsplit(' and ', 1)
                        if len(parts) == 2:
                            authors = [name.strip() for name in parts[0].split(',')]
                            authors.append(parts[1].strip())
                    else:
                        authors = [name.strip() for name in author_string.split(',')]
        
        # Method 4: Extract from BibTeX if available (most reliable)
        if not authors:
            bibtex_elem = soup.find('pre', class_='bibtex') or soup.find('code', class_='bibtex')
            if not bibtex_elem:
                # Look for BibTeX in a different format
                bibtex_button = soup.find('button', {'data-clipboard-text': True})
                if bibtex_button:
                    bibtex_text = bibtex_button.get('data-clipboard-text', '')
                else:
                    bibtex_text = ""
            else:
                bibtex_text = bibtex_elem.text.strip()
            
            if bibtex_text:
                # Extract authors from BibTeX
                authors = self._extract_authors_from_bibtex(bibtex_text)
        
        metadata['authors'] = authors
        
        # Abstract - look for the abstract span or div
        abstract_elem = None
        
        # Method 1: Look for span with class="abstract-text"
        abstract_elem = soup.find('span', class_='abstract-text')
        
        # Method 2: Look for div with class="card-body" containing abstract
        if not abstract_elem:
            card_bodies = soup.find_all('div', class_='card-body')
            for card in card_bodies:
                # Check if this card contains the abstract
                if 'Abstract' in card.text[:100]:
                    # Find the actual abstract text (usually after "Abstract" heading)
                    abstract_elem = card
                    break
        
        # Method 3: Look for any element containing "Abstract" as heading
        if not abstract_elem:
            abstract_heading = soup.find(text=re.compile(r'^Abstract$', re.I))
            if abstract_heading:
                # Get the parent element and then find the text
                parent = abstract_heading.parent
                if parent:
                    # Look for next sibling or within parent
                    abstract_elem = parent.find_next_sibling() or parent
        
        if abstract_elem:
            # Clean up the abstract text
            abstract_text = abstract_elem.text.strip()
            # Remove "Abstract" heading if present at the beginning
            if abstract_text.startswith('Abstract'):
                abstract_text = abstract_text[8:].strip()
            metadata['abstract'] = abstract_text
        
        # Extract structured metadata from the page
        metadata_section = soup.find('dl', class_='row') or soup.find('div', class_='acl-paper-details')
        if metadata_section:
            metadata.update(self._parse_metadata_section(metadata_section))
        
        # Anthology ID
        anthology_id_elem = soup.find(text=re.compile(r'Anthology ID:'))
        if anthology_id_elem:
            anthology_id = anthology_id_elem.find_next().text.strip()
            metadata['anthology_id'] = anthology_id
        
        # Conference/Venue information
        venue_elem = soup.find(text=re.compile(r'Venue:'))
        if venue_elem:
            venue = venue_elem.find_next().text.strip()
            metadata['venue'] = venue
        
        # Year
        year_elem = soup.find(text=re.compile(r'Year:'))
        if year_elem:
            year_text = year_elem.find_next().text.strip()
            metadata['year'] = int(year_text) if year_text.isdigit() else None
        
        # DOI
        doi_elem = soup.find(text=re.compile(r'DOI:'))
        if doi_elem:
            doi = doi_elem.find_next().text.strip()
            metadata['doi'] = doi
        elif soup.find('a', href=re.compile(r'doi\.org')):
            doi_link = soup.find('a', href=re.compile(r'doi\.org'))
            metadata['doi'] = doi_link.text.strip()
        
        # Pages
        pages_elem = soup.find(text=re.compile(r'Pages:'))
        if pages_elem:
            pages = pages_elem.find_next().text.strip()
            metadata['pages'] = pages
        
        # BibTeX - look for pre-formatted bibtex or in button data
        bibtex_text = ""
        bibtex_elem = soup.find('pre', class_='bibtex') or soup.find('code', class_='bibtex')
        if bibtex_elem:
            bibtex_text = bibtex_elem.text.strip()
        else:
            # Look for BibTeX in button's clipboard data
            bibtex_button = soup.find('button', {'data-clipboard-text': True})
            if bibtex_button:
                button_text = bibtex_button.get('data-clipboard-text', '')
                # Check if it looks like BibTeX
                if '@' in button_text and '{' in button_text:
                    bibtex_text = button_text
        
        if bibtex_text:
            metadata['bibtex'] = bibtex_text
            
            # If we still don't have authors, try extracting from BibTeX
            if not metadata.get('authors'):
                metadata['authors'] = self._extract_authors_from_bibtex(bibtex_text)
        
        # Volume/Proceedings
        volume_elem = soup.find(text=re.compile(r'Volume:'))
        if volume_elem:
            volume = volume_elem.find_next().text.strip()
            metadata['proceedings'] = volume
        
        return metadata
    
    def _parse_metadata_section(self, section) -> Dict[str, Any]:
        """Parse the metadata section with dt/dd pairs"""
        metadata = {}
        
        # Find all dt/dd pairs
        labels = section.find_all('dt')
        values = section.find_all('dd')
        
        for label, value in zip(labels, values):
            label_text = label.text.strip().rstrip(':').lower()
            value_text = value.text.strip()
            
            if 'anthology' in label_text:
                metadata['anthology_id'] = value_text
            elif 'venue' in label_text:
                metadata['venue'] = value_text
            elif 'year' in label_text:
                try:
                    metadata['year'] = int(value_text)
                except Exception:
                    pass
            elif 'month' in label_text:
                metadata['month'] = value_text
            elif 'doi' in label_text:
                metadata['doi'] = value_text
            elif 'pages' in label_text:
                metadata['pages'] = value_text
            elif 'volume' in label_text or 'proceedings' in label_text:
                metadata['proceedings'] = value_text
            elif 'address' in label_text or 'location' in label_text:
                metadata['location'] = value_text
            elif 'publisher' in label_text:
                metadata['publisher'] = value_text
            elif 'editor' in label_text:
                # Parse editors
                editors = [e.strip() for e in value_text.split(',')]
                metadata['editors'] = editors
        
        return metadata
    
    def _extract_authors_from_bibtex(self, bibtex_text: str) -> List[str]:
        """Extract author names from BibTeX entry"""
        authors = []
        
        # Look for author field in BibTeX
        # Match author = {....} or author = "..."
        author_match = re.search(r'author\s*=\s*[{"]([^}"]*)["{}]', bibtex_text, re.IGNORECASE | re.DOTALL)
        if author_match:
            author_string = author_match.group(1)
            # Clean up the author string
            author_string = author_string.replace('\n', ' ').strip()
            
            # Split by "and" (BibTeX format)
            author_parts = author_string.split(' and ')
            for author in author_parts:
                author = author.strip()
                if author:
                    # Handle "Last, First" format or "First Last" format
                    if ',' in author:
                        # "Last, First" format - reverse it
                        parts = author.split(',', 1)
                        if len(parts) == 2:
                            author = f"{parts[1].strip()} {parts[0].strip()}"
                    authors.append(author)
        
        return authors
    
    def _get_pdf_url(self, page_url: str, soup: BeautifulSoup) -> str:
        """Get the PDF URL from the page"""
        # First try: look for PDF link on the page
        pdf_link = soup.find('a', href=re.compile(r'\.pdf$'))
        if pdf_link:
            return urljoin(page_url, pdf_link['href'])
        
        # Second try: construct from URL pattern
        # ACL Anthology URLs typically follow pattern:
        # Page: https://aclanthology.org/2025.acl-long.5/
        # PDF: https://aclanthology.org/2025.acl-long.5.pdf
        if page_url.endswith('/'):
            pdf_url = page_url.rstrip('/') + '.pdf'
        else:
            pdf_url = page_url + '.pdf'
        
        return pdf_url
    
    def download_paper(self, pdf_url: str, save_dir: Path) -> Path:
        """
        Download paper PDF from ACL Anthology
        
        Args:
            pdf_url: URL to the PDF file
            save_dir: Directory to save the PDF
            
        Returns:
            Path to the saved PDF file
        """
        try:
            # Create save directory if it doesn't exist
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename from URL
            url_path = urlparse(pdf_url).path
            filename = url_path.split('/')[-1]
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            # Add timestamp and hash to avoid conflicts
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            url_hash = hashlib.md5(pdf_url.encode()).hexdigest()[:8]
            filename = f"{timestamp}_{url_hash}_{filename}"
            
            save_path = save_dir / filename
            
            # Download the PDF
            logger.info(f"Downloading PDF from: {pdf_url}")
            response = self.session.get(pdf_url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Save to file
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"PDF saved to: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"Error downloading PDF from {pdf_url}: {e}")
            raise
    
    def import_paper(self, url: str, save_dir: Path) -> Dict[str, Any]:
        """
        Import a paper from ACL Anthology URL
        
        Args:
            url: ACL Anthology paper URL
            save_dir: Directory to save the PDF
            
        Returns:
            Dictionary with paper metadata and local PDF path
        """
        try:
            # Parse the ACL Anthology page
            metadata = self.parse_acl_url(url)
            
            # Download the PDF
            pdf_path = self.download_paper(metadata['pdf_url'], save_dir)
            metadata['pdf_path'] = str(pdf_path)
            
            # Format for database storage
            paper_data = {
                'title': metadata.get('title', ''),
                'authors': ', '.join(metadata.get('authors', [])),
                'abstract': metadata.get('abstract', ''),
                'pdf_path': str(pdf_path),
                'pdf_url': metadata.get('pdf_url', ''),
                'doi': metadata.get('doi', ''),
                'conference': metadata.get('venue', ''),
                'proceedings': metadata.get('proceedings', ''),
                'publication_date': self._parse_publication_date(
                    metadata.get('year'),
                    metadata.get('month')
                ),
                'pages': metadata.get('pages', ''),
                'source': 'acl_anthology',
                'source_id': metadata.get('anthology_id', ''),
                'source_url': url,
                'metadata': metadata  # Store full metadata
            }
            
            return paper_data
            
        except Exception as e:
            logger.error(f"Error importing paper from {url}: {e}")
            raise
    
    def _parse_publication_date(self, year: Optional[int], month: Optional[str]) -> Optional[datetime]:
        """Parse publication date from year and month"""
        if not year:
            return None
        
        # Map month names to numbers
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        month_num = 1  # Default to January
        if month:
            month_lower = month.lower()
            month_num = month_map.get(month_lower, 1)
        
        try:
            return datetime(year, month_num, 1)
        except Exception:
            return None


# Singleton instance
acl_anthology_service = ACLAnthologyService()