"""
Tag Ontology v2 API package - MongoDB Implementation.
Handles all tag concept operations using MongoDB.

Sub-modules:
- concepts: Tree, hierarchy, list, detail, simple CRUD for concepts
- concepts_ontology: ObjectId-based concept create, update, delete
- aliases_and_search: Alias management, concept search, find by name
- tools: Statistics, graph visualization, export, mapping rebuild
"""

from fastapi import APIRouter

from .concepts import router as concepts_router
from .concepts_ontology import router as concepts_ontology_router
from .aliases_and_search import router as aliases_search_router
from .tools import router as tools_router

router = APIRouter()

router.include_router(concepts_router)
router.include_router(concepts_ontology_router)
router.include_router(aliases_search_router)
router.include_router(tools_router)
