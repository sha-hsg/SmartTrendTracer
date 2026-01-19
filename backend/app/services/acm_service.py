"""
ACM Digital Library integration service
Handles paper metadata extraction and PDF downloads from dl.acm.org
"""
import logging
import re
from typing import Dict, Any, Optional, List
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import bibtexparser
from bibtexparser.bparser import BibTexParser
from pathlib import Path

logger = logging.getLogger(__name__)

class ACMService:
    """Service for importing papers from ACM Digital Library"""
    
    BASE_URL = "https://dl.acm.org"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin'
        })
        # Enable cookies to handle session management
        self.session.cookies.clear()
    
    def extract_doi_from_url(self, url: str) -> Optional[str]:
        """
        Extract DOI from ACM URL
        
        Args:
            url: ACM URL (e.g., https://dl.acm.org/doi/10.1145/3677389.3702588)
            
        Returns:
            DOI string or None
        """
        # Pattern for ACM DOI URLs
        doi_pattern = r'(?:doi(?:/|%2F)|\.org/)?(10\.\d{4,}/[-._;()/:\w]+)'
        match = re.search(doi_pattern, url)
        if match:
            return match.group(1)
        return None
    
    def fetch_bibtex(self, doi: str) -> Optional[str]:
        """
        Fetch BibTeX citation from ACM
        
        Args:
            doi: DOI identifier (e.g., "10.1145/3677389.3702588")
            
        Returns:
            BibTeX string or None
        """
        try:
            # Try the direct citation download endpoint first
            citation_url = f"{self.BASE_URL}/action/showCitFormats"
            params = {'doi': doi}
            
            # Add referer header to avoid 403
            headers = self.session.headers.copy()
            headers['Referer'] = f"{self.BASE_URL}/doi/{doi}"
            
            response = self.session.get(citation_url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                # Parse the citation formats page to get the download link
                soup = BeautifulSoup(response.text, 'html.parser')
                # Look for BibTeX download link
                bibtex_link = None
                for link in soup.find_all('a', href=True):
                    if 'format=bibtex' in link['href'].lower():
                        bibtex_link = link['href']
                        break
                
                if bibtex_link:
                    if not bibtex_link.startswith('http'):
                        bibtex_link = f"{self.BASE_URL}{bibtex_link}"
                    
                    # Download the BibTeX
                    bibtex_response = self.session.get(bibtex_link, headers=headers, timeout=15)
                    if bibtex_response.status_code == 200:
                        # Sometimes BibTeX is in a download attachment
                        content = bibtex_response.text.strip()
                        if content.startswith('@'):
                            return content
                        # Try to extract from HTML if wrapped
                        soup = BeautifulSoup(content, 'html.parser')
                        pre_tag = soup.find('pre')
                        if pre_tag and pre_tag.text.strip().startswith('@'):
                            return pre_tag.text.strip()
            
            # Alternative: Try citation export endpoint
            export_url = f"{self.BASE_URL}/action/downloadCitation"
            data = {
                'format': 'bibtex',
                'doi': doi,
                'include': 'abs',
                'direct': 'true',
                'submit': 'Download'
            }
            
            response = self.session.post(export_url, data=data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                content = response.text.strip()
                if content.startswith('@'):
                    return content
                # Check if it's wrapped in HTML
                soup = BeautifulSoup(content, 'html.parser')
                pre_tag = soup.find('pre')
                if pre_tag and pre_tag.text.strip().startswith('@'):
                    return pre_tag.text.strip()
                # Sometimes it's in a textarea
                textarea = soup.find('textarea')
                if textarea and textarea.text.strip().startswith('@'):
                    return textarea.text.strip()
            
            logger.warning(f"Could not fetch BibTeX for DOI: {doi}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching BibTeX: {e}")
            return None
    
    def parse_bibtex(self, bibtex_str: str) -> Dict[str, Any]:
        """
        Parse BibTeX string to extract metadata
        
        Args:
            bibtex_str: BibTeX citation string
            
        Returns:
            Dictionary with paper metadata
        """
        try:
            parser = BibTexParser(common_strings=True)
            parser.customization = lambda record: record
            bib_database = bibtexparser.loads(bibtex_str, parser=parser)
            
            if not bib_database.entries:
                return {}
            
            entry = bib_database.entries[0]
            
            # Extract metadata
            metadata = {
                'title': entry.get('title', '').strip('{}'),
                'authors': self._parse_authors(entry.get('author', '')),
                'year': entry.get('year', ''),
                'venue': entry.get('booktitle', entry.get('journal', '')).strip('{}'),
                'publisher': entry.get('publisher', '').strip('{}'),
                'pages': entry.get('pages', ''),
                'doi': entry.get('doi', ''),
                'abstract': entry.get('abstract', '').strip('{}'),
                'keywords': entry.get('keywords', '').strip('{}'),
                'series': entry.get('series', '').strip('{}'),
                'volume': entry.get('volume', ''),
                'number': entry.get('number', ''),
                'month': entry.get('month', ''),
                'isbn': entry.get('isbn', ''),
                'url': entry.get('url', ''),
                'bibtex_type': entry.get('ENTRYTYPE', 'article')
            }
            
            # Clean up empty fields
            metadata = {k: v for k, v in metadata.items() if v}
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error parsing BibTeX: {e}")
            return {}
    
    def _parse_authors(self, authors_str: str) -> str:
        """
        Parse BibTeX author string
        
        Args:
            authors_str: BibTeX author string with "and" separators
            
        Returns:
            Comma-separated author names
        """
        if not authors_str:
            return ''
        
        # Split by "and" and clean up
        authors = authors_str.split(' and ')
        cleaned_authors = []
        
        for author in authors:
            author = author.strip()
            # Handle "Last, First" format
            if ',' in author:
                parts = author.split(',')
                if len(parts) == 2:
                    author = f"{parts[1].strip()} {parts[0].strip()}"
            cleaned_authors.append(author)
        
        return ', '.join(cleaned_authors)
    
    def fetch_metadata_from_page(self, doi: str) -> Dict[str, Any]:
        """
        Fetch metadata by scraping the ACM paper page or using CrossRef API as fallback
        
        Args:
            doi: DOI identifier
            
        Returns:
            Dictionary with paper metadata
        """
        metadata = {}
        
        # First try CrossRef API (more reliable and doesn't require scraping)
        try:
            crossref_url = f"https://api.crossref.org/works/{doi}"
            response = requests.get(crossref_url, timeout=10)
            if response.status_code == 200:
                data = response.json().get('message', {})
                
                # Extract title
                if 'title' in data and data['title']:
                    metadata['title'] = data['title'][0]
                
                # Extract authors
                if 'author' in data:
                    authors = []
                    for author in data['author']:
                        name_parts = []
                        if 'given' in author:
                            name_parts.append(author['given'])
                        if 'family' in author:
                            name_parts.append(author['family'])
                        if name_parts:
                            authors.append(' '.join(name_parts))
                    if authors:
                        metadata['authors'] = ', '.join(authors)
                
                # Extract abstract
                if 'abstract' in data:
                    metadata['abstract'] = data['abstract']
                
                # Extract year
                if 'published-print' in data:
                    metadata['year'] = str(data['published-print']['date-parts'][0][0])
                elif 'published-online' in data:
                    metadata['year'] = str(data['published-online']['date-parts'][0][0])
                
                # Extract venue/conference
                if 'container-title' in data and data['container-title']:
                    metadata['venue'] = data['container-title'][0]
                
                # Extract publisher
                if 'publisher' in data:
                    metadata['publisher'] = data['publisher']
                
                # Extract pages
                if 'page' in data:
                    metadata['pages'] = data['page']
                
                # Extract volume and issue
                if 'volume' in data:
                    metadata['volume'] = data['volume']
                if 'issue' in data:
                    metadata['number'] = data['issue']
                
                metadata['doi'] = doi
                metadata['url'] = f"{self.BASE_URL}/doi/{doi}"
                
                if metadata.get('title'):
                    logger.info(f"Successfully fetched metadata from CrossRef for DOI: {doi}")
                    return metadata
        except Exception as e:
            logger.warning(f"CrossRef API failed: {e}")
        
        # Fallback to page scraping with better error handling
        try:
            paper_url = f"{self.BASE_URL}/doi/{doi}"
            headers = self.session.headers.copy()
            headers['Referer'] = self.BASE_URL
            
            response = self.session.get(paper_url, headers=headers, timeout=15)
            
            # Even if we get 403, we can still try to extract from meta tags
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try meta tags first (often available even on error pages)
            meta_mappings = {
                'citation_title': 'title',
                'citation_author': 'authors',
                'citation_publication_date': 'year',
                'citation_journal_title': 'venue',
                'citation_conference_title': 'venue',
                'citation_abstract': 'abstract',
                'citation_doi': 'doi',
                'DC.Title': 'title',
                'DC.Creator': 'authors',
                'DC.Date': 'year',
                'DC.Description': 'abstract'
            }
            
            authors_list = []
            for meta_name, field in meta_mappings.items():
                meta_tags = soup.find_all('meta', {'name': meta_name})
                if not meta_tags:
                    meta_tags = soup.find_all('meta', {'property': meta_name})
                
                for meta in meta_tags:
                    content = meta.get('content', '').strip()
                    if content:
                        if field == 'authors':
                            authors_list.append(content)
                        elif field == 'year' and not metadata.get('year'):
                            year_match = re.search(r'\b(19|20)\d{2}\b', content)
                            if year_match:
                                metadata['year'] = year_match.group()
                        elif not metadata.get(field):
                            metadata[field] = content
            
            if authors_list:
                metadata['authors'] = ', '.join(authors_list)
            
            # If we still don't have a title, try common HTML elements
            if not metadata.get('title'):
                # Try various selectors
                selectors = [
                    'h1.citation__title',
                    'h1[property="name"]',
                    'h1[itemprop="name"]',
                    '.title-text',
                    'h1'
                ]
                for selector in selectors:
                    elem = soup.select_one(selector)
                    if elem and elem.text.strip():
                        metadata['title'] = elem.text.strip()
                        break
            
            metadata['doi'] = doi
            metadata['url'] = paper_url
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error fetching metadata from page: {e}")
            return {'doi': doi, 'url': f"{self.BASE_URL}/doi/{doi}"}
    
    def download_pdf(self, doi: str, save_path: Path) -> bool:
        """
        Download PDF from ACM
        
        Args:
            doi: DOI identifier
            save_path: Path to save the PDF
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # ACM PDF URL format
            pdf_url = f"{self.BASE_URL}/doi/pdf/{doi}"
            
            logger.info(f"Downloading PDF from: {pdf_url}")
            response = self.session.get(pdf_url, timeout=30, stream=True)
            
            # Check for common access restriction status codes
            if response.status_code == 403:
                logger.error(f"PDF access forbidden (403). This paper likely requires institutional access or subscription to ACM Digital Library for DOI: {doi}")
                return False
            elif response.status_code == 401:
                logger.error(f"PDF access requires authentication (401) for DOI: {doi}")
                return False
            elif response.status_code != 200:
                logger.error(f"HTTP {response.status_code} when accessing PDF for DOI: {doi}")
                return False
            
            # Check if we got a PDF or a redirect/HTML page
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"Response is not a PDF. Content-Type: {content_type}")
                # Try to follow redirects or handle access requirements
                if 'html' in content_type.lower():
                    # Parse HTML to find actual PDF link
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Look for PDF download link with various selectors
                    pdf_link = (
                        soup.find('a', {'title': 'PDF'}) or 
                        soup.find('a', text=re.compile(r'PDF', re.I)) or
                        soup.find('a', href=re.compile(r'\.pdf$', re.I)) or
                        soup.find('a', class_=re.compile(r'pdf', re.I))
                    )
                    if pdf_link and pdf_link.get('href'):
                        new_pdf_url = pdf_link['href']
                        if not new_pdf_url.startswith('http'):
                            new_pdf_url = f"{self.BASE_URL}{new_pdf_url}"
                        logger.info(f"Found PDF link, trying: {new_pdf_url}")
                        response = self.session.get(new_pdf_url, timeout=30, stream=True)
                        content_type = response.headers.get('Content-Type', '')
                    
                    # If we still don't have a PDF, check if it's an access issue
                    if 'pdf' not in content_type.lower():
                        if 'login' in response.text.lower() or 'sign in' in response.text.lower():
                            logger.error(f"PDF access requires authentication/institutional access for DOI: {doi}")
                        else:
                            logger.error(f"Could not find valid PDF. Final content type: {content_type}")
                        return False
            
            if response.status_code == 200 and 'pdf' in content_type.lower():
                # Save PDF
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info(f"PDF saved to: {save_path}")
                return True
            else:
                logger.error(f"Failed to download PDF. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return False
    
    def import_paper(self, url: str, save_dir: Path) -> Dict[str, Any]:
        """
        Import a paper from ACM URL
        
        Args:
            url: ACM paper URL
            save_dir: Directory to save the PDF
            
        Returns:
            Dictionary with paper data and file path
        """
        try:
            # Extract DOI from URL
            doi = self.extract_doi_from_url(url)
            if not doi:
                raise ValueError(f"Could not extract DOI from URL: {url}")
            
            logger.info(f"Extracted DOI: {doi}")
            
            # Try to fetch BibTeX first (most reliable)
            bibtex = self.fetch_bibtex(doi)
            if bibtex:
                metadata = self.parse_bibtex(bibtex)
                metadata['bibtex'] = bibtex
            else:
                # Fallback to page scraping
                metadata = self.fetch_metadata_from_page(doi)
            
            if not metadata.get('title'):
                raise ValueError("Could not extract paper title")
            
            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_title = re.sub(r'[^\w\s-]', '', metadata['title'])[:50]
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            filename = f"{timestamp}_{safe_title}.pdf"
            pdf_path = save_dir / filename
            
            # Download PDF
            pdf_success = self.download_pdf(doi, pdf_path)
            
            # Prepare return data
            paper_data = {
                'title': metadata.get('title', ''),
                'authors': metadata.get('authors', ''),
                'abstract': metadata.get('abstract', ''),
                'pdf_path': str(pdf_path) if pdf_success else None,
                'pdf_url': f"{self.BASE_URL}/doi/pdf/{doi}",
                'doi': doi,
                'year': metadata.get('year', ''),
                'venue': metadata.get('venue', ''),
                'conference': metadata.get('venue', ''),
                'journal': metadata.get('journal', ''),
                'publisher': metadata.get('publisher', 'ACM'),
                'pages': metadata.get('pages', ''),
                'volume': metadata.get('volume', ''),
                'number': metadata.get('number', ''),
                'keywords': metadata.get('keywords', ''),
                'bibtex': metadata.get('bibtex', ''),
                'source': 'acm',
                'source_url': url
            }
            
            # Clean up empty fields
            paper_data = {k: v for k, v in paper_data.items() if v}
            
            return paper_data
            
        except Exception as e:
            logger.error(f"Error importing ACM paper: {e}")
            raise


# Singleton instance
acm_service = ACMService()