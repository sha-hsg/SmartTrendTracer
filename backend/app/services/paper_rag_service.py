"""
Service for integrating papers with RAG search system
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
import pickle
import os
from pathlib import Path
import numpy as np
import faiss
from openai import OpenAI

# Get OpenAI API key from environment
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

logger = logging.getLogger(__name__)

class PaperRAGService:
    def __init__(self, index_path: str = "data/rag_index"):
        """Initialize the Paper RAG service"""
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client for embeddings
        self.client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        
        # Load or create index
        self.load_or_create_index()
    
    def load_or_create_index(self):
        """Load existing index or create a new one"""
        try:
            # Try to load existing index
            index_file = self.index_path / "faiss.index"
            metadata_file = self.index_path / "metadata.pkl"
            doc_map_file = self.index_path / "doc_map.pkl"
            
            if index_file.exists() and metadata_file.exists() and doc_map_file.exists():
                self.index = faiss.read_index(str(index_file))
                with open(metadata_file, 'rb') as f:
                    loaded_metadata = pickle.load(f)
                    # Handle both list and dict formats for compatibility
                    if isinstance(loaded_metadata, list):
                        self.metadata = loaded_metadata
                        self.metadata_dict = {}
                    else:
                        self.metadata_dict = loaded_metadata
                        self.metadata = []
                with open(doc_map_file, 'rb') as f:
                    self.doc_map = pickle.load(f)
                logger.info(f"Loaded existing RAG index with {self.index.ntotal} documents")
            else:
                # Create new index
                self.index = faiss.IndexFlatL2(1536)  # OpenAI embedding dimension
                self.metadata = []
                self.metadata_dict = {}
                self.doc_map = {}
                logger.info("Created new RAG index")
                
        except Exception as e:
            logger.error(f"Error loading RAG index: {e}")
            # Create new index on error
            self.index = faiss.IndexFlatL2(1536)
            self.metadata = []
            self.metadata_dict = {}
            self.doc_map = {}
    
    def save_index(self):
        """Save the index to disk"""
        try:
            index_file = self.index_path / "faiss.index"
            metadata_file = self.index_path / "metadata.pkl"
            doc_map_file = self.index_path / "doc_map.pkl"
            
            faiss.write_index(self.index, str(index_file))
            with open(metadata_file, 'wb') as f:
                # Save in dict format for compatibility with main RAG service
                if self.metadata_dict:
                    pickle.dump(self.metadata_dict, f)
                else:
                    # Convert list to dict if needed
                    metadata_as_dict = {}
                    for i, meta in enumerate(self.metadata):
                        if isinstance(meta, dict) and 'id' in meta:
                            metadata_as_dict[meta['id']] = meta
                    pickle.dump(metadata_as_dict, f)
            with open(doc_map_file, 'wb') as f:
                pickle.dump(self.doc_map, f)
            
            # Update index info
            info_file = self.index_path / "index_info.json"
            import json
            with open(info_file, 'w') as f:
                json.dump({
                    "total_documents": self.index.ntotal,
                    "last_updated": datetime.now().isoformat(),
                    "embedding_model": "text-embedding-ada-002"
                }, f, indent=2)
            
            logger.info(f"Saved RAG index with {self.index.ntotal} documents")
            
        except Exception as e:
            logger.error(f"Error saving RAG index: {e}")
    
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for text using OpenAI"""
        if not self.client:
            logger.warning("OpenAI client not initialized")
            return None
        
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None
    
    def add_paper_to_index(self, db: Session, paper_id: int) -> bool:
        """Add a paper to the RAG index by rebuilding the main index"""
        try:
            # Verify paper exists
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if not paper:
                logger.error(f"Paper {paper_id} not found")
                return False
            
            # For simplicity, just rebuild the main RAG index
            # In production, you'd want incremental updates
            from app.services.rag_service import RAGService
            
            logger.info(f"Rebuilding RAG index to include paper {paper_id}")
            rag_service = RAGService(db)
            result = rag_service.rebuild_index()
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Error adding paper to index: {str(e)}", exc_info=True)
            return False
    
    def add_papers_batch(self, db: Session, paper_ids: List[int]) -> Dict[str, int]:
        """Add multiple papers to the index"""
        results = {"success": 0, "failed": 0}
        
        for paper_id in paper_ids:
            if self.add_paper_to_index(db, paper_id):
                results["success"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"Batch indexing complete: {results}")
        return results
    
    def search_papers(self, query: str, k: int = 10) -> List[Dict]:
        """Search for papers similar to the query"""
        try:
            # Use the main RAG service for searching
            from app.services.rag_service import RAGService
            
            rag_service = RAGService(db)
            
            # Search using main RAG service
            search_results = rag_service.search(query, k=k*2)  # Get more results to filter
            
            # Filter to only paper results
            paper_results = []
            for result in search_results:
                if result.source_type == 'paper':
                    paper_results.append({
                        'type': 'paper',
                        'paper_id': int(result.source_id),
                        'score': result.score,
                        'title': result.metadata.get('title', 'Untitled'),
                        'authors': result.metadata.get('authors', []),
                        'abstract': result.content[:500] if result.content else None,
                        'metadata': result.metadata
                    })
                    
                if len(paper_results) >= k:
                    break
            
            return paper_results
            
        except Exception as e:
            logger.error(f"Error searching papers: {str(e)}", exc_info=True)
            return []
    
    def update_all_papers(self, db: Session) -> Dict[str, int]:
        """Update the index with all papers in the database"""
        try:
            # Just rebuild the main RAG index which includes papers
            from app.services.rag_service import RAGService
            
            logger.info("Rebuilding main RAG index to include papers")
            rag_service = RAGService(db)
            result = rag_service.rebuild_index()
            
            if result.get('success'):
                # Count papers in the rebuilt index
                stats = rag_service.get_stats()
                paper_count = stats.get('documents_by_type', {}).get('paper', 0)
                return {"success": paper_count, "failed": 0}
            else:
                return {"success": 0, "failed": 1}
            
        except Exception as e:
            logger.error(f"Error updating all papers: {str(e)}", exc_info=True)
            return {"success": 0, "failed": 0}
    
    def get_index_stats(self) -> Dict:
        """Get statistics about the RAG index"""
        paper_count = sum(1 for m in self.metadata if m.get("type") == "paper")
        tweet_count = sum(1 for m in self.metadata if m.get("type") == "tweet")
        article_count = sum(1 for m in self.metadata if m.get("type") == "article")
        
        return {
            "total_documents": self.index.ntotal,
            "papers": paper_count,
            "tweets": tweet_count,
            "articles": article_count,
            "last_updated": datetime.now().isoformat()
        }