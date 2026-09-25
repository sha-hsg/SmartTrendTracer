"""
Single point of contact for the external Marker (8002) and MinerU (8003)
PDF services: addressing, health probes, control commands and the progress
callback URL. Previously each of seven files hardcoded localhost:8002/8003 and
the API layer posted to Marker's /kill endpoint by URL.
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def marker_url(path: str = "") -> str:
    return settings.marker_service_url.rstrip("/") + ("/" + path.lstrip("/") if path else "")


def mineru_url(path: str = "") -> str:
    return settings.mineru_service_url.rstrip("/") + ("/" + path.lstrip("/") if path else "")


def progress_callback_url(paper_id: str) -> str:
    """URL the PDF services call to report progress for a paper."""
    return f"{settings.backend_base_url}/api/papers/{paper_id}/progress-callback"


def kill_marker_job() -> None:
    """Stop an orphaned marker_single subprocess (sync). Never raises."""
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(marker_url("kill"))
            logger.info(f"Marker /kill response: {resp.status_code} {resp.text}")
    except Exception as err:
        logger.warning(f"Failed to call Marker /kill endpoint: {err}")


async def kill_marker_job_async() -> None:
    """Stop an orphaned marker_single subprocess (async). Never raises."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(marker_url("kill"))
            logger.info(f"Marker /kill response: {resp.status_code} {resp.text}")
    except Exception as err:
        logger.warning(f"Failed to call Marker /kill endpoint: {err}")
