"""
OpenReview integration service
Handles paper metadata extraction and PDF downloads from openreview.net
"""
import logging
import re
import json
from typing import Dict, Any, Optional, List
import requests
from datetime import datetime, timezone
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

class OpenReviewService:
    """Service for importing papers from OpenReview"""
    
    BASE_URL = "https://openreview.net"
    API_BASE = "https://api.openreview.net"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/html',
        })
    
    def extract_forum_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract forum ID from OpenReview URL
        
        Args:
            url: OpenReview URL (e.g., https://openreview.net/forum?id=ZZ4tcxJvux)
            
        Returns:
            Forum ID string or None
        """
        # Pattern for OpenReview forum URLs
        patterns = [
            r'openreview\.net/forum\?id=([^&#]+)',
            r'openreview\.net/pdf\?id=([^&#]+)',
            r'api\.openreview\.net/notes\?id=([^&#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def fetch_paper_metadata(self, forum_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch paper metadata using OpenReview API v2
        
        Args:
            forum_id: OpenReview forum ID
            
        Returns:
            Dictionary with paper metadata or None
        """
        try:
            # Use OpenReview API v2
            api_url = "https://api2.openreview.net/notes"
            params = {'id': forum_id}
            
            response = self.session.get(api_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # OpenReview API returns a dict with 'notes' key
                notes = data.get('notes', [])
                
                if notes and len(notes) > 0:
                    note = notes[0]  # Get the first (main) note
                    
                    # Extract content fields
                    content = note.get('content', {})
                    
                    # Helper function to extract value from field (handles both direct values and dict with 'value' key)
                    def extract_value(field, default=''):
                        if isinstance(field, dict) and 'value' in field:
                            return field['value']
                        return field if field else default
                    
                    # Extract title
                    title = extract_value(content.get('title', {}), 'Untitled')
                    
                    # Extract authors
                    authors_field = content.get('authors', {})
                    authors = extract_value(authors_field, [])
                    if not isinstance(authors, list):
                        authors = []
                    
                    # Extract abstract
                    abstract = extract_value(content.get('abstract', {}), '')
                    
                    # Extract keywords
                    keywords_field = content.get('keywords', {})
                    keywords = extract_value(keywords_field, [])
                    if not isinstance(keywords, list):
                        keywords = []
                    
                    # Extract venue
                    venue = extract_value(content.get('venue', {}), '')
                    
                    # Extract TL;DR - check both 'TLDR' and 'TL;DR' keys
                    tldr = extract_value(content.get('TLDR', {}), '') or extract_value(content.get('TL;DR', {}), '')
                    
                    # Extract year from venue or creation date
                    year = None
                    if venue:
                        year_match = re.search(r'20\d{2}', venue)
                        if year_match:
                            year = int(year_match.group())
                    
                    # If no year in venue, try from cdate
                    if not year and 'cdate' in note:
                        # cdate is in milliseconds
                        try:
                            created_date = datetime.fromtimestamp(note['cdate'] / 1000)
                            year = created_date.year
                        except Exception:
                            pass
                    
                    # Extract PDF link
                    pdf_url = None
                    pdf_path = extract_value(content.get('pdf', {}), '')
                    if pdf_path:
                        if not pdf_path.startswith('http'):
                            pdf_url = f"{self.BASE_URL}{pdf_path}"
                        else:
                            pdf_url = pdf_path
                    else:
                        # Fallback to standard URL
                        pdf_url = f"{self.BASE_URL}/pdf?id={forum_id}"
                    
                    # Extract supplementary material
                    supplementary = []
                    supp_material = extract_value(content.get('supplementary_material', {}), '')
                    if supp_material:
                        supplementary.append({
                            'type': 'Supplementary Material',
                            'url': supp_material if supp_material.startswith('http') else f"{self.BASE_URL}{supp_material}"
                        })
                    
                    # Check for code URL
                    code_url = extract_value(content.get('code', {}), '')
                    if code_url:
                        supplementary.append({
                            'type': 'Code',
                            'url': code_url
                        })
                    
                    # Extract BibTeX if available
                    bibtex = extract_value(content.get('_bibtex', {}), '')
                    
                    # Extract publication date
                    publication_date = None
                    if 'pdate' in note:
                        try:
                            publication_date = datetime.fromtimestamp(note['pdate'] / 1000)
                        except Exception:
                            pass
                    elif 'cdate' in note:
                        try:
                            publication_date = datetime.fromtimestamp(note['cdate'] / 1000)
                        except Exception:
                            pass
                    
                    # Build metadata dictionary
                    metadata = {
                        'title': title,
                        'authors': authors,
                        'abstract': abstract,
                        'keywords': keywords,
                        'venue': venue,
                        'year': year,
                        'forum_id': forum_id,
                        'pdf_url': pdf_url,
                        'supplementary': supplementary,
                        'tldr': tldr,
                        'openreview_url': f"{self.BASE_URL}/forum?id={forum_id}",
                        'bibtex': bibtex,  # Use the provided BibTeX
                        'publication_date': publication_date.isoformat() if publication_date else None,
                        'api_response': note  # Store full response for debugging
                    }
                    
                    return metadata
            
            # Fallback: Try scraping the forum page
            return self._scrape_forum_page(forum_id)
            
        except Exception as e:
            logger.error(f"Error fetching OpenReview metadata: {e}")
            return self._scrape_forum_page(forum_id)
    
    def _scrape_forum_page(self, forum_id: str) -> Optional[Dict[str, Any]]:
        """
        Fallback method to scrape metadata from forum page
        
        Args:
            forum_id: OpenReview forum ID
            
        Returns:
            Dictionary with paper metadata or None
        """
        try:
            forum_url = f"{self.BASE_URL}/forum?id={forum_id}"
            response = self.session.get(forum_url, timeout=15)
            
            if response.status_code != 200:
                return None
            
            # OpenReview uses React and loads data dynamically
            # Look for the __NEXT_DATA__ script tag which contains the initial data
            import re
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the script tag with __NEXT_DATA__
            script_tag = soup.find('script', id='__NEXT_DATA__')
            if script_tag:
                try:
                    data = json.loads(script_tag.string)
                    
                    # Navigate through the Next.js data structure
                    props = data.get('props', {}).get('pageProps', {})
                    note = props.get('note', {}) or props.get('forumNote', {})
                    
                    if note:
                        content = note.get('content', {})
                        
                        # Extract metadata from the scraped data
                        title = content.get('title', 'Untitled')
                        authors = content.get('authors', [])
                        abstract = content.get('abstract', '')
                        keywords = content.get('keywords', [])
                        venue = content.get('venue', '')
                        
                        # Construct metadata
                        metadata = {
                            'title': title,
                            'authors': authors if isinstance(authors, list) else [],
                            'abstract': abstract,
                            'keywords': keywords if isinstance(keywords, list) else [],
                            'venue': venue,
                            'year': None,  # Will be extracted from venue or date
                            'forum_id': forum_id,
                            'pdf_url': f"{self.BASE_URL}/pdf?id={forum_id}",
                            'supplementary': [],
                            'openreview_url': forum_url
                        }
                        
                        # Try to extract year
                        if venue:
                            year_match = re.search(r'20\d{2}', venue)
                            if year_match:
                                metadata['year'] = int(year_match.group())
                        
                        return metadata
                except json.JSONDecodeError:
                    logger.error("Failed to parse __NEXT_DATA__ JSON")
            
            # Final fallback: Extract basic info from meta tags
            title_meta = soup.find('meta', property='og:title')
            title = title_meta.get('content', 'Untitled') if title_meta else 'Untitled'
            
            return {
                'title': title,
                'authors': [],
                'abstract': '',
                'keywords': [],
                'venue': '',
                'year': None,
                'forum_id': forum_id,
                'pdf_url': f"{self.BASE_URL}/pdf?id={forum_id}",
                'supplementary': [],
                'openreview_url': forum_url
            }
            
        except Exception as e:
            logger.error(f"Error scraping OpenReview forum page: {e}")
            return None
    
    def download_pdf(self, pdf_url: str, save_path: Path) -> bool:
        """
        Download PDF from OpenReview
        
        Args:
            pdf_url: URL to the PDF
            save_path: Path where to save the PDF
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.get(pdf_url, timeout=30, stream=True)
            
            if response.status_code == 200:
                # Ensure directory exists
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write PDF content
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info(f"PDF saved to: {save_path}")
                return True
            else:
                logger.error(f"Failed to download PDF: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return False
    
    def generate_bibtex(self, metadata: Dict[str, Any]) -> str:
        """
        Generate BibTeX citation from metadata
        
        Args:
            metadata: Paper metadata dictionary
            
        Returns:
            BibTeX string
        """
        # If BibTeX is already provided by OpenReview, use it
        if metadata.get('bibtex'):
            return metadata['bibtex']
        
        # Otherwise, generate citation key
        first_author = metadata['authors'][0].split()[-1] if metadata['authors'] else 'Unknown'
        year = metadata.get('year', datetime.now(timezone.utc).year)
        title_words = metadata['title'].split()[:2]
        citation_key = f"{first_author}{year}{''.join(title_words)}"
        citation_key = re.sub(r'[^a-zA-Z0-9]', '', citation_key)
        
        # Build BibTeX entry
        bibtex = f"@inproceedings{{{citation_key},\n"
        bibtex += f"  title = {{{metadata['title']}}},\n"
        
        if metadata['authors']:
            authors_str = ' and '.join(metadata['authors'])
            bibtex += f"  author = {{{authors_str}}},\n"
        
        if metadata.get('venue'):
            bibtex += f"  booktitle = {{{metadata['venue']}}},\n"
        
        if metadata.get('year'):
            bibtex += f"  year = {{{metadata['year']}}},\n"
        
        bibtex += f"  url = {{{metadata['openreview_url']}}},\n"
        
        if metadata.get('abstract'):
            # Escape special characters in abstract
            abstract = metadata['abstract'].replace('{', '\\{').replace('}', '\\}')
            bibtex += f"  abstract = {{{abstract}}},\n"
        
        if metadata.get('keywords'):
            keywords_str = ', '.join(metadata['keywords'])
            bibtex += f"  keywords = {{{keywords_str}}},\n"
        
        bibtex += "}\n"
        
        return bibtex
    
    def import_paper(self, url: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Import a paper from OpenReview
        
        Args:
            url: OpenReview URL
            tags: Optional list of tags to add
            
        Returns:
            Dictionary with import results
        """
        try:
            # Extract forum ID
            forum_id = self.extract_forum_id_from_url(url)
            if not forum_id:
                return {
                    'success': False,
                    'error': 'Invalid OpenReview URL. Could not extract forum ID.'
                }
            
            # Fetch metadata
            metadata = self.fetch_paper_metadata(forum_id)
            if not metadata:
                return {
                    'success': False,
                    'error': 'Failed to fetch paper metadata from OpenReview'
                }
            
            # Generate filename for PDF
            safe_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', metadata['title'])[:50]
            pdf_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{forum_id}_{safe_title}.pdf"
            pdf_path = Path('data/papers') / pdf_filename
            
            # Download PDF if URL is available
            if metadata.get('pdf_url'):
                pdf_downloaded = self.download_pdf(metadata['pdf_url'], pdf_path)
                if pdf_downloaded:
                    metadata['pdf_path'] = str(pdf_path)
                else:
                    logger.warning("PDF download failed, continuing without PDF")
            
            # Generate BibTeX
            metadata['bibtex'] = self.generate_bibtex(metadata)
            
            # Add tags if provided
            if tags:
                metadata['tags'] = tags
            
            return {
                'success': True,
                'metadata': metadata,
                'forum_id': forum_id
            }
            
        except Exception as e:
            logger.error(f"Error importing OpenReview paper: {e}")
            return {
                'success': False,
                'error': str(e)
            }