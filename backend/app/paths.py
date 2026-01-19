"""
Centralized path management for cross-platform portability.

This module provides a single source of truth for all file paths in the application,
ensuring the project can be relocated to any directory and works identically on
Linux, macOS, and Windows.

All paths are computed relative to the project root, eliminating hardcoded absolute paths.
"""

from pathlib import Path
import os
from typing import Optional


# ============================================================================
# Project Root Detection
# ============================================================================

def get_project_root() -> Path:
    """
    Dynamically detect the project root directory.

    Works by finding the parent directory containing both 'backend' and 'frontend' folders.
    This allows the project to be placed anywhere on the filesystem.

    Returns:
        Path: Absolute path to the project root
    """
    # Start from this file's location
    current = Path(__file__).resolve()

    # Walk up the directory tree
    for parent in current.parents:
        # Check if this looks like the project root
        if (parent / "backend").exists() and (parent / "frontend").exists():
            return parent

    # Fallback: assume standard structure (backend/app/paths.py)
    return Path(__file__).resolve().parent.parent.parent


# ============================================================================
# Core Directory Paths
# ============================================================================

# Project structure
PROJECT_ROOT = get_project_root()
BACKEND_ROOT = PROJECT_ROOT / "backend"
FRONTEND_ROOT = PROJECT_ROOT / "frontend"

# Data root directory (all data files stored here)
DATA_ROOT = BACKEND_ROOT / "data"

# Ensure data directory exists
DATA_ROOT.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Data Storage Paths
# ============================================================================

# Research papers
PAPERS_DIR = DATA_ROOT / "papers"
PAPER_REPOSITORY = DATA_ROOT / "paper_repository"
PAPER_IMAGES = DATA_ROOT / "paper_images"

# Books
BOOK_REPOSITORY = DATA_ROOT / "book_repository"

# Substack articles
ARTICLE_IMAGES = DATA_ROOT / "article_images"

# Twitter media
MEDIA_DIR = DATA_ROOT / "media"

# Processing outputs
MINERU_OUTPUT = DATA_ROOT / "mineru_output"
TEI_XML = DATA_ROOT / "tei_xml"
GPT5_RESPONSES = DATA_ROOT / "gpt5_responses"


# ============================================================================
# Vector Store and RAG Paths
# ============================================================================

# RAG indexes
RAG_INDEX_PATH = DATA_ROOT / "rag_index"
RAG_INDEX_CONCEPTS = DATA_ROOT / "rag_index_concepts"

# Vector stores for embeddings
VECTOR_STORE_PATH = DATA_ROOT / "vector_store"
EMBEDDINGS_CACHE = DATA_ROOT / "embeddings_cache"


# ============================================================================
# MongoDB Sync Directory
# ============================================================================

MONGODB_SYNC = BACKEND_ROOT / "mongodb_sync"
MONGODB_SYNC_LATEST = MONGODB_SYNC / "latest"
MONGODB_SYNC_BACKUPS = MONGODB_SYNC / "backups"


# ============================================================================
# Helper Functions
# ============================================================================

def get_relative_path(absolute_path: Path, base: Optional[Path] = None) -> str:
    """
    Convert an absolute path to a relative path from base directory.

    Args:
        absolute_path: The absolute path to convert
        base: Base directory (defaults to DATA_ROOT)

    Returns:
        str: Relative path as string (forward slashes, cross-platform)

    Example:
        >>> p = Path("/path/to/data/papers/file.pdf")
        >>> get_relative_path(p)
        "papers/file.pdf"
    """
    if base is None:
        base = DATA_ROOT

    try:
        rel = Path(absolute_path).relative_to(base)
        # Use forward slashes for cross-platform compatibility
        return str(rel).replace(os.sep, '/')
    except ValueError:
        # Path is not relative to base, return as-is
        return str(absolute_path)


