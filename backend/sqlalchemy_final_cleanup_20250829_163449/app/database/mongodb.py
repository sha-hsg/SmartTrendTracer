"""
MongoDB configuration and connection management
"""
import os
from typing import Optional, Dict, Any
from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.database import Database
from pymongo.collection import Collection
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

class MongoDBManager:
    """Manages MongoDB connections and collections"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self._collections: Dict[str, Collection] = {}
        
    def connect(self, 
                uri: str = None,
                database: str = "smarttrendtracer") -> Database:
        """
        Connect to MongoDB
        
        Args:
            uri: MongoDB connection string (defaults to local)
            database: Database name
        """
        if not uri:
            # Default to local MongoDB
            uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        
        try:
            self.client = MongoClient(uri)
            self.db = self.client[database]
            
            # Test connection
            self.client.server_info()
            logger.info(f"Connected to MongoDB: {database}")
            
            # Initialize collections
            self._init_collections()
            
            return self.db
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _init_collections(self):
        """Initialize collections with indexes"""
        if not self.db:
            raise Exception("Not connected to MongoDB")
        
        # Tag Concepts Collection
        concepts = self.db.concepts
        concepts.create_index([("slug", ASCENDING)], unique=True)
        concepts.create_index([("status", ASCENDING)])
        concepts.create_index([("entity_type", ASCENDING)])
        concepts.create_index([("parents", ASCENDING)])
        concepts.create_index([("display_name", TEXT)])
        self._collections["concepts"] = concepts
        
        # Aliases Collection
        aliases = self.db.aliases
        aliases.create_index([("alias_text", ASCENDING)], unique=True)
        aliases.create_index([("concept_id", ASCENDING)])
        aliases.create_index([("alias_type", ASCENDING)])
        self._collections["aliases"] = aliases
        
        # Relations Collection
        relations = self.db.relations
        relations.create_index([("source_id", ASCENDING)])
        relations.create_index([("target_id", ASCENDING)])
        relations.create_index([("relation_type", ASCENDING)])
        relations.create_index([
            ("source_id", ASCENDING),
            ("target_id", ASCENDING),
            ("relation_type", ASCENDING)
        ], unique=True)
        self._collections["relations"] = relations
        
        # Reorganization Proposals Collection
        proposals = self.db.reorganization_proposals
        proposals.create_index([("proposal_id", ASCENDING)], unique=True)
        proposals.create_index([("status", ASCENDING)])
        proposals.create_index([("created_at", ASCENDING)])
        self._collections["proposals"] = proposals
        
        # Tag Instances Collection (actual tag usage)
        instances = self.db.tag_instances
        instances.create_index([("content_type", ASCENDING)])
        instances.create_index([("content_id", ASCENDING)])
        instances.create_index([("concept_id", ASCENDING)])
        instances.create_index([("original_text", ASCENDING)])
        self._collections["instances"] = instances
        
        logger.info(f"Initialized {len(self._collections)} collections")
    
    def get_collection(self, name: str) -> Collection:
        """Get a collection by name"""
        if name in self._collections:
            return self._collections[name]
        elif self.db:
            return self.db[name]
        else:
            raise Exception(f"Collection {name} not found and DB not connected")
    
    @property
    def concepts(self) -> Collection:
        """Get concepts collection"""
        return self.get_collection("concepts")
    
    @property
    def aliases(self) -> Collection:
        """Get aliases collection"""
        return self.get_collection("aliases")
    
    @property
    def relations(self) -> Collection:
        """Get relations collection"""
        return self.get_collection("relations")
    
    @property
    def proposals(self) -> Collection:
        """Get proposals collection"""
        return self.get_collection("proposals")
    
    @property
    def instances(self) -> Collection:
        """Get tag instances collection"""
        return self.get_collection("instances")
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Singleton instance
_mongodb = MongoDBManager()

def get_mongodb() -> MongoDBManager:
    """Get MongoDB manager instance"""
    global _mongodb
    if not _mongodb.db:
        _mongodb.connect()
    return _mongodb

def get_db() -> Database:
    """Get MongoDB database instance"""
    return get_mongodb().db