"""
DEPRECATED: Tag service using SQLite v2 tables

⚠️  DEPRECATED AS OF JANUARY 24, 2025 ⚠️
This service is deprecated after the complete MongoDB migration.

REPLACEMENT: Use ConceptOnlyTagService instead
- Location: app/services/concept_only_tag_service.py
- Reason: Full system migration to MongoDB - no SQLite fallback needed
- Status: MongoDB is now primary and only database

DO NOT USE in new code. This file is preserved for reference only.
Legacy usage found in:
- app/api/tag_import_export.py

Migration completed: January 24, 2025
"""
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import get_db

logger = logging.getLogger(__name__)

class TagServiceV2:
    """Service for managing tags using SQLite v2 tables"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
    
    def export_ontology(self, include_instances: bool = False, include_proposals: bool = False) -> Dict[str, Any]:
        """Export the complete tag ontology structure"""
        try:
            export_data = {
                "version": "2.0",
                "exported_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "total_concepts": 0,
                    "total_aliases": 0,
                    "total_relations": 0,
                    "total_instances": 0,
                    "root_concepts": []
                },
                "concepts": [],
                "aliases": [],
                "relations": []
            }
            
            # Export concepts
            concepts = self.db.execute(text("SELECT * FROM tag_concepts_v2")).fetchall()
            for row in concepts:
                concept = {
                    "id": row.id,
                    "slug": row.slug,
                    "display_name": row.display_name,
                    "description": row.description,
                    "status": row.status,
                    "usage_count": row.usage_count,
                    "icon": row.icon,
                    "color": row.color,
                    "parents": json.loads(row.parents) if row.parents else [],
                    "children": json.loads(row.children) if row.children else [],
                    "level": row.level,
                    "entity_type": row.entity_type,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at
                }
                export_data['concepts'].append(concept)
            
            # Export aliases
            aliases = self.db.execute(text("SELECT * FROM tag_aliases_v2")).fetchall()
            for row in aliases:
                alias = {
                    "alias_text": row.alias_text,
                    "concept_id": row.concept_id,
                    "alias_type": row.alias_type,
                    "confidence": row.confidence,
                    "created_at": row.created_at
                }
                export_data['aliases'].append(alias)
            
            # Export relations
            relations = self.db.execute(text("SELECT * FROM tag_relations_v2")).fetchall()
            for row in relations:
                relation = {
                    "source_id": row.source_id,
                    "target_id": row.target_id,
                    "relation_type": row.relation_type,
                    "confidence": row.confidence,
                    "created_at": row.created_at
                }
                export_data['relations'].append(relation)
            
            # Optionally export instances
            if include_instances:
                export_data['instances'] = []
                # Export tweet tags
                tweet_tags = self.db.execute(text("""
                    SELECT 'tweet' as content_type, tt.tweet_id as content_id,
                           t.tag as original_text, t.tag as display_name, 'manual' as tag_type
                    FROM tweet_tags tt
                    JOIN tags t ON tt.tag_id = t.id
                """)).fetchall()
                
                for row in tweet_tags:
                    instance = {
                        "content_type": row.content_type,
                        "content_id": str(row.content_id),
                        "original_text": row.original_text,
                        "display_name": row.display_name,
                        "tag_type": row.tag_type,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    export_data['instances'].append(instance)
                
                # Export paper tags
                paper_tags = self.db.execute(text("""
                    SELECT 'paper' as content_type, pt.paper_id as content_id,
                           t.tag as original_text, t.tag as display_name, pt.tag_type
                    FROM paper_tags pt
                    JOIN tags t ON pt.tag_id = t.id
                """)).fetchall()
                
                for row in paper_tags:
                    instance = {
                        "content_type": row.content_type,
                        "content_id": str(row.content_id),
                        "original_text": row.original_text,
                        "display_name": row.display_name,
                        "tag_type": row.tag_type or 'manual',
                        "created_at": datetime.utcnow().isoformat()
                    }
                    export_data['instances'].append(instance)
                
                # Export article tags
                article_tags = self.db.execute(text("""
                    SELECT 'article' as content_type, at.article_id as content_id,
                           t.tag as original_text, t.tag as display_name, 'manual' as tag_type
                    FROM article_tags at
                    JOIN tags t ON at.tag_id = t.id
                """)).fetchall()
                
                for row in article_tags:
                    instance = {
                        "content_type": row.content_type,
                        "content_id": str(row.content_id),
                        "original_text": row.original_text,
                        "display_name": row.display_name,
                        "tag_type": row.tag_type,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    export_data['instances'].append(instance)
                
                export_data['metadata']['total_instances'] = len(export_data['instances'])
            
            # Optionally export proposals
            if include_proposals:
                export_data['proposals'] = []
                proposals = self.db.execute(text("SELECT * FROM tag_reorganization_proposals")).fetchall()
                for row in proposals:
                    proposal = {
                        "proposal_id": row.proposal_id,
                        "version": row.version,
                        "model_used": row.model_used,
                        "total_tags": row.total_tags,
                        "confidence_score": row.confidence_score,
                        "reasoning": row.reasoning,
                        "concepts": json.loads(row.concepts) if row.concepts else [],
                        "aliases": json.loads(row.aliases) if row.aliases else [],
                        "relations": json.loads(row.relations) if row.relations else [],
                        "root_categories": json.loads(row.root_categories) if row.root_categories else [],
                        "merge_proposals": json.loads(row.merge_proposals) if row.merge_proposals else [],
                        "governance": json.loads(row.governance) if row.governance else {},
                        "validation": json.loads(row.validation) if row.validation else {},
                        "status": row.status,
                        "applied_at": row.applied_at,
                        "applied_by": row.applied_by,
                        "created_at": row.created_at
                    }
                    export_data['proposals'].append(proposal)
            
            # Update metadata
            export_data['metadata']['total_concepts'] = len(export_data['concepts'])
            export_data['metadata']['total_aliases'] = len(export_data['aliases'])
            export_data['metadata']['total_relations'] = len(export_data['relations'])
            
            # Find root concepts
            root_concepts = [
                c['id'] for c in export_data['concepts'] 
                if not c.get('parents') or len(c.get('parents', [])) == 0
            ]
            export_data['metadata']['root_concepts'] = root_concepts
            
            logger.info(f"Exported {len(export_data['concepts'])} concepts, "
                       f"{len(export_data['aliases'])} aliases, "
                       f"{len(export_data['relations'])} relations")
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting ontology: {e}")
            raise
    
    def import_ontology(self, import_data: Dict[str, Any], merge_mode: str = "replace",
                       backup_existing: bool = True) -> Dict[str, Any]:
        """Import tag ontology from JSON data"""
        try:
            stats = {
                "concepts_imported": 0,
                "aliases_imported": 0,
                "relations_imported": 0,
                "instances_imported": 0
            }
            
            # Backup existing data if requested
            if backup_existing:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                # Create backup tables
                self.db.execute(text(f"CREATE TABLE IF NOT EXISTS tag_concepts_v2_backup_{timestamp} AS SELECT * FROM tag_concepts_v2"))
                self.db.execute(text(f"CREATE TABLE IF NOT EXISTS tag_aliases_v2_backup_{timestamp} AS SELECT * FROM tag_aliases_v2"))
                self.db.execute(text(f"CREATE TABLE IF NOT EXISTS tag_relations_v2_backup_{timestamp} AS SELECT * FROM tag_relations_v2"))
                logger.info(f"Created backup with timestamp {timestamp}")
            
            # Import based on merge mode
            if merge_mode == "replace":
                # Clear existing data
                self.db.execute(text("DELETE FROM tag_relations_v2"))
                self.db.execute(text("DELETE FROM tag_aliases_v2"))
                self.db.execute(text("DELETE FROM tag_concepts_v2"))
            
            # Import concepts
            for concept_data in import_data.get('concepts', []):
                parents_json = json.dumps(concept_data.get('parents', []))
                children_json = json.dumps(concept_data.get('children', []))
                
                if merge_mode == "merge":
                    # Update or insert
                    self.db.execute(text("""
                        INSERT OR REPLACE INTO tag_concepts_v2 
                        (id, slug, display_name, description, status, usage_count, 
                         icon, color, parents, children, level, entity_type, created_at, updated_at)
                        VALUES (:id, :slug, :display_name, :description, :status, :usage_count,
                                :icon, :color, :parents, :children, :level, :entity_type, :created_at, :updated_at)
                    """), {
                        "id": concept_data['id'],
                        "slug": concept_data['slug'],
                        "display_name": concept_data['display_name'],
                        "description": concept_data.get('description'),
                        "status": concept_data.get('status', 'active'),
                        "usage_count": concept_data.get('usage_count', 0),
                        "icon": concept_data.get('icon'),
                        "color": concept_data.get('color'),
                        "parents": parents_json,
                        "children": children_json,
                        "level": concept_data.get('level', 0),
                        "entity_type": concept_data.get('entity_type'),
                        "created_at": concept_data.get('created_at', datetime.utcnow().isoformat()),
                        "updated_at": concept_data.get('updated_at', datetime.utcnow().isoformat())
                    })
                else:  # replace or skip_existing
                    self.db.execute(text("""
                        INSERT INTO tag_concepts_v2 
                        (id, slug, display_name, description, status, usage_count, 
                         icon, color, parents, children, level, entity_type, created_at, updated_at)
                        VALUES (:id, :slug, :display_name, :description, :status, :usage_count,
                                :icon, :color, :parents, :children, :level, :entity_type, :created_at, :updated_at)
                    """), {
                        "id": concept_data['id'],
                        "slug": concept_data['slug'],
                        "display_name": concept_data['display_name'],
                        "description": concept_data.get('description'),
                        "status": concept_data.get('status', 'active'),
                        "usage_count": concept_data.get('usage_count', 0),
                        "icon": concept_data.get('icon'),
                        "color": concept_data.get('color'),
                        "parents": parents_json,
                        "children": children_json,
                        "level": concept_data.get('level', 0),
                        "entity_type": concept_data.get('entity_type'),
                        "created_at": concept_data.get('created_at', datetime.utcnow().isoformat()),
                        "updated_at": concept_data.get('updated_at', datetime.utcnow().isoformat())
                    })
                
                stats["concepts_imported"] += 1
            
            # Import aliases
            for alias_data in import_data.get('aliases', []):
                if merge_mode == "merge":
                    self.db.execute(text("""
                        INSERT OR REPLACE INTO tag_aliases_v2 
                        (alias_text, concept_id, alias_type, confidence, created_at)
                        VALUES (:alias_text, :concept_id, :alias_type, :confidence, :created_at)
                    """), {
                        "alias_text": alias_data['alias_text'],
                        "concept_id": alias_data['concept_id'],
                        "alias_type": alias_data['alias_type'],
                        "confidence": alias_data.get('confidence', 1.0),
                        "created_at": alias_data.get('created_at', datetime.utcnow().isoformat())
                    })
                else:
                    self.db.execute(text("""
                        INSERT INTO tag_aliases_v2 
                        (alias_text, concept_id, alias_type, confidence, created_at)
                        VALUES (:alias_text, :concept_id, :alias_type, :confidence, :created_at)
                    """), {
                        "alias_text": alias_data['alias_text'],
                        "concept_id": alias_data['concept_id'],
                        "alias_type": alias_data['alias_type'],
                        "confidence": alias_data.get('confidence', 1.0),
                        "created_at": alias_data.get('created_at', datetime.utcnow().isoformat())
                    })
                
                stats["aliases_imported"] += 1
            
            # Import relations
            for relation_data in import_data.get('relations', []):
                self.db.execute(text("""
                    INSERT INTO tag_relations_v2 
                    (source_id, target_id, relation_type, confidence, created_at)
                    VALUES (:source_id, :target_id, :relation_type, :confidence, :created_at)
                """), {
                    "source_id": relation_data['source_id'],
                    "target_id": relation_data['target_id'],
                    "relation_type": relation_data['relation_type'],
                    "confidence": relation_data.get('confidence', 1.0),
                    "created_at": relation_data.get('created_at', datetime.utcnow().isoformat())
                })
                
                stats["relations_imported"] += 1
            
            self.db.commit()
            
            logger.info(f"Imported {stats['concepts_imported']} concepts, "
                       f"{stats['aliases_imported']} aliases, "
                       f"{stats['relations_imported']} relations")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error importing ontology: {e}")
            self.db.rollback()
            raise
    
    def validate_ontology(self) -> Dict[str, Any]:
        """Validate the current tag ontology for consistency"""
        try:
            issues = []
            warnings = []
            
            # Get all concepts
            concepts = self.db.execute(text("SELECT * FROM tag_concepts_v2")).fetchall()
            concept_dict = {c.id: c for c in concepts}
            concept_ids = set(concept_dict.keys())
            
            # Check for orphaned aliases
            aliases = self.db.execute(text("SELECT * FROM tag_aliases_v2")).fetchall()
            for alias in aliases:
                if alias.concept_id not in concept_ids:
                    issues.append(f"Orphaned alias '{alias.alias_text}' references non-existent concept '{alias.concept_id}'")
            
            # Check for broken parent references
            for concept in concepts:
                parents = json.loads(concept.parents) if concept.parents else []
                for parent_id in parents:
                    if parent_id not in concept_ids:
                        issues.append(f"Concept '{concept.id}' has non-existent parent '{parent_id}'")
                
                children = json.loads(concept.children) if concept.children else []
                for child_id in children:
                    if child_id not in concept_ids:
                        issues.append(f"Concept '{concept.id}' has non-existent child '{child_id}'")
            
            # Check for mismatched parent-child relationships
            for concept in concepts:
                children = json.loads(concept.children) if concept.children else []
                for child_id in children:
                    if child_id in concept_dict:
                        child = concept_dict[child_id]
                        child_parents = json.loads(child.parents) if child.parents else []
                        if concept.id not in child_parents:
                            warnings.append(f"Parent-child mismatch: '{concept.id}' lists '{child_id}' as child but not vice versa")
            
            # Check for duplicate slugs
            slug_count = self.db.execute(text("""
                SELECT slug, COUNT(*) as count 
                FROM tag_concepts_v2 
                GROUP BY slug 
                HAVING COUNT(*) > 1
            """)).fetchall()
            
            for row in slug_count:
                issues.append(f"Duplicate slug '{row.slug}' used by {row.count} concepts")
            
            return {
                "valid": len(issues) == 0,
                "total_concepts": len(concepts),
                "total_aliases": len(aliases),
                "issues": issues,
                "warnings": warnings,
                "summary": {
                    "critical_issues": len(issues),
                    "warnings": len(warnings)
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating ontology: {e}")
            raise


# Singleton instance
_tag_service_v2 = None

def get_tag_service_v2(db: Session = None) -> TagServiceV2:
    """Get the SQLite v2 tag service instance"""
    global _tag_service_v2
    if _tag_service_v2 is None:
        _tag_service_v2 = TagServiceV2(db)
    return _tag_service_v2