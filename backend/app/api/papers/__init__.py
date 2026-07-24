"""
Papers API package - split from monolithic papers_mongodb.py.

Sub-modules:
- crud: List, get, create, update content, delete, upload papers
- metadata: Metadata update, flag toggle, rating, field patching
- facets: Faceted search, statistics, DBLP search
- processing: Marker, MinerU processing + progress tracking
- analysis: AI-powered paper analyses (14+ types) — create, retrieve, list available/saved
- analysis_management: Free-form analyses CRUD, update/delete generated analyses
- analysis_generation: Analysis generation (single; frontend iterates sequentially)
- entities: Entity extraction
- tag_suggestions: AI-powered tag/concept suggestions
- affiliations: Affiliation extraction and application
- bulk_ops: Bulk operations on entities
- concepts: Concept/tag management
- content: Snippets, sections, references, TEI XML, PDF serving, LLM section extraction
- content_media: Image serving for processed papers (Marker, MinerU)
- grobid: GROBID TEI processing and metadata
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .metadata import router as metadata_router
from .facets import router as facets_router
from .processing import router as processing_router
from .analysis import router as analysis_router
from .analysis_management import router as analysis_management_router
from .analysis_generation import router as analysis_generation_router
from .entities import router as entities_router
from .tag_suggestions import router as tag_suggestions_router
from .affiliations import router as affiliations_router
from .bulk_ops import router as bulk_ops_router
from .concepts import router as concepts_router
from .content import router as content_router
from .content_media import router as content_media_router
from .grobid import router as grobid_router

router = APIRouter()

# Static-path routers first, parametric catch-all last
router.include_router(facets_router)
router.include_router(processing_router)
router.include_router(analysis_router)
router.include_router(analysis_management_router)
router.include_router(analysis_generation_router)
router.include_router(entities_router)
router.include_router(tag_suggestions_router)
router.include_router(affiliations_router)
router.include_router(bulk_ops_router)
router.include_router(concepts_router)
router.include_router(content_router)
router.include_router(content_media_router)
router.include_router(grobid_router)
router.include_router(metadata_router)   # /{paper_id}/metadata, /flag, /rating, PATCH
router.include_router(crud_router)       # /{paper_id} LAST
