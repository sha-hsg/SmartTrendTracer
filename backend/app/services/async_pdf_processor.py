"""
Async PDF Processor Service
Handles PDF processing without blocking the main thread
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional
import requests
from pathlib import Path
import time
from app.utils.content_cleaner import clean_markdown_content

logger = logging.getLogger(__name__)

class AsyncPDFProcessor:
    """Async wrapper for PDF processing to prevent blocking"""

    def __init__(self):
        # Thread pool for blocking I/O operations
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.marker_service_url = "http://localhost:8002"
        self.mineru_service_url = "http://localhost:8003"

    async def process_pdf_async(
        self,
        pdf_path: str,
        prefer_method: str = "auto",
        paper_id: Optional[int] = None
    ) -> Dict:
        """
        Process PDF asynchronously without blocking the event loop

        Args:
            pdf_path: Path to PDF file
            prefer_method: Preferred processing method ("auto", "marker", "mineru")
            paper_id: Persist images/links under this paper id (enables image extraction path)

        Returns:
            Dict with keys:
              - success (bool)
              - markdown (str)
              - metadata (dict)
              - method_used (str | None)
              - images_extracted (int | None)
              - tables_skipped / llm_used / page_range (if provided by server)
              - _debug (dict | None)  # only when server returns it
              - error (str | None)
        """
        loop = asyncio.get_event_loop()

        # Prefer explicit routing if requested
        if prefer_method.lower() == "marker":
            marker_result = await loop.run_in_executor(
                self.executor,
                self._process_with_marker_service,
                pdf_path,
                paper_id,
            )
            if marker_result.get("success"):
                return marker_result

            # fallback to mineru if available
            mineru_available = await self._check_mineru_service_async()
            if mineru_available:
                return await loop.run_in_executor(
                    self.executor, self._process_with_mineru_service, pdf_path, paper_id
                )
            return marker_result

        if prefer_method.lower() == "mineru":
            mineru_result = await loop.run_in_executor(
                self.executor, self._process_with_mineru_service, pdf_path, paper_id
            )
            if mineru_result.get("success"):
                return mineru_result
            # fallback to marker if available
            marker_available = await self._check_marker_service_async()
            if marker_available:
                return await loop.run_in_executor(
                    self.executor, self._process_with_marker_service, pdf_path, paper_id
                )
            return mineru_result

        # Auto: probe availability and choose best path
        marker_available = await self._check_marker_service_async()
        mineru_available = await self._check_mineru_service_async()

        if marker_available:
            result = await loop.run_in_executor(
                self.executor, self._process_with_marker_service, pdf_path, paper_id
            )
            if not result.get("success") and mineru_available:
                logger.info("Marker failed, trying MinerU service...")
                result = await loop.run_in_executor(
                    self.executor, self._process_with_mineru_service, pdf_path, paper_id
                )
        elif mineru_available:
            result = await loop.run_in_executor(
                self.executor, self._process_with_mineru_service, pdf_path, paper_id
            )
        else:
            # Fall back to synchronous processor in thread (your local fallback)
            from .pdf_processor_service import get_pdf_processor_service
            processor = get_pdf_processor_service()
            result = await loop.run_in_executor(
                self.executor, processor.process_pdf, pdf_path, prefer_method
            )

        return result

    # ----------------------- Service Probes -----------------------

    async def _check_marker_service_async(self) -> bool:
        """Check if Marker service is available (async)"""
        loop = asyncio.get_event_loop()

        def check():
            try:
                r = requests.get(f"{self.marker_service_url}/health", timeout=1)
                return r.status_code == 200 and r.json().get("marker") == "available"
            except Exception:
                return False

        return await loop.run_in_executor(self.executor, check)

    async def _check_mineru_service_async(self) -> bool:
        """Check if MinerU service is available (async)"""
        loop = asyncio.get_event_loop()

        def check():
            try:
                r = requests.get(f"{self.mineru_service_url}/health", timeout=1)
                return r.status_code == 200 and r.json().get("mineru") == "available"
            except Exception:
                return False

        return await loop.run_in_executor(self.executor, check)

    # ----------------------- Server Calls -----------------------

    def _process_with_marker_service(self, pdf_path: str, paper_id: Optional[int] = None) -> Dict:
        """Process PDF using Marker service (blocking, run in thread)"""
        t0 = time.time()
        try:
            with open(pdf_path, "rb") as f:
                files = {"file": (Path(pdf_path).name, f, "application/pdf")}
                # Ask server for best-quality path; it will do CLI fallback if needed.
                data = {
                    "force_ocr": "false",
                    "output_format": "markdown",
                    "use_llm": "true",
                    "skip_tables": "false",
                    "llm_light": "false",
                    "debug": "true",  # include server pipeline snapshot in response
                }

                if paper_id is not None:
                    data["paper_id"] = str(paper_id)

                logger.info("Sending PDF to Marker service: %s (paper_id=%s)",
                            Path(pdf_path).name, paper_id)
                response = requests.post(
                    f"{self.marker_service_url}/convert",
                    files=files,
                    data=data,
                    timeout=10800,  # 3 hours timeout for long PDF processing (Marker can take 2+ hours for complex documents)
                )

            if response.status_code != 200:
                # Log body to help debug config mismatches
                body_preview = response.text[:500].replace("\n", " ")
                logger.error("Marker non-200 (%s): %s", response.status_code, body_preview)
                return {
                    "success": False,
                    "markdown": "",
                    "metadata": {},
                    "method_used": None,
                    "error": f"Marker HTTP {response.status_code}: {body_preview}",
                }

            # Safe JSON parse
            try:
                result = response.json()
            except ValueError:
                body_preview = response.text[:500].replace("\n", " ")
                logger.error("Marker returned non-JSON body: %s", body_preview)
                return {
                    "success": False,
                    "markdown": "",
                    "metadata": {},
                    "method_used": None,
                    "error": "Marker returned non-JSON response",
                }

            if result.get("success"):
                elapsed = round(time.time() - t0, 3)
                # Optional debug logging
                if "images_extracted" in result:
                    logger.info(
                        "Marker server extracted %s images (reported images=%s)",
                        result.get("images_extracted"), result.get("images"),
                    )
                
                # Clean the markdown content to remove problematic HTML tags
                raw_content = result.get("content", "")
                cleaned_content = clean_markdown_content(raw_content)
                
                return {
                    "success": True,
                    "markdown": cleaned_content,
                    "metadata": result.get("metadata", {}),
                    "method_used": "marker_service",
                    "processing_time": elapsed,
                    # Bubble up useful debug fields from the server:
                    "images_extracted": result.get("images_extracted"),
                    "images": result.get("images"),
                    "tables_skipped": result.get("tables_skipped"),
                    "llm_used": result.get("llm_used"),
                    "page_range": result.get("page_range"),
                    "_debug": result.get("_debug"),
                }

            # success == False with 200 response
            # Still clean content even in failure case (might have partial content)
            raw_content = result.get("content", "") or ""
            cleaned_content = clean_markdown_content(raw_content) if raw_content else ""
            
            return {
                "success": False,
                "markdown": cleaned_content,
                "metadata": result.get("metadata", {}) or {},
                "method_used": None,
                "error": result.get("detail") or "Marker service processing failed",
                "_debug": result.get("_debug"),
            }

        except Exception as e:
            logger.exception("Marker service error")
            return {
                "success": False,
                "markdown": "",
                "metadata": {},
                "method_used": None,
                "error": str(e),
            }

    def _process_with_mineru_service(self, pdf_path: str, paper_id: Optional[int] = None) -> Dict:
        """Process PDF using MinerU service (blocking, run in thread)"""
        t0 = time.time()
        try:
            with open(pdf_path, "rb") as f:
                files = {"file": (Path(pdf_path).name, f, "application/pdf")}
                data = {
                    "parse_tables": "false",
                    "output_format": "markdown",
                }
                # Add paper_id if provided (MinerU expects integer, not string)
                if paper_id:
                    data["paper_id"] = paper_id

                logger.info("Sending PDF to MinerU service: %s", Path(pdf_path).name)
                response = requests.post(
                    f"{self.mineru_service_url}/convert",
                    files=files,
                    data=data,
                    timeout=3600,  # 1 hour timeout (MinerU processes can be long too)
                )

            if response.status_code != 200:
                body_preview = response.text[:500].replace("\n", " ")
                logger.error("MinerU non-200 (%s): %s", response.status_code, body_preview)
                return {
                    "success": False,
                    "markdown": "",
                    "metadata": {},
                    "method_used": None,
                    "error": f"MinerU HTTP {response.status_code}: {body_preview}",
                }

            try:
                result = response.json()
            except ValueError:
                body_preview = response.text[:500].replace("\n", " ")
                logger.error("MinerU returned non-JSON body: %s", body_preview)
                return {
                    "success": False,
                    "markdown": "",
                    "metadata": {},
                    "method_used": None,
                    "error": "MinerU returned non-JSON response",
                }

            if result.get("success"):
                elapsed = round(time.time() - t0, 3)
                
                # Clean the markdown content to remove problematic HTML tags
                raw_content = result.get("content", "")
                cleaned_content = clean_markdown_content(raw_content)
                
                return {
                    "success": True,
                    "markdown": cleaned_content,
                    "metadata": result.get("metadata", {}),
                    "method_used": "mineru_service",
                    "processing_time": elapsed,
                }

            # Clean content even in failure case
            raw_content = result.get("content", "") or ""
            cleaned_content = clean_markdown_content(raw_content) if raw_content else ""
            
            return {
                "success": False,
                "markdown": cleaned_content,
                "metadata": result.get("metadata", {}) or {},
                "method_used": None,
                "error": result.get("detail") or "MinerU service processing failed",
            }

        except Exception as e:
            logger.exception("MinerU service error")
            return {
                "success": False,
                "markdown": "",
                "metadata": {},
                "method_used": None,
                "error": str(e),
            }

# Singleton instance
_async_processor = None

def get_async_pdf_processor() -> AsyncPDFProcessor:
    """Get or create async PDF processor instance"""
    global _async_processor
    if _async_processor is None:
        _async_processor = AsyncPDFProcessor()
    return _async_processor