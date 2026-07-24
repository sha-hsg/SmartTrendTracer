import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.llm_manager import get_llm_manager

from app.services.rag.index_manager import (
    init_embedding_clients,
    get_index_paths,
    load_index as _load_index,
    rebuild_index as _rebuild_index,
    get_stats as _get_stats,
    get_sample_questions as _get_sample_questions,
)
from app.services.rag.search import search as _search
from app.services.rag.trend_analysis import (
    is_trend_query,
    analyze_trends as _analyze_trends,
    ask as _ask,
)

logger = logging.getLogger(__name__)


class ConceptBasedRAGService:
    """RAG Service that uses MongoDB concepts for better semantic search"""

    def __init__(self, db=None):
        from app.database.mongodb import get_client, get_database

        self.mongo_client = get_client()
        self.db = get_database()
        self.concept_service = ConceptOnlyTagService()
        self.llm_manager = get_llm_manager()
        self.user_id = "default"

        google_api_key = os.getenv('GOOGLE_API_KEY')
        openai_api_key = os.getenv('OPENAI_API_KEY')
        self.use_gemini_embeddings, self.openai_client = init_embedding_clients(google_api_key, openai_api_key)

        self.index_dir = Path("data/rag_index_concepts")
        self.paths = get_index_paths(self.index_dir)

        self.embeddings_cache = {}

        self.load_index()

    def load_index(self):
        self.index, self.metadata, self.doc_map = _load_index(self.paths)

    def rebuild_index(self):
        self.index, self.metadata, self.doc_map, index_info = _rebuild_index(
            self.db, self.concept_service, self.use_gemini_embeddings,
            self.openai_client, self.paths, self.embeddings_cache
        )
        return index_info

    def search(self, query: str, k: int = 10, concept_filter: Optional[List[str]] = None,
               content_types: Optional[List[str]] = None) -> List[Dict]:
        return _search(
            self.index, self.metadata, self.doc_map,
            self.use_gemini_embeddings, self.openai_client, self.embeddings_cache,
            query, k=k, concept_filter=concept_filter, content_types=content_types
        )

    def ask(self, question: str, k: int = 10, use_concepts: bool = True,
            content_types: Optional[List[str]] = None,
            concept_filter: Optional[List[str]] = None,
            model: Optional[str] = None) -> Dict[str, Any]:
        return _ask(
            self.search, self.llm_manager, self.user_id,
            question, k=k, use_concepts=use_concepts,
            content_types=content_types, concept_filter=concept_filter,
            model=model
        )

    def is_trend_query(self, question: str) -> bool:
        return is_trend_query(question)

    def analyze_trends(self, question: str, content_types: Optional[List[str]] = None,
                       k: int = 50, model: Optional[str] = None) -> Dict[str, Any]:
        return _analyze_trends(
            self.search, self.llm_manager, self.user_id,
            question, content_types=content_types, k=k, model=model
        )

    def get_stats(self) -> Dict[str, Any]:
        return _get_stats(self.index, self.paths)

    def get_sample_questions(self) -> List[str]:
        return _get_sample_questions(self.concept_service)
