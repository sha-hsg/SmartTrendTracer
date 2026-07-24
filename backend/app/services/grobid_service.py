"""
GROBID Service for extracting structured metadata from PDFs
Uses the HuggingFace GROBID Space for processing
"""
import os
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.services.grobid_helpers import (
    parse_bibtex,
    parse_header_xml,
    extract_references,
    extract_sections,
    parse_citations,
    extract_conclusion,
)

logger = logging.getLogger(__name__)

class GROBIDService:
    """Service for extracting structured metadata using GROBID"""

    def __init__(self):
        # Using the HuggingFace GROBID Space
        self.grobid_url = "https://kermitt2-grobid.hf.space"
        self.timeout = 60  # seconds

    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process a PDF file with GROBID to extract structured metadata

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing extracted metadata, TEI XML, and references
        """
        try:
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file not found: {pdf_path}")
                return {
                    'success': False,
                    'error': 'PDF file not found'
                }

            # Process header first (for quick metadata extraction)
            header_result = self._process_header(pdf_path)

            # Process full document (for complete TEI and references)
            full_result = self._process_full_document(pdf_path)

            # Process citations
            citations_result = self._process_citations(pdf_path)

            # Combine results
            result = {
                'success': True,
                'header': header_result,
                'full_document': full_result,
                'citations': citations_result,
                'processed_at': datetime.now(timezone.utc).isoformat()
            }

            # Extract structured data
            if header_result.get('success'):
                result['metadata'] = self._parse_header_xml(header_result.get('tei_xml', ''))

            if full_result.get('success'):
                result['references'] = self._extract_references(full_result.get('tei_xml', ''))
                result['sections'] = self._extract_sections(full_result.get('tei_xml', ''))

            if citations_result.get('success'):
                result['citation_contexts'] = self._parse_citations(citations_result.get('tei_xml', ''))

            return result

        except Exception as e:
            logger.error(f"Error processing PDF with GROBID: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _process_header(self, pdf_path: str) -> Dict[str, Any]:
        """Process PDF header to extract basic metadata"""
        try:
            url = f"{self.grobid_url}/api/processHeaderDocument"

            # Check if GROBID is accessible
            try:
                test_response = requests.get(self.grobid_url, timeout=2)
            except requests.exceptions.ConnectionError:
                logger.error(f"GROBID service is not running at {self.grobid_url}")
                return {
                    'success': False,
                    'error': f'GROBID service is not running. Please start GROBID at {self.grobid_url}'
                }

            with open(pdf_path, 'rb') as f:
                files = {'input': f}
                response = requests.post(
                    url,
                    files=files,
                    timeout=self.timeout
                )

            if response.status_code == 200:
                return {
                    'success': True,
                    'tei_xml': response.text
                }
            else:
                logger.error(f"GROBID header processing failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }

        except requests.RequestException as e:
            logger.error(f"Request error in header processing: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _process_full_document(self, pdf_path: str) -> Dict[str, Any]:
        """Process full PDF document to extract complete TEI"""
        try:
            url = f"{self.grobid_url}/api/processFulltextDocument"

            # Check if GROBID is accessible
            try:
                test_response = requests.get(self.grobid_url, timeout=2)
            except requests.exceptions.ConnectionError:
                logger.error(f"GROBID service is not running at {self.grobid_url}")
                return {
                    'success': False,
                    'error': f'GROBID service is not running. Please start GROBID at {self.grobid_url}'
                }

            with open(pdf_path, 'rb') as f:
                files = {'input': f}
                data = {
                    'consolidateHeader': '1',
                    'consolidateCitations': '1',
                    'includeRawCitations': '1',
                    'includeRawAffiliations': '1'
                }
                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    timeout=self.timeout * 2  # Longer timeout for full processing
                )

            if response.status_code == 200:
                return {
                    'success': True,
                    'tei_xml': response.text
                }
            else:
                logger.error(f"GROBID full document processing failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }

        except requests.RequestException as e:
            logger.error(f"Request error in full document processing: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _process_citations(self, pdf_path: str) -> Dict[str, Any]:
        """Process citations in the PDF"""
        # Note: processCitationList expects raw citation strings, not PDFs
        # Citations are already extracted in the full document processing
        # So we'll just return a placeholder here
        return {
            'success': True,
            'tei_xml': '',
            'note': 'Citations are extracted from full document processing'
        }

    # ------------------------------------------------------------------
    # Delegate parsing to grobid_helpers (preserving method signatures)
    # ------------------------------------------------------------------

    def _parse_bibtex(self, bibtex_str: str) -> Dict[str, Any]:
        """Parse BibTeX format metadata from GROBID"""
        return parse_bibtex(bibtex_str)

    def _parse_header_xml(self, tei_xml: str) -> Dict[str, Any]:
        """Parse TEI header XML or BibTeX to extract metadata"""
        return parse_header_xml(tei_xml)

    def _extract_references(self, tei_xml: str) -> List[Dict[str, Any]]:
        """Extract references from TEI XML"""
        return extract_references(tei_xml)

    def _extract_sections(self, tei_xml: str) -> List[Dict[str, Any]]:
        """Extract document sections from TEI XML"""
        return extract_sections(tei_xml)

    def _parse_citations(self, tei_xml: str) -> List[Dict[str, Any]]:
        """Parse citation contexts from TEI XML"""
        return parse_citations(tei_xml)

    def extract_conclusion(self, tei_xml: str) -> Optional[Dict[str, str]]:
        """
        Extract conclusion section from TEI XML

        Args:
            tei_xml: TEI XML content

        Returns:
            Dict with title and content of conclusion, or None if not found
        """
        return extract_conclusion(tei_xml)

    def save_tei_xml(self, tei_xml: str, output_path: str) -> bool:
        """
        Save TEI XML to file

        Args:
            tei_xml: TEI XML content
            output_path: Path to save the XML file

        Returns:
            Success boolean
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(tei_xml)
            logger.info(f"TEI XML saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving TEI XML: {e}")
            return False