def resolve_data_path(relative_path: str) -> Path:
    """
    Resolve a relative path to an absolute path within DATA_ROOT.

    Args:
        relative_path: Relative path string (e.g., "papers/file.pdf")

    Returns:
        Path: Absolute path

    Example:
        >>> resolve_data_path("papers/file.pdf")
        Path("/absolute/path/to/backend/data/papers/file.pdf")
    """
    # Normalize path separators
    normalized = relative_path.replace('\\', '/')
    return DATA_ROOT / normalized


def ensure_dir(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists

    Returns:
        Path: The same path (for chaining)
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


# ============================================================================
# Initialize Required Directories
# ============================================================================

def initialize_directories():
    """
    Create all required directories if they don't exist.
    Safe to call multiple times (idempotent).
    """
    directories = [
        PAPERS_DIR,
        PAPER_REPOSITORY,
        PAPER_IMAGES,
        BOOK_REPOSITORY,
        ARTICLE_IMAGES,
        MEDIA_DIR,
        MINERU_OUTPUT,
        TEI_XML,
        GPT5_RESPONSES,
        RAG_INDEX_PATH,
        RAG_INDEX_CONCEPTS,
        VECTOR_STORE_PATH,
        MONGODB_SYNC,
        MONGODB_SYNC_LATEST,
        MONGODB_SYNC_BACKUPS,
    ]

    for directory in directories:
        ensure_dir(directory)


# Initialize on module import (safe, creates dirs only if needed)
initialize_directories()


# ============================================================================
# Environment Variable Support
# ============================================================================

def get_service_url(service_name: str, default: str) -> str:
    """
    Get service URL from environment variables with fallback to default.

    Args:
        service_name: Name of the service (e.g., "MARKER", "MINERU")
        default: Default URL if not set in environment

    Returns:
        str: Service URL
    """
    env_var = f"{service_name}_SERVICE_URL"
    return os.getenv(env_var, default)


# Service URLs (configurable via environment variables)
MARKER_SERVICE_URL = get_service_url("MARKER", "http://localhost:8002")
MINERU_SERVICE_URL = get_service_url("MINERU", "http://localhost:8003")
GROBID_SERVICE_URL = get_service_url("GROBID", "https://kermitt2-grobid.hf.space")


# ============================================================================
# Path Validation
# ============================================================================

def validate_paths():
    """
    Validate that all critical paths are accessible and writable.
    Raises exceptions if there are issues.
    """
    # Check DATA_ROOT is writable
    if not os.access(DATA_ROOT, os.W_OK):
        raise PermissionError(f"Data directory not writable: {DATA_ROOT}")

    # Check all required directories exist (should be created by initialize_directories)
    required = [PAPERS_DIR, BOOK_REPOSITORY, RAG_INDEX_PATH, VECTOR_STORE_PATH]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(f"Required directory does not exist: {path}")


if __name__ == "__main__":
    # For debugging: print all paths
    print("SmartTrendTracer Path Configuration")
    print("=" * 60)
    print(f"Project Root:     {PROJECT_ROOT}")
    print(f"Backend Root:     {BACKEND_ROOT}")
    print(f"Data Root:        {DATA_ROOT}")
    print()
    print("Data Directories:")
    print(f"  Papers:         {PAPERS_DIR}")
    print(f"  Paper Repo:     {PAPER_REPOSITORY}")
    print(f"  Books:          {BOOK_REPOSITORY}")
    print(f"  Articles:       {ARTICLE_IMAGES}")
    print()
    print("Vector Stores:")
    print(f"  RAG Index:      {RAG_INDEX_PATH}")
    print(f"  Vector Store:   {VECTOR_STORE_PATH}")
    print()
    print("MongoDB Sync:")
    print(f"  Sync Dir:       {MONGODB_SYNC}")
    print()
    print("Service URLs:")
    print(f"  Marker:         {MARKER_SERVICE_URL}")
    print(f"  MinerU:         {MINERU_SERVICE_URL}")
    print(f"  GROBID:         {GROBID_SERVICE_URL}")
    print()

    # Validate
    try:
        validate_paths()
        print("✅ All paths validated successfully")
    except Exception as e:
        print(f"❌ Path validation failed: {e}")
