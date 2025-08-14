"""
Service for processing PDF research papers
"""
import os
import re
import hashlib
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import PyPDF2
from pdfplumber import PDF
import logging

logger = logging.getLogger(__name__)

class PaperService:
    def __init__(self, storage_path: str = "data/papers"):
        """Initialize the paper service with storage path"""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def extract_text_from_pdf(self, pdf_path: str) -> Dict:
        """
        Extract text and metadata from a PDF file
        
        Returns:
            Dict containing:
            - content: Full text content
            - title: Extracted title (if found)
            - abstract: Extracted abstract (if found)
            - page_count: Number of pages
            - metadata: PDF metadata
        """
        result = {
            "content": "",
            "title": None,
            "abstract": None,
            "page_count": 0,
            "metadata": {},
            "sections": []
        }
        
        try:
            # Try with pdfplumber first (better text extraction)
            with PDF.open(pdf_path) as pdf:
                # Extract metadata
                if pdf.metadata:
                    result["metadata"] = {
                        "title": pdf.metadata.get('Title'),
                        "author": pdf.metadata.get('Author'),
                        "subject": pdf.metadata.get('Subject'),
                        "creator": pdf.metadata.get('Creator'),
                        "producer": pdf.metadata.get('Producer'),
                        "creation_date": pdf.metadata.get('CreationDate'),
                        "mod_date": pdf.metadata.get('ModDate'),
                    }
                
                # Extract text from all pages
                text_pages = []
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_pages.append(page_text)
                        
                result["page_count"] = len(pdf.pages)
                result["content"] = "\n\n".join(text_pages)
                
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying PyPDF2: {e}")
            
            # Fallback to PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    # Extract metadata
                    if pdf_reader.metadata:
                        result["metadata"] = {
                            "title": pdf_reader.metadata.get('/Title'),
                            "author": pdf_reader.metadata.get('/Author'),
                            "subject": pdf_reader.metadata.get('/Subject'),
                            "creator": pdf_reader.metadata.get('/Creator'),
                            "producer": pdf_reader.metadata.get('/Producer'),
                        }
                    
                    # Extract text
                    text_pages = []
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        if text:
                            text_pages.append(text)
                    
                    result["page_count"] = len(pdf_reader.pages)
                    result["content"] = "\n\n".join(text_pages)
                    
            except Exception as e:
                logger.error(f"Failed to extract text from PDF: {e}")
                raise
        
        # Try to extract title and abstract from content
        if result["content"]:
            result["title"] = self._extract_title(result["content"], result["metadata"].get("title"))
            result["abstract"] = self._extract_abstract(result["content"])
            result["sections"] = self._extract_sections(result["content"])
        
        return result
    
    def _extract_title(self, content: str, metadata_title: Optional[str] = None) -> Optional[str]:
        """Extract paper title from content"""
        if metadata_title:
            return metadata_title
            
        # Look for title in first few lines
        lines = content.split('\n')[:20]
        
        # Common patterns for titles
        for line in lines:
            line = line.strip()
            # Title is often the longest line in the beginning
            if len(line) > 10 and len(line) < 200:
                # Check if it doesn't contain common non-title elements
                if not any(word in line.lower() for word in ['abstract', 'introduction', 'keywords', '@', 'university', 'department']):
                    # Check if it's mostly title case or all caps
                    if line.isupper() or (sum(1 for c in line if c.isupper()) / len(line) > 0.3):
                        return line.title() if line.isupper() else line
        
        # If no title found, use first substantial line
        for line in lines:
            line = line.strip()
            if len(line) > 20:
                return line[:200]  # Limit length
                
        return None
    
    def _extract_abstract(self, content: str) -> Optional[str]:
        """Extract abstract from paper content"""
        content_lower = content.lower()
        
        # Look for abstract section
        abstract_patterns = [
            r'abstract[\s\n]+(.+?)(?:1\.?\s*introduction|\n\s*keywords|1\s+introduction)',
            r'abstract:?\s*\n+(.+?)(?:keywords|introduction|1\.)',
            r'summary[\s\n]+(.+?)(?:1\.?\s*introduction|\n\s*keywords)',
        ]
        
        for pattern in abstract_patterns:
            match = re.search(pattern, content_lower, re.DOTALL | re.IGNORECASE)
            if match:
                abstract = match.group(1)
                # Clean up the abstract
                abstract = re.sub(r'\s+', ' ', abstract).strip()
                # Limit length
                if len(abstract) > 100 and len(abstract) < 5000:
                    # Get the actual case version
                    start_idx = content_lower.find(match.group(1)[:50])
                    if start_idx != -1:
                        return content[start_idx:start_idx + len(abstract)].strip()
                    return abstract
        
        return None
    
    def _extract_sections(self, content: str) -> List[Dict]:
        """Extract major sections from paper"""
        sections = []
        
        # Common section patterns
        section_patterns = [
            r'(\d+\.?\s*introduction)',
            r'(\d+\.?\s*related\s+work)',
            r'(\d+\.?\s*background)',
            r'(\d+\.?\s*method(?:ology|s)?)',
            r'(\d+\.?\s*approach)',
            r'(\d+\.?\s*experiment(?:s|al)?)',
            r'(\d+\.?\s*result(?:s)?)',
            r'(\d+\.?\s*discussion)',
            r'(\d+\.?\s*conclusion)',
            r'(\d+\.?\s*future\s+work)',
            r'(references)',
            r'(acknowledgment(?:s)?)',
        ]
        
        combined_pattern = '|'.join(section_patterns)
        matches = list(re.finditer(combined_pattern, content, re.IGNORECASE | re.MULTILINE))
        
        for i, match in enumerate(matches):
            section_title = match.group(0).strip()
            start_pos = match.end()
            
            # Find end position (start of next section or end of document)
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)
            
            section_content = content[start_pos:end_pos].strip()
            
            # Determine section type
            section_type = self._classify_section(section_title)
            
            if section_content and len(section_content) > 50:  # Minimum content length
                sections.append({
                    "title": section_title,
                    "type": section_type,
                    "content": section_content[:10000],  # Limit section length
                    "position": i
                })
        
        return sections
    
    def _classify_section(self, title: str) -> str:
        """Classify section type based on title"""
        title_lower = title.lower()
        
        if 'introduction' in title_lower:
            return 'introduction'
        elif 'related' in title_lower or 'background' in title_lower:
            return 'background'
        elif 'method' in title_lower or 'approach' in title_lower:
            return 'methods'
        elif 'experiment' in title_lower:
            return 'experiments'
        elif 'result' in title_lower:
            return 'results'
        elif 'discussion' in title_lower:
            return 'discussion'
        elif 'conclusion' in title_lower or 'future' in title_lower:
            return 'conclusion'
        elif 'reference' in title_lower:
            return 'references'
        else:
            return 'other'
    
    def save_pdf_file(self, file_content: bytes, filename: str) -> str:
        """
        Save uploaded PDF file to storage
        
        Returns:
            Path to saved file
        """
        # Generate unique filename using hash
        file_hash = hashlib.md5(file_content).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean filename
        safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        base_name = Path(safe_filename).stem
        extension = Path(safe_filename).suffix or '.pdf'
        
        # Create unique filename
        unique_filename = f"{timestamp}_{file_hash}_{base_name}{extension}"
        file_path = self.storage_path / unique_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return str(file_path)
    
    def extract_metadata_from_filename(self, filename: str) -> Dict:
        """
        Try to extract metadata from filename
        Common patterns: 
        - AuthorYear_Title.pdf
        - Year_Conference_Title.pdf
        - arxiv_id_title.pdf
        """
        metadata = {}
        
        # Remove extension
        name = Path(filename).stem
        
        # Check for arxiv pattern (e.g., 2301.12345v2)
        arxiv_pattern = r'(\d{4}\.\d{4,5}(?:v\d+)?)'
        arxiv_match = re.search(arxiv_pattern, name)
        if arxiv_match:
            metadata['arxiv_id'] = arxiv_match.group(1)
        
        # Check for year
        year_pattern = r'(19|20)\d{2}'
        year_match = re.search(year_pattern, name)
        if year_match:
            metadata['year'] = int(year_match.group(0))
        
        # Check for common conference abbreviations
        conferences = ['icml', 'neurips', 'iclr', 'cvpr', 'acl', 'emnlp', 'naacl', 'eccv', 'iccv', 'aaai', 'ijcai']
        name_lower = name.lower()
        for conf in conferences:
            if conf in name_lower:
                metadata['conference'] = conf.upper()
                break
        
        return metadata
    
    def extract_authors_from_content(self, content: str) -> List[Dict]:
        """Extract author information from paper content"""
        authors = []
        
        # Look for author section in first part of paper
        first_page = content[:3000] if len(content) > 3000 else content
        
        # Common patterns for authors
        # Pattern 1: Names followed by affiliations with numbers/symbols
        # Pattern 2: Names with email addresses
        # Pattern 3: Names in specific author sections
        
        # Simple approach: look for lines with email addresses
        email_pattern = r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[^\n]*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        email_matches = re.finditer(email_pattern, first_page)
        
        for match in email_matches:
            name = match.group(1).strip()
            email = match.group(2).strip()
            
            # Validate name (should have at least first and last name)
            if len(name.split()) >= 2:
                authors.append({
                    "name": name,
                    "email": email,
                    "position": len(authors)
                })
        
        # If no authors found with emails, try other patterns
        if not authors:
            # Look for author names after title and before abstract
            # This is a simplified approach
            lines = first_page.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                # Check if line could be author names (title case, reasonable length)
                if (len(line) > 5 and len(line) < 100 and 
                    not any(word in line.lower() for word in ['abstract', 'introduction', 'keywords', 'university']) and
                    sum(1 for c in line if c.isupper()) >= 2):  # At least 2 capital letters
                    
                    # Split by common separators
                    potential_authors = re.split(r'[,;&]|\sand\s', line)
                    for author in potential_authors:
                        author = author.strip()
                        if len(author.split()) >= 2 and len(author.split()) <= 4:
                            authors.append({
                                "name": author,
                                "email": None,
                                "position": len(authors)
                            })
                    
                    # Don't process too many lines
                    if authors and len(authors) > 0:
                        break
        
        return authors[:10]  # Limit to 10 authors