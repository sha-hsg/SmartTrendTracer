"""
Book PDF/EPUB Processing Service
Extended from async_pdf_processor with book-specific optimizations:
- Longer timeouts (6+ hours for large books)
- Enhanced section-wise processing
- Better handling of book-specific content (TOC, chapters, glossary)
- EPUB native processing support
"""

import os
import asyncio
import logging
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class BookProcessorService:
    def __init__(self):
        """Initialize book processor with extended configuration"""
        self.marker_service_url = os.getenv("MARKER_SERVICE_URL", "http://localhost:8002")
        self.mineru_service_url = os.getenv("MINERU_SERVICE_URL", "http://localhost:8003")

        # Extended timeouts for book processing
        self.marker_timeout = 21600  # 6 hours for large books
        self.mineru_timeout = 18000  # 5 hours for MinerU

        # Book-specific processing options
        self.max_file_size = 500 * 1024 * 1024  # 500MB for large books
        self.enable_chapter_detection = True
        self.enable_toc_extraction = True
        self.enable_glossary_extraction = True

    async def process_book(
        self,
        book_id: str,
        file_path: str,
        file_type: str = "pdf",
        preferred_processor: str = "auto"
    ) -> Dict[str, Any]:
        """
        Process a book file (PDF or EPUB) to extract content and metadata.

        Args:
            book_id: MongoDB ObjectId as string
            file_path: Path to the book file
            file_type: "pdf" or "epub"
            preferred_processor: "marker", "mineru", "epub_native", or "auto"

        Returns:
            Dict containing success status, markdown content, metadata, etc.
        """
        logger.info(f"Starting book processing: {file_path} (type: {file_type})")

        try:
            # Validate file
            if not os.path.exists(file_path):
                return {"success": False, "error": "Book file not found"}

            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.warning(f"Large book file: {file_size / (1024*1024):.1f}MB")

            # Choose processing method
            if file_type == "epub":
                return await asyncio.to_thread(
                    self._process_epub,
                    book_id,
                    file_path
                )
            elif file_type == "pdf":
                return await asyncio.to_thread(
                    self._process_pdf,
                    book_id,
                    file_path,
                    preferred_processor
                )
            else:
                return {"success": False, "error": f"Unsupported file type: {file_type}"}

        except Exception as e:
            logger.error(f"Error processing book {book_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "method_used": None
            }

    def _process_pdf(
        self,
        book_id: str,
        pdf_path: str,
        preferred_processor: str = "auto"
    ) -> Dict[str, Any]:
        """Process PDF book with extended timeouts and book-specific features"""

        # Determine best processor for this book
        if preferred_processor == "auto":
            file_size = os.path.getsize(pdf_path)
            if file_size > 100 * 1024 * 1024:  # > 100MB
                processor = "marker"  # Marker handles large files better
            else:
                processor = "marker"  # Default to Marker for books
        else:
            processor = preferred_processor

        if processor == "marker":
            return self._process_with_marker(book_id, pdf_path)
        elif processor == "mineru":
            return self._process_with_mineru(book_id, pdf_path)
        else:
            return {"success": False, "error": f"Unknown processor: {processor}"}

    def _process_with_marker(self, book_id: str, pdf_path: str) -> Dict[str, Any]:
        """Process book with Marker service (extended timeout and book config)"""

        try:
            # Book-specific Marker configuration
            data = {
                "extract_images": "true",
                "book_mode": "true",  # Enable book-specific processing
                "detect_chapters": str(self.enable_chapter_detection).lower(),
                "extract_toc": str(self.enable_toc_extraction).lower(),
                "extract_glossary": str(self.enable_glossary_extraction).lower(),
                "max_pages": "2000",  # Allow processing of large books
                "book_id": book_id
            }

            logger.info(f"Sending book PDF to Marker service (6-hour timeout): {Path(pdf_path).name}")
            with open(pdf_path, "rb") as pdf_file:
                response = requests.post(
                    f"{self.marker_service_url}/convert",
                    files={"pdf": pdf_file},
                    data=data,
                    timeout=self.marker_timeout,  # 6 hours for large books
                )

            if response.status_code != 200:
                logger.error(f"Marker service error ({response.status_code}): {response.text[:500]}")
                return {
                    "success": False,
                    "error": f"Marker service returned {response.status_code}",
                    "method_used": "marker"
                }

            result = response.json()

            # Extract book-specific metadata
            metadata = result.get("metadata", {})

            # Extract table of contents if available
            toc = self._extract_table_of_contents(result.get("markdown", ""))
            if toc:
                metadata["table_of_contents"] = toc

            # Extract glossary terms if available
            glossary = self._extract_glossary_terms(result.get("markdown", ""))
            if glossary:
                metadata["glossary_terms"] = glossary

            # Estimate reading difficulty for books
            reading_difficulty = self._estimate_reading_difficulty(result.get("markdown", ""))
            if reading_difficulty:
                metadata["reading_difficulty"] = reading_difficulty

            return {
                "success": True,
                "markdown": result.get("markdown", ""),
                "metadata": metadata,
                "method_used": "marker",
                "images_extracted": bool(result.get("images")),
                "processing_time": result.get("processing_time"),
                "page_count": result.get("page_count")
            }

        except requests.exceptions.Timeout:
            logger.error(f"Marker timeout after {self.marker_timeout/3600:.1f} hours for book {book_id}")
            return {
                "success": False,
                "error": f"Processing timeout after {self.marker_timeout/3600:.1f} hours",
                "method_used": "marker"
            }
        except Exception as e:
            logger.error(f"Marker processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method_used": "marker"
            }

    def _process_with_mineru(self, book_id: str, pdf_path: str) -> Dict[str, Any]:
        """Process book with MinerU service (extended timeout)"""

        try:
            data = {"book_id": book_id, "book_mode": "true"}

            logger.info(f"Sending book PDF to MinerU service (5-hour timeout): {Path(pdf_path).name}")
            with open(pdf_path, "rb") as pdf_file:
                response = requests.post(
                    f"{self.mineru_service_url}/convert",
                    files={"pdf": pdf_file},
                    data=data,
                    timeout=self.mineru_timeout,  # 5 hours for large books
                )

            if response.status_code != 200:
                logger.error(f"MinerU service error ({response.status_code}): {response.text[:500]}")
                return {
                    "success": False,
                    "error": f"MinerU service returned {response.status_code}",
                    "method_used": "mineru"
                }

            result = response.json()

            return {
                "success": True,
                "markdown": result.get("markdown", ""),
                "metadata": result.get("metadata", {}),
                "method_used": "mineru",
                "images_extracted": bool(result.get("images")),
                "processing_time": result.get("processing_time")
            }

        except requests.exceptions.Timeout:
            logger.error(f"MinerU timeout after {self.mineru_timeout/3600:.1f} hours for book {book_id}")
            return {
                "success": False,
                "error": f"Processing timeout after {self.mineru_timeout/3600:.1f} hours",
                "method_used": "mineru"
            }
        except Exception as e:
            logger.error(f"MinerU processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method_used": "mineru"
            }

    def _process_epub(self, book_id: str, epub_path: str) -> Dict[str, Any]:
        """Process EPUB book using native EPUB parsing"""

        try:
            # Import EPUB loader (from langchain)
            from langchain_community.document_loaders import UnstructuredEPubLoader

            logger.info(f"Processing EPUB book: {Path(epub_path).name}")

            # Load EPUB content
            loader = UnstructuredEPubLoader(epub_path, mode="elements")
            documents = loader.load()

            # Combine all document content
            markdown_content = ""
            metadata = {
                "source": epub_path,
                "file_type": "epub",
                "total_elements": len(documents)
            }

            # Process each document element
            for doc in documents:
                markdown_content += doc.page_content + "\n\n"

                # Extract metadata from first document
                if not metadata.get("title") and doc.metadata.get("title"):
                    metadata["title"] = doc.metadata["title"]

            # Extract book-specific features from EPUB content
            toc = self._extract_table_of_contents(markdown_content)
            if toc:
                metadata["table_of_contents"] = toc

            glossary = self._extract_glossary_terms(markdown_content)
            if glossary:
                metadata["glossary_terms"] = glossary

            reading_difficulty = self._estimate_reading_difficulty(markdown_content)
            if reading_difficulty:
                metadata["reading_difficulty"] = reading_difficulty

            return {
                "success": True,
                "markdown": markdown_content,
                "metadata": metadata,
                "method_used": "epub_native",
                "images_extracted": False,  # EPUB images handled separately
                "processing_time": None
            }

        except ImportError:
            logger.error("EPUB processing requires langchain_community package")
            return {
                "success": False,
                "error": "EPUB processing not available - missing dependencies",
                "method_used": "epub_native"
            }
        except Exception as e:
            logger.error(f"EPUB processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method_used": "epub_native"
            }

    def _extract_table_of_contents(self, markdown: str) -> List[Dict[str, Any]]:
        """Extract table of contents from markdown content"""
        toc = []
        lines = markdown.split('\n')

        for i, line in enumerate(lines):
            # Look for chapter headings (# or ##)
            if line.strip().startswith(('# ', '## ')):
                level = len(line) - len(line.lstrip('#'))
                title = line.strip('#').strip()

                # Estimate page number (rough approximation)
                chars_before = len('\n'.join(lines[:i]))
                estimated_page = max(1, chars_before // 2500)  # ~2500 chars per page

                toc.append({
                    "chapter": title,
                    "level": level,
                    "page": estimated_page
                })

        return toc[:50]  # Limit to first 50 entries

    def _extract_glossary_terms(self, markdown: str) -> List[Dict[str, str]]:
        """Extract glossary terms from markdown content"""
        glossary = []
        lines = markdown.split('\n')

        in_glossary_section = False
        for line in lines:
            # Look for glossary section
            if any(keyword in line.lower() for keyword in ['glossary', 'definitions', 'terminology']):
                if line.strip().startswith('#'):
                    in_glossary_section = True
                    continue

            # Stop at next major section
            if in_glossary_section and line.strip().startswith('#'):
                break

            # Extract term definitions (format: **Term**: Definition)
            if in_glossary_section and '**' in line and ':' in line:
                try:
                    term_part = line.split('**')[1].split('**')[0]
                    if ':' in line:
                        definition_part = line.split(':', 1)[1].strip()
                        if term_part and definition_part:
                            glossary.append({
                                "term": term_part.strip(),
                                "definition": definition_part.strip()
                            })
                except (IndexError, ValueError):
                    continue

        return glossary[:100]  # Limit to first 100 terms

    def _estimate_reading_difficulty(self, markdown: str) -> Optional[str]:
        """Estimate reading difficulty of the book content"""
        try:
            # Simple heuristic based on sentence length and word complexity
            sentences = [s.strip() for s in markdown.replace('.', '.\n').split('\n') if s.strip()]
            if not sentences:
                return None

            # Calculate average sentence length
            total_words = sum(len(sentence.split()) for sentence in sentences)
            avg_sentence_length = total_words / len(sentences)

            # Calculate average word length
            all_words = markdown.split()
            avg_word_length = sum(len(word) for word in all_words) / len(all_words) if all_words else 0

            # Simple classification
            if avg_sentence_length < 15 and avg_word_length < 5:
                return "beginner"
            elif avg_sentence_length < 20 and avg_word_length < 6:
                return "intermediate"
            elif avg_sentence_length < 25 and avg_word_length < 7:
                return "advanced"
            else:
                return "expert"

        except Exception:
            return None
