"""
ArXiv Import Service
Handles importing papers directly from ArXiv URLs
"""

import re
import os
import logging
import requests
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class ArXivImportService:
    """Service for importing papers from ArXiv"""
    
    # ArXiv URL patterns (ordered for proper matching)
    ARXIV_PATTERNS = [
        r'(?:https?://)?arxiv\.org/abs/(\d{4}\.\d{4,5}(?:v\d+)?)',  # New format: 2301.12345
        r'(?:https?://)?arxiv\.org/abs/([a-zA-Z\-\.]+/\d{7}(?:v\d+)?)',  # Old format: cs.AI/0701123
        r'(?:https?://)?arxiv\.org/pdf/(\d{4}\.\d{4,5}(?:v\d+)?)',  # PDF URL new
        r'(?:https?://)?arxiv\.org/pdf/([a-zA-Z\-\.]+/\d{7}(?:v\d+)?)',  # PDF URL old
    ]
    
    # ArXiv API base URL
    ARXIV_API_BASE = "http://export.arxiv.org/api/query"
    
    def __init__(self):
        """Initialize ArXiv import service"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SmartTrendTracer/1.0 (https://github.com/smarttrendtracer)'
        })
        logger.info("ArXiv Import Service initialized")
    
    def extract_arxiv_id(self, url_or_id: str) -> Optional[str]:
        """
        Extract ArXiv ID from URL or validate ID
        
        Supports:
        - Direct IDs: "2301.12345", "cs.AI/0701123"
        - Abstract URLs: "https://arxiv.org/abs/2301.12345"
        - PDF URLs: "https://arxiv.org/pdf/2301.12345"
        - With version: "2301.12345v2"
        
        Args:
            url_or_id: ArXiv URL or ID
        
        Returns:
            ArXiv ID or None if invalid
        """
        # Clean input
        url_or_id = url_or_id.strip()
        
        # If it's already just an ID, validate it
        if re.match(r'^\d{4}\.\d{4,5}(?:v\d+)?$', url_or_id):
            logger.debug(f"Detected direct ArXiv ID (new format): {url_or_id}")
            return url_or_id
        if re.match(r'^[a-zA-Z\-\.]+/\d{7}(?:v\d+)?$', url_or_id):
            logger.debug(f"Detected direct ArXiv ID (old format): {url_or_id}")
            return url_or_id
        
        # Try to extract from URL
        for pattern in self.ARXIV_PATTERNS:
            match = re.search(pattern, url_or_id)
            if match:
                arxiv_id = match.group(1)
                # Determine URL type for logging
                if '/pdf/' in url_or_id:
                    logger.debug(f"Extracted ArXiv ID from PDF URL: {arxiv_id}")
                elif '/abs/' in url_or_id:
                    logger.debug(f"Extracted ArXiv ID from abstract URL: {arxiv_id}")
                else:
                    logger.debug(f"Extracted ArXiv ID from URL: {arxiv_id}")
                return arxiv_id
        
        logger.warning(f"Could not extract ArXiv ID from: {url_or_id}")
        return None
    
    def fetch_metadata(self, arxiv_id: str) -> Optional[Dict]:
        """
        Fetch paper metadata from ArXiv API
        
        Args:
            arxiv_id: ArXiv paper ID
        
        Returns:
            Dictionary with paper metadata or None if failed
        """
        try:
            # Query ArXiv API
            params = {
                'id_list': arxiv_id,
                'max_results': 1
            }
            
            logger.info(f"Fetching metadata for ArXiv ID: {arxiv_id}")

            # Retry logic with increasing timeouts (ArXiv can be slow)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    timeout = 45 + (attempt * 15)  # 45s, 60s, 75s
                    response = self.session.get(self.ARXIV_API_BASE, params=params, timeout=timeout)
                    response.raise_for_status()
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"ArXiv API attempt {attempt + 1} failed, retrying: {e}")
                        import time
                        time.sleep(2)  # Brief pause before retry
                    else:
                        raise
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Find the entry
            ns = {'atom': 'http://www.w3.org/2005/Atom', 
                  'arxiv': 'http://arxiv.org/schemas/atom'}
            entry = root.find('.//atom:entry', ns)
            
            if entry is None:
                logger.error(f"No entry found for ArXiv ID: {arxiv_id}")
                return None
            
            # Extract metadata
            metadata = {
                'arxiv_id': arxiv_id,
                'title': entry.find('atom:title', ns).text.strip().replace('\n', ' '),
                'abstract': entry.find('atom:summary', ns).text.strip(),
                'authors': [],
                'published': None,
                'updated': None,
                'categories': [],
                'pdf_url': f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                'abs_url': f"https://arxiv.org/abs/{arxiv_id}",
                'comment': None,
                'journal_ref': None,
                'doi': None
            }
            
            # Extract authors
            for author in entry.findall('atom:author', ns):
                name = author.find('atom:name', ns)
                if name is not None:
                    metadata['authors'].append(name.text.strip())
            
            # Extract dates
            published = entry.find('atom:published', ns)
            if published is not None:
                metadata['published'] = published.text
            
            updated = entry.find('atom:updated', ns)
            if updated is not None:
                metadata['updated'] = updated.text
            
            # Extract categories
            for category in entry.findall('atom:category', ns):
                term = category.get('term')
                if term:
                    metadata['categories'].append(term)
            
            # Extract comment (often contains page count, conference info)
            comment = entry.find('arxiv:comment', ns)
            if comment is not None:
                metadata['comment'] = comment.text.strip()
            
            # Extract journal reference
            journal_ref = entry.find('arxiv:journal_ref', ns)
            if journal_ref is not None:
                metadata['journal_ref'] = journal_ref.text.strip()
            
            # Extract DOI
            doi = entry.find('arxiv:doi', ns)
            if doi is not None:
                metadata['doi'] = doi.text.strip()
            
            logger.info(f"Successfully fetched metadata for: {metadata['title']}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to fetch metadata for {arxiv_id}: {e}")
            return None
    
    def download_pdf(self, arxiv_id: str, output_dir: Optional[str] = None) -> Optional[str]:
        """
        Download PDF from ArXiv
        
        Args:
            arxiv_id: ArXiv paper ID
            output_dir: Directory to save PDF (uses data/papers if None)
        
        Returns:
            Path to downloaded PDF or None if failed
        """
        try:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            logger.info(f"Downloading PDF from: {pdf_url}")
            response = self.session.get(pdf_url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Determine output path - use permanent directory by default
            if output_dir:
                output_path = Path(output_dir)
            else:
                # Use permanent data/papers directory instead of temp
                output_path = Path("data/papers")
            
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create filename from ID
            safe_id = arxiv_id.replace('/', '_')
            pdf_path = output_path / f"arxiv_{safe_id}.pdf"
            
            # Download file
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded PDF to: {pdf_path}")
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"Failed to download PDF for {arxiv_id}: {e}")
            return None
    
    def import_paper(self, url_or_id: str, download_dir: Optional[str] = None) -> Dict:
        """
        Import a paper from ArXiv
        
        Args:
            url_or_id: ArXiv URL or ID
            download_dir: Directory to save PDF
        
        Returns:
            Dictionary with import results
        """
        result = {
            'success': False,
            'arxiv_id': None,
            'metadata': None,
            'pdf_path': None,
            'error': None
        }
        
        # Extract ArXiv ID
        arxiv_id = self.extract_arxiv_id(url_or_id)
        if not arxiv_id:
            result['error'] = f"Invalid ArXiv URL or ID: {url_or_id}"
            logger.error(result['error'])
            return result
        
        result['arxiv_id'] = arxiv_id
        
        # Fetch metadata
        metadata = self.fetch_metadata(arxiv_id)
        if not metadata:
            result['error'] = f"Failed to fetch metadata for {arxiv_id}"
            return result
        
        result['metadata'] = metadata
        
        # Download PDF
        pdf_path = self.download_pdf(arxiv_id, download_dir)
        if not pdf_path:
            result['error'] = f"Failed to download PDF for {arxiv_id}"
            return result
        
        result['pdf_path'] = pdf_path
        result['success'] = True
        
        logger.info(f"Successfully imported ArXiv paper: {metadata['title']}")
        return result
    
    def search_papers(self, query: str, max_results: int = 10) -> Optional[list]:
        """
        Search for papers on ArXiv
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of paper metadata or None if failed
        """
        try:
            params = {
                'search_query': query,
                'max_results': max_results,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            logger.info(f"Searching ArXiv for: {query}")
            response = self.session.get(self.ARXIV_API_BASE, params=params, timeout=60)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Extract entries
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('.//atom:entry', ns)
            
            papers = []
            for entry in entries:
                # Extract ID from entry ID URL
                id_url = entry.find('atom:id', ns).text
                arxiv_id = id_url.split('/abs/')[-1]
                
                paper = {
                    'arxiv_id': arxiv_id,
                    'title': entry.find('atom:title', ns).text.strip().replace('\n', ' '),
                    'summary': entry.find('atom:summary', ns).text.strip()[:200] + '...',
                    'authors': [],
                    'published': entry.find('atom:published', ns).text,
                    'pdf_url': f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                    'abs_url': f"https://arxiv.org/abs/{arxiv_id}"
                }
                
                # Extract authors
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns)
                    if name is not None:
                        paper['authors'].append(name.text.strip())
                
                papers.append(paper)
            
            logger.info(f"Found {len(papers)} papers for query: {query}")
            return papers
            
        except Exception as e:
            logger.error(f"Failed to search ArXiv: {e}")
            return None


# Singleton instance
_arxiv_service = None

def get_arxiv_service() -> ArXivImportService:
    """Get or create ArXiv import service singleton"""
    global _arxiv_service
    if _arxiv_service is None:
        _arxiv_service = ArXivImportService()
    return _arxiv_service