"""
Ontology Graph API - Provides graph data for visualization
MongoDB version
"""
from fastapi import APIRouter, Query
import logging
from app.database.mongodb import get_database
from app.repositories import ontology_graph as repo

logger = logging.getLogger(__name__)

# MongoDB connection
db = get_database()

router = APIRouter()


@router.get("/data")
def get_graph_data(
    include_orphans: bool = Query(True),
    min_usage: int = Query(0)
):
    """
    Get ontology graph data in format suitable for force-directed graph.
    
    Returns:
        nodes: List of concepts with metadata
        links: List of parent-child relationships
    """
    return repo.get_graph_data(include_orphans=include_orphans, min_usage=min_usage)
