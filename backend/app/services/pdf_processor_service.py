from app.services import pdf_service_client
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import time
import subprocess
import requests
import asyncio

from .image_manager import get_image_manager
from .async_pdf_processor import get_async_pdf_processor
from .pdf_extraction_helpers import (
    process_with_marker_cli,
    process_with_mineru_service,
    process_with_mineru_cli,
    process_with_fallback,
    process_with_pix2text,
    process_with_nougat,
    text_to_markdown,
)

# Disable MPS for processors to prevent segfault on macOS
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

logger = logging.getLogger(__name__)

def _run_async_coro(coro):
    """
    Run an async coroutine safely from sync code.
    - If no event loop is running: use asyncio.run
    - If a loop is running in this thread: raise (caller must be async)
    - If a loop is running in *another* thread, the caller of this function
      should switch to an async context or own that thread's loop.
    """
    try:
        asyncio.get_running_loop()
        # If we got here, we're inside an event loop on this thread – we cannot block.
        raise RuntimeError("Cannot run coroutine from within an active event loop.")
    except RuntimeError:
        # No running loop in this thread — safe to asyncio.run
        return asyncio.run(coro)

class PDFProcessorService:
    """Service for processing PDF documents to markdown"""

    def __init__(self):
        logger.info("="*60)
        logger.info("🔍 PDF PROCESSOR INITIALIZATION")
        logger.info("="*60)

        # Marker service configuration
        self.marker_service_url = pdf_service_client.marker_url()

        # MinerU service configuration
        self.mineru_service_url = pdf_service_client.mineru_url()

        # Check available processors in order of preference
        self.marker_service_available = self._check_marker_service()  # Best - isolated environment
        self.mineru_service_available = self._check_mineru_service()  # Second best - isolated environment
        self.marker_available = self._check_marker()  # Direct marker (may have conflicts)
        self.mineru_available = self._check_mineru()  # Direct mineru (may have dependency issues)
        self.pix2text_available = self._check_pix2text()
        self.nougat_available = self._check_nougat()
        self.docling_available = False  # DISABLED - causes segfaults on macOS
        self.fallback_available = True  # pypdfium2 is always available

        logger.info("📊 PDF Processor Status:")
        logger.info(f"  🌟 Marker Service (best): {self.marker_service_available}")
        logger.info(f"  ⭐ MinerU Service (second): {self.mineru_service_available}")
        logger.info(f"  ⚠️  Marker Direct: {self.marker_available} (may have conflicts)")
        logger.info(f"  ⚠️  MinerU Direct: {self.mineru_available} (may have dep issues)")
        logger.info(f"  ✅ Pix2Text: {self.pix2text_available}")
        logger.info(f"  ❌ Nougat: {self.nougat_available} (transformer issues)")
        logger.info(f"  ❌ Docling: DISABLED (causes segfaults)")
        logger.info(f"  ✅ Basic (fallback): {self.fallback_available}")

        if not self.marker_service_available:
            logger.info("💡 Marker Service not running - For best results:")
            logger.info("    1. Run: cd marker_service && ./setup_marker.sh")
            logger.info("    2. Run: ./start_marker_service.sh")

        if not self.mineru_available:
            logger.info("ℹ️  MinerU not available - To enable:")
            logger.info("    Run: pip install mineru")

        logger.info("="*60)

    def _check_marker_service(self) -> bool:
        try:
            response = requests.get(f"{self.marker_service_url}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get("marker") == "available":
                    logger.info("✅ Marker Service is running and healthy")
                    return True
            return False
        except Exception as e:
            logger.debug(f"Marker service not available: {e}")
            return False

    def _check_mineru_service(self) -> bool:
        try:
            response = requests.get(f"{self.mineru_service_url}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get("mineru") == "available":
                    logger.info("✅ MinerU Service is running and healthy")
                    return True
            return False
        except Exception as e:
            logger.debug(f"MinerU service not available: {e}")
            return False

    def _check_docling(self) -> bool:
        return False

    def _check_marker(self) -> bool:
        try:
            logger.debug("Checking Marker availability...")
            import marker  # noqa: F401
            from marker.converters.pdf import PdfConverter  # noqa: F401
            from marker.config.parser import ConfigParser  # noqa: F401
            logger.info("✅ Marker imports successful")
            return True
        except ImportError as e:
            logger.error(f"❌ Marker import failed: {e}")
            logger.info("   Install with: pip install marker-pdf")
            return False
        except Exception as e:
            logger.error(f"❌ Marker check failed with unexpected error: {e}")
            return False

    def _check_pix2text(self) -> bool:
        try:
            logger.debug("Checking Pix2Text availability...")
            from pix2text import Pix2Text  # noqa: F401
            logger.info("✅ Pix2Text imports successful")
            return True
        except ImportError as e:
            logger.debug(f"Pix2Text not installed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Pix2Text check failed: {e}")
            return False

    def _check_mineru(self) -> bool:
        try:
            logger.debug("Checking MinerU availability...")
            result = subprocess.run(['mineru', '--version'],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("✅ MinerU CLI available")
                return True
            return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.debug("MinerU CLI not found")
            return False
        except Exception as e:
            logger.error(f"❌ MinerU check failed: {e}")
            return False

    def _check_nougat(self) -> bool:
        try:
            logger.debug("Checking Nougat availability...")
            result = subprocess.run(['nougat', '--help'],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'nougat' in result.stdout.lower():
                logger.info("✅ Nougat CLI available")
                return True
            return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.debug("Nougat CLI not found")
            return False
        except Exception as e:
            logger.error(f"❌ Nougat check failed: {e}")
            return False

    def process_pdf(self, pdf_path: str, prefer_method: str = "auto", paper_id: Optional[int] = None, mongo_paper_id: Optional[str] = None) -> Dict:
        """
        Process a PDF file to extract structured content with image extraction

        Args:
            pdf_path: Path to the PDF file
            prefer_method: Preferred processing method ("marker", "pix2text", "mineru", "nougat", "docling", "auto")
            paper_id: Optional paper ID for image storage (integer)
            mongo_paper_id: Optional MongoDB paper ID for callback URLs (string)

        Returns:
            Dict with processed content and metadata
        """
        result = {
            "success": False,
            "markdown": "",
            "metadata": {},
            "method_used": None,
            "processing_time": 0,
            "error": None
        }

        start_time = time.time()

        # Validate file exists
        if not os.path.exists(pdf_path):
            result["error"] = f"PDF file not found: {pdf_path}"
            return result

        # Try methods in order of preference
        methods = []

        logger.info("="*60)
        logger.info(f"🔄 PDF PROCESSING: {Path(pdf_path).name}")
        logger.info("="*60)

        if prefer_method == "marker_service" and self.marker_service_available:
            methods = ["marker_service", "mineru", "marker", "pix2text", "fallback"]
            logger.info("📋 Preference: Marker Service (user requested)")
        elif prefer_method == "marker":
            # Prefer Marker service over CLI when available
            if self.marker_service_available:
                methods = ["marker_service", "marker", "pix2text", "mineru", "fallback"]
                logger.info("📋 Preference: Marker Service (isolated environment)")
            elif self.marker_available:
                methods = ["marker", "pix2text", "mineru", "nougat", "fallback"]
                logger.info("📋 Preference: Marker CLI (user requested)")
            else:
                methods = ["mineru_service", "pix2text", "fallback"]
                logger.info("📋 Marker not available, falling back to other methods")
        elif prefer_method == "pix2text" and self.pix2text_available:
            methods = ["pix2text", "marker", "mineru", "nougat", "fallback"]
            logger.info("📋 Preference: Pix2Text (user requested)")
        elif prefer_method == "mineru":
            # Prefer MinerU service over CLI when available
            if self.mineru_service_available:
                methods = ["mineru_service", "mineru", "marker", "pix2text", "fallback"]
                logger.info("📋 Preference: MinerU Service (isolated environment)")
            elif self.mineru_available:
                methods = ["mineru", "marker", "pix2text", "nougat", "fallback"]
                logger.info("📋 Preference: MinerU CLI (user requested)")
            else:
                methods = ["marker_service", "marker", "pix2text", "fallback"]
                logger.info("📋 MinerU not available, falling back to other methods")
        elif prefer_method == "nougat" and self.nougat_available:
            methods = ["nougat", "marker", "pix2text", "mineru", "fallback"]
            logger.info("📋 Preference: Nougat (user requested)")
        else:  # auto - Prefer Marker Service, then MinerU Service, then fallback
            methods = []
            if self.marker_service_available:
                methods.append("marker_service")
            if self.mineru_service_available:
                methods.append("mineru_service")
            methods.append("fallback")  # Always have fallback
            logger.info(f"📋 Preference: Auto (trying services in order: {methods})")

        logger.info(f"🔍 Will try methods in order: {methods}")
        logger.info("="*60)

        for method in methods:
            try:
                if method == "marker_service" and self.marker_service_available:
                    logger.info("🌟 Attempting Marker Service via Async client (unified path)...")
                    content, metadata = self._process_with_marker_service(pdf_path, paper_id)
                    if content:
                        result["success"] = True
                        result["markdown"] = content
                        result["metadata"] = metadata
                        result["method_used"] = "marker_service"
                        logger.info("✅ SUCCESS with Marker Service!")
                        break
                    else:
                        logger.warning("❌ Marker Service returned empty content")

                elif method == "mineru_service" and self.mineru_service_available:
                    logger.info("⭐ Attempting MinerU Service (isolated environment, high quality)...")
                    content, metadata = process_with_mineru_service(pdf_path, self.mineru_service_url, paper_id, mongo_paper_id)
                    if content:
                        result["success"] = True
                        result["markdown"] = content
                        result["metadata"] = metadata
                        result["method_used"] = "mineru_service"
                        logger.info("✅ SUCCESS with MinerU Service!")
                        break
                    else:
                        logger.warning("❌ MinerU Service returned empty content")

                elif method == "marker" and self.marker_available:
                    logger.info("⭐ Attempting Marker CLI (fallback from service, may have conflicts)...")
                    content, metadata = process_with_marker_cli(pdf_path)
                    if content:
                        result["success"] = True
                        result["markdown"] = content
                        result["metadata"] = metadata
                        result["method_used"] = "marker"
                        logger.info("✅ SUCCESS with Marker!")
                        break
                    else:
                        logger.warning("❌ Marker returned empty content")

                elif method == "pix2text" and self.pix2text_available:
                    logger.info("🖼️ Attempting Pix2Text (OCR-based)...")
                    content, metadata = process_with_pix2text(pdf_path)
                    if content:
                        result["success"] = True
                        result["markdown"] = content
                        result["metadata"] = metadata
                        result["method_used"] = "pix2text"
                        logger.info("✅ SUCCESS with Pix2Text!")
                        break
                    else:
                        logger.warning("❌ Pix2Text returned empty content")

                elif method == "mineru" and self.mineru_available:
                    logger.info("⛏️ Attempting MinerU CLI (fallback from service, table detection disabled)...")
                    content, metadata = process_with_mineru_cli(pdf_path)
                    if content:
                        result["success"] = True
                        result["markdown"] = content
                        result["metadata"] = metadata
                        result["method_used"] = "mineru"
                        logger.info("✅ SUCCESS with MinerU!")
                        break
                    else:
                        logger.warning("❌ MinerU returned empty content")

                elif method == "nougat" and self.nougat_available:
                    logger.info("🍫 Attempting Nougat (Meta, neural OCR)...")
                    content, metadata = process_with_nougat(pdf_path)
                    if content:
                        result["success"] = True
                        result["markdown"] = content
                        result["metadata"] = metadata
                        result["method_used"] = "nougat"
                        logger.info("✅ SUCCESS with Nougat!")
                        break
                    else:
                        logger.warning("❌ Nougat returned empty content")

                elif method == "fallback":
                    logger.info("📄 Attempting basic extraction (fallback)...")
                    content, metadata = process_with_fallback(pdf_path)
                    if content:
                        result["success"] = True
                        result["markdown"] = content
                        result["metadata"] = metadata
                        result["method_used"] = "pypdfium2"
                        logger.info("✅ SUCCESS with basic extraction")
                        logger.warning("⚠️  Using basic extraction - quality may be lower")
                        if not self.marker_available:
                            logger.warning("    - Install Marker: pip install marker-pdf")
                        if not self.pix2text_available:
                            logger.warning("    - Install Pix2Text: pip install pix2text")
                        break
                    else:
                        logger.warning("❌ Basic extraction returned empty content")

            except Exception as e:
                logger.error(f"❌ FAILED with {method}: {str(e)[:200]}")
                logger.debug(f"Full error: {e}")
                result["error"] = str(e)
                continue

        result["processing_time"] = time.time() - start_time

        logger.info("="*60)
        if result["success"]:
            logger.info("✅ PDF PROCESSING COMPLETE")
            logger.info(f"   Method: {result['method_used']}")
            logger.info(f"   Time: {result['processing_time']:.2f}s")
            logger.info(f"   Content length: {len(result['markdown'])} characters")
        else:
            logger.error("❌ PDF PROCESSING FAILED")
            logger.error(f"   Error: {result['error']}")
            logger.error("   No processor could extract content from this PDF")
        logger.info("="*60)

        return result

    # ----------------- Unified Marker Service path (uses async client) -----------------

    def _process_with_marker_service(self, pdf_path: str, paper_id: Optional[int] = None) -> Tuple[str, Dict]:
        try:
            async_client = get_async_pdf_processor()
            if async_client.local_fallback is None:
                async_client.local_fallback = self.process_pdf
            result = _run_async_coro(
                async_client.process_pdf_async(
                    pdf_path=pdf_path,
                    prefer_method="marker",
                    paper_id=paper_id,
                )
            )
            if result.get("success") and result.get("markdown"):
                metadata = result.get("metadata", {}) or {}
                metadata["processor"] = "marker_service"
                if "images_extracted" in result:
                    metadata["images_extracted"] = result["images_extracted"]
                if "images" in result:
                    metadata["image_count"] = result["images"]
                if "_debug" in result and isinstance(result["_debug"], dict):
                    metadata["_debug"] = result["_debug"]
                    pipe = result["_debug"]
                    logger.info("Marker pipeline: figure_or_image_present=%s", pipe.get("figure_or_image_present"))
                if paper_id and metadata.get("images_extracted", 0) > 0:
                    logger.info(f"📸 Extracted {metadata['images_extracted']} images for paper {paper_id}")
                return result["markdown"], metadata

            err = result.get("error") or "Marker service processing failed"
            logger.warning(f"❌ Marker Service failed: {err}")
            dbg = result.get("_debug")
            if isinstance(dbg, dict):
                logger.warning("Last pipeline snapshot: %s", {
                    "figure_or_image_present": dbg.get("figure_or_image_present"),
                    "processors_count": len(dbg.get("processors", [])),
                })
            return "", {}

        except RuntimeError as rexc:
            logger.error("Event loop is already running; cannot block here. "
                         "Call the async client directly in an async context. Details: %s", rexc)
            return "", {}
        except Exception as e:
            logger.error(f"❌ Marker Service (async client) error: {e}")
            return "", {}

    def _text_to_markdown(self, text: str) -> str:
        return text_to_markdown(text)


# Singleton instance
_pdf_processor_service = None

def get_pdf_processor_service() -> PDFProcessorService:
    global _pdf_processor_service
    if _pdf_processor_service is None:
        _pdf_processor_service = PDFProcessorService()
    return _pdf_processor_service
