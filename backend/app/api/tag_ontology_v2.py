"""
API endpoints for managing tag ontology v2 with concept structure
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
import json

router = APIRouter()

# Pydantic models for v2 structure
    slug: str
    display_name: str
    description: Optional[str] = None
    entity_type: Optional[str] = None
    parent_ids: List[str] = []
    icon: Optional[str] = None
    color: Optional[str] = None

    display_name: Optional[str] = None
    description: Optional[str] = None
    entity_type: Optional[str] = None
    parent_ids: Optional[List[str]] = None
    icon: Optional[str] = None
    color: Optional[str] = None

    alias_text: str
    alias_type: str = "synonym"
    confidence: float = 1.0

    id: str
    slug: str
    display_name: str
    description: Optional[str]
    entity_type: Optional[str]
    parents: List[str]
    children: List[str]
    level: int
    icon: Optional[str]
    color: Optional[str]
    usage_count: int
    created_at: str
    updated_at: str

    id: str
    slug: str
    display_name: str
    description: Optional[str]
    entity_type: Optional[str]
    parents: List[str]
    children: List[str]
    level: int
    icon: Optional[str]
    color: Optional[str]
    usage_count: int
    tweet_count: int
    article_count: int
    paper_count: int
    aliases: List[Dict[str, Any]]

def _convert_to_frontend_format(node: Dict, db = None) -> Dict:
    """Convert v2 concept to frontend format with string IDs"""
    frontend_node = {
        "id": node["id"],  # Keep string ID as-is
        "tag": node["slug"],
        "display_name": node["display_name"],
        "description": node.get("description"),
        "child_count": len(node.get("children", [])),
        "descendant_count": len(node.get("children", [])),  # Simplified
        "synonyms": [],  # Initialize empty, will populate if db provided
        "entity_type": node.get("entity_type"),
        "icon": node.get("icon"),
        "color": node.get("color")
    }
    
    # Fetch aliases/synonyms if db connection available
    if db:
        try:
            alias_result = db.execute(text("""
                SELECT alias_text FROM tag_aliases_v2
                WHERE concept_id = :concept_id
            """), {"concept_id": node["id"]})
            frontend_node["synonyms"] = [row[0] for row in alias_result]
        except:
            pass  # Keep empty array on error
    
    # Recursively convert children
    if "children_concepts" in node and node["children_concepts"]:
        frontend_node["children"] = [
            _convert_to_frontend_format(child, db) 
            for child in node["children_concepts"]
        ]
    elif node.get("children"):
        frontend_node["children"] = []
    
    return frontend_node

@router.get("/tree")
    """Get the complete tag tree - returns array for frontend compatibility"""
    hierarchy = get_hierarchy(db)
    # Convert to frontend format with string IDs and include synonyms
    root_concepts = hierarchy.get("root_concepts", [])
    return [_convert_to_frontend_format(node, db) for node in root_concepts]

@router.get("/hierarchy")
    """Get the complete tag hierarchy from v2 tables"""
    try:
        # Get all concepts
        result = db.execute(text("""
            SELECT id, slug, display_name, description, entity_type,
                   parents, children, level, icon, color, usage_count,
                   created_at, updated_at
            FROM tag_concepts_v2
            WHERE status = 'active' OR status IS NULL
            ORDER BY level, display_name
        """))
        
        concepts = []
        concept_map = {}
        
        for row in result:
            concept = {
                "id": row[0],
                "slug": row[1],
                "display_name": row[2],
                "description": row[3],
                "entity_type": row[4],
                "parents": json.loads(row[5]) if row[5] else [],
                "children": json.loads(row[6]) if row[6] else [],
                "level": row[7] if row[7] is not None else 0,
                "icon": row[8],
                "color": row[9],
                "usage_count": row[10] if row[10] else 0,
                "created_at": str(row[11]) if row[11] else None,
                "updated_at": str(row[12]) if row[12] else None
            }
            concepts.append(concept)
            concept_map[concept["id"]] = concept
        
        # Build hierarchy
        root_concepts = []
        for concept in concepts:
            if not concept["parents"] or len(concept["parents"]) == 0:
                root_concepts.append(concept)
        
        # Add children recursively
        def add_children(parent):
            parent["children_concepts"] = []
            for child_id in parent.get("children", []):
                if child_id in concept_map:
                    child = concept_map[child_id].copy()
                    parent["children_concepts"].append(child)
                    add_children(child)
        
        for root in root_concepts:
            add_children(root)
        
        return {
            "total_concepts": len(concepts),
            "root_concepts": root_concepts,
            "all_concepts": concepts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching hierarchy: {str(e)}")

@router.get("/concepts")
def get_all_concepts(
    include_aliases: bool = Query(False),
):
    """Get all concepts from v2 tables"""
    try:
        # Get concepts
        result = db.execute(text("""
            SELECT id, slug, display_name, description, entity_type,
                   parents, children, level, icon, color, usage_count
            FROM tag_concepts_v2
            WHERE status = 'active' OR status IS NULL
            ORDER BY display_name
        """))
        
        concepts = []
        for row in result:
            concept = {
                "id": row[0],
                "tag": row[1],  # Frontend expects 'tag' field
                "slug": row[1],
                "display_name": row[2],
                "description": row[3],
                "entity_type": row[4],
                "parents": json.loads(row[5]) if row[5] else [],
                "children": json.loads(row[6]) if row[6] else [],
                "level": row[7] if row[7] is not None else 0,
                "icon": row[8],
                "color": row[9],
                "usage_count": row[10] if row[10] else 0,
                "synonyms": []  # Initialize as empty array for frontend compatibility
            }
            
            # Always fetch aliases/synonyms for frontend compatibility
            alias_result = db.execute(text("""
                SELECT alias_text, alias_type, confidence
                FROM tag_aliases_v2
                WHERE concept_id = :concept_id
            """), {"concept_id": concept["id"]})
            
            aliases = [
                {
                    "text": row[0],
                    "type": row[1],
                    "confidence": row[2]
                }
                for row in alias_result
            ]
            
            # Always include synonyms as string array
            concept["synonyms"] = [alias["text"] for alias in aliases]
            
            if include_aliases:
                # Include full alias details if requested
                concept["aliases"] = aliases
            
            concepts.append(concept)
        
        return concepts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching concepts: {str(e)}")

@router.get("/concept/{concept_id}")
def get_concept_detail(
    concept_id: str,
):
    """Get detailed information about a specific concept"""
    try:
        # Now expects string IDs like "c_0001"
        # Get concept
        result = db.execute(text("""
            SELECT id, slug, display_name, description, entity_type,
                   parents, children, level, icon, color, usage_count,
                   created_at, updated_at
            FROM tag_concepts_v2
            WHERE id = :concept_id
        """), {"concept_id": concept_id})
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Concept not found")
        
        concept = {
            "id": row[0],
            "tag": row[1],  # Frontend expects 'tag' field (same as slug)
            "slug": row[1],
            "display_name": row[2],
            "description": row[3],
            "entity_type": row[4],
            "parents": json.loads(row[5]) if row[5] else [],
            "children": json.loads(row[6]) if row[6] else [],
            "level": row[7] if row[7] is not None else 0,
            "icon": row[8],
            "color": row[9],
            "usage_count": row[10] if row[10] else 0,
            "created_at": str(row[11]) if row[11] else None,
            "updated_at": str(row[12]) if row[12] else None,
            "child_count": 0,  # Will be updated
            "descendant_count": 0,  # Will be updated
            "parent_id": None  # Will be updated
        }
        
        # Get parent details
        if concept["parents"] and len(concept["parents"]) > 0:
            # Set parent_id to first parent for compatibility
            concept["parent_id"] = concept["parents"][0]
            
            # Build IN clause with placeholders
            parent_placeholders = ', '.join([f':parent_{i}' for i in range(len(concept["parents"]))])
            parent_params = {f'parent_{i}': pid for i, pid in enumerate(concept["parents"])}
            
            parent_result = db.execute(text(f"""
                SELECT id, slug, display_name, icon, color
                FROM tag_concepts_v2
                WHERE id IN ({parent_placeholders})
            """), parent_params)
            
            parent_rows = list(parent_result)
            concept["parent_details"] = [
                {
                    "id": row[0],
                    "tag": row[1],  # Frontend expects 'tag'
                    "slug": row[1],
                    "display_name": row[2],
                    "icon": row[3],
                    "color": row[4]
                }
                for row in parent_rows
            ]
            
            # Set single parent for frontend compatibility (uses first parent)
            if parent_rows:
                first_parent = parent_rows[0]
                concept["parent"] = {
                    "id": first_parent[0],
                    "tag": first_parent[1],
                    "display_name": first_parent[2]
                }
        else:
            concept["parent_details"] = []
            concept["parent"] = None
        
        # Get children details
        if concept["children"]:
            # Build IN clause with placeholders
            child_placeholders = ', '.join([f':child_{i}' for i in range(len(concept["children"]))])
            child_params = {f'child_{i}': cid for i, cid in enumerate(concept["children"])}
            
            children_result = db.execute(text(f"""
                SELECT id, slug, display_name, icon, color, usage_count
                FROM tag_concepts_v2
                WHERE id IN ({child_placeholders})
                ORDER BY display_name
            """), child_params)
            
            children_list = [
                {
                    "id": row[0],
                    "tag": row[1],  # Frontend expects 'tag'
                    "slug": row[1],
                    "display_name": row[2],
                    "icon": row[3],
                    "color": row[4],
                    "usage_count": row[5] if row[5] else 0,
                    "child_count": 0  # Simplified for now
                }
                for row in children_result
            ]
            concept["children_details"] = children_list
            concept["children"] = children_list  # Frontend expects 'children' not 'children_details'
            concept["child_count"] = len(children_list)
            concept["descendant_count"] = len(children_list)  # Simplified
        else:
            concept["children_details"] = []
            concept["children"] = []
            concept["child_count"] = 0
            concept["descendant_count"] = 0
        
        # Get aliases
        alias_result = db.execute(text("""
            SELECT alias_text, alias_type, confidence, created_at
            FROM tag_aliases_v2
            WHERE concept_id = :concept_id
            ORDER BY alias_text
        """), {"concept_id": concept_id})
        
        concept["aliases"] = [
            {
                "text": row[0],
                "type": row[1],
                "confidence": row[2],
                "created_at": str(row[3]) if row[3] else None
            }
            for row in alias_result
        ]
        
        # Also add synonyms as simple string array for frontend compatibility
        # Always initialize as array even if empty
        concept["synonyms"] = [alias["text"] for alias in concept["aliases"]] if concept["aliases"] else []
        
        # Get usage statistics
        # Count tweets with this concept or its aliases
        tweet_count = 0
        article_count = 0
        paper_count = 0
        
        # Get all possible tag texts (slug + aliases)
        tag_texts = [concept["slug"]]
        tag_texts.extend([a["text"] for a in concept["aliases"]])
        
        # Count tweets
        for tag_text in tag_texts:
            tweet_result = db.execute(text("""
                SELECT COUNT(DISTINCT tweet_id)
                FROM tags
                WHERE LOWER(tag) = LOWER(:tag)
            """), {"tag": tag_text})
            tweet_count += tweet_result.scalar() or 0
            
            # Count articles
            article_result = db.execute(text("""
                SELECT COUNT(DISTINCT article_id)
                FROM article_tags
                WHERE LOWER(tag) = LOWER(:tag)
            """), {"tag": tag_text})
            article_count += article_result.scalar() or 0
            
            # Count papers
            paper_result = db.execute(text("""
                SELECT COUNT(DISTINCT paper_id)
                FROM paper_tags
                WHERE LOWER(tag) = LOWER(:tag)
            """), {"tag": tag_text})
            paper_count += paper_result.scalar() or 0
        
        concept["usage_stats"] = {
            "tweet_count": tweet_count,
            "article_count": article_count,
            "paper_count": paper_count,
            "total_count": tweet_count + article_count + paper_count
        }
        
        return concept
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error fetching concept {concept_id}: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console for debugging
        raise HTTPException(status_code=500, detail=f"Error fetching concept: {str(e)}")

@router.post("/concept")
def create_concept(
    concept: ConceptV2Create,
):
    """Create a new concept in v2 structure"""
    try:
        # Generate concept ID
        result = db.execute(text("SELECT COUNT(*) FROM tag_concepts_v2"))
        count = result.scalar()
        new_id = f"c_{count + 1:04d}"
        
        # Determine level based on parents
        level = 0
        if concept.parent_ids:
            # Get max level of parents
            parent_result = db.execute(text("""
                SELECT MAX(level) FROM tag_concepts_v2
                WHERE id IN :parent_ids
            """), {"parent_ids": tuple(concept.parent_ids)})
            parent_level = parent_result.scalar()
            level = (parent_level or 0) + 1
        
        # Insert concept
        db.execute(text("""
            INSERT INTO tag_concepts_v2 (
                id, slug, display_name, description, entity_type,
                parents, children, level, icon, color, usage_count,
                status, created_at, updated_at
            ) VALUES (
                :id, :slug, :display_name, :description, :entity_type,
                :parents, '[]', :level, :icon, :color, 0,
                'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """), {
            "id": new_id,
            "slug": concept.slug,
            "display_name": concept.display_name,
            "description": concept.description,
            "entity_type": concept.entity_type,
            "parents": json.dumps(concept.parent_ids),
            "level": level,
            "icon": concept.icon,
            "color": concept.color
        })
        
        # Update parent concepts to include this as a child
        for parent_id in concept.parent_ids:
            # Get current children
            result = db.execute(text("""
                SELECT children FROM tag_concepts_v2
                WHERE id = :parent_id
            """), {"parent_id": parent_id})
            
            row = result.fetchone()
            if row:
                children = json.loads(row[0]) if row[0] else []
                if new_id not in children:
                    children.append(new_id)
                    
                    db.execute(text("""
                        UPDATE tag_concepts_v2
                        SET children = :children,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :parent_id
                    """), {
                        "children": json.dumps(children),
                        "parent_id": parent_id
                    })
        
        db.commit()
        
        return {"id": new_id, "message": "Concept created successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating concept: {str(e)}")

@router.put("/concept/{concept_id}")
def update_concept(
    concept_id: str,
    update: ConceptV2Update,
):
    """Update an existing concept"""
    try:
        # Build update query dynamically
        update_fields = []
        params = {"concept_id": concept_id}
        
        if update.display_name is not None:
            update_fields.append("display_name = :display_name")
            params["display_name"] = update.display_name
        
        if update.description is not None:
            update_fields.append("description = :description")
            params["description"] = update.description
        
        if update.entity_type is not None:
            update_fields.append("entity_type = :entity_type")
            params["entity_type"] = update.entity_type
        
        if update.icon is not None:
            update_fields.append("icon = :icon")
            params["icon"] = update.icon
        
        if update.color is not None:
            update_fields.append("color = :color")
            params["color"] = update.color
        
        if update.parent_ids is not None:
            # Handle parent update (more complex due to hierarchy)
            update_fields.append("parents = :parents")
            params["parents"] = json.dumps(update.parent_ids)
            
            # Calculate new level
            if update.parent_ids:
                parent_result = db.execute(text("""
                    SELECT MAX(level) FROM tag_concepts_v2
                    WHERE id IN :parent_ids
                """), {"parent_ids": tuple(update.parent_ids)})
                parent_level = parent_result.scalar()
                level = (parent_level or 0) + 1
            else:
                level = 0
            
            update_fields.append("level = :level")
            params["level"] = level
        
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"""
                UPDATE tag_concepts_v2
                SET {', '.join(update_fields)}
                WHERE id = :concept_id
            """
            
            db.execute(text(query), params)
            db.commit()
        
        return {"message": "Concept updated successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating concept: {str(e)}")

@router.delete("/concept/{concept_id}")
def delete_concept(
    concept_id: str,
):
    """Delete a concept (soft delete by setting status)"""
    try:
        # Set status to deleted
        db.execute(text("""
            UPDATE tag_concepts_v2
            SET status = 'deleted',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :concept_id
        """), {"concept_id": concept_id})
        
        # Remove from parent's children
        db.execute(text("""
            UPDATE tag_concepts_v2
            SET children = (
                SELECT json_group_array(value)
                FROM json_each(children)
                WHERE value != :concept_id
            )
            WHERE children LIKE :pattern
        """), {
            "concept_id": concept_id,
            "pattern": f'%"{concept_id}"%'
        })
        
        db.commit()
        
        return {"message": "Concept deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting concept: {str(e)}")

@router.post("/concept/{concept_id}/alias")
def add_alias(
    concept_id: str,
    alias: AliasCreate,
):
    """Add an alias to a concept"""
    try:
        db.execute(text("""
            INSERT INTO tag_aliases_v2 (
                alias_text, concept_id, alias_type, confidence, created_at
            ) VALUES (
                :alias_text, :concept_id, :alias_type, :confidence, CURRENT_TIMESTAMP
            )
        """), {
            "alias_text": alias.alias_text,
            "concept_id": concept_id,
            "alias_type": alias.alias_type,
            "confidence": alias.confidence
        })
        
        db.commit()
        
        return {"message": "Alias added successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding alias: {str(e)}")

@router.delete("/alias/{alias_text}")
def delete_alias(
    alias_text: str,
):
    """Delete an alias"""
    try:
        db.execute(text("""
            DELETE FROM tag_aliases_v2
            WHERE alias_text = :alias_text
        """), {"alias_text": alias_text})
        
        db.commit()
        
        return {"message": "Alias deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting alias: {str(e)}")

@router.get("/search")
def search_concepts(
    query: str = Query(..., min_length=1),
    include_aliases: bool = Query(True),
):
    """Search for concepts by name or alias"""
    try:
        results = []
        search_pattern = f"%{query}%"
        
        # Search in concepts
        concept_result = db.execute(text("""
            SELECT id, slug, display_name, description, entity_type,
                   icon, color, usage_count
            FROM tag_concepts_v2
            WHERE (LOWER(slug) LIKE LOWER(:pattern)
                   OR LOWER(display_name) LIKE LOWER(:pattern))
                  AND (status = 'active' OR status IS NULL)
            ORDER BY usage_count DESC
            LIMIT 20
        """), {"pattern": search_pattern})
        
        for row in concept_result:
            concept = {
                "id": row[0],
                "tag": row[1],  # Frontend expects 'tag' field
                "slug": row[1],
                "display_name": row[2],
                "description": row[3],
                "entity_type": row[4],
                "icon": row[5],
                "color": row[6],
                "usage_count": row[7] if row[7] else 0,
                "match_type": "concept",
                "synonyms": []  # Initialize for frontend
            }
            
            # Get synonyms for this concept
            syn_result = db.execute(text("""
                SELECT alias_text FROM tag_aliases_v2
                WHERE concept_id = :concept_id
            """), {"concept_id": concept["id"]})
            concept["synonyms"] = [row[0] for row in syn_result]
            
            results.append(concept)
        
        # Search in aliases if requested
        if include_aliases:
            alias_result = db.execute(text("""
                SELECT DISTINCT c.id, c.slug, c.display_name, c.description,
                       c.entity_type, c.icon, c.color, c.usage_count,
                       a.alias_text
                FROM tag_aliases_v2 a
                JOIN tag_concepts_v2 c ON a.concept_id = c.id
                WHERE LOWER(a.alias_text) LIKE LOWER(:pattern)
                      AND (c.status = 'active' OR c.status IS NULL)
                ORDER BY c.usage_count DESC
                LIMIT 20
            """), {"pattern": search_pattern})
            
            for row in alias_result:
                # Check if concept already in results
                if not any(r["id"] == row[0] for r in results):
                    concept = {
                        "id": row[0],
                        "tag": row[1],  # Frontend expects 'tag' field
                        "slug": row[1],
                        "display_name": row[2],
                        "description": row[3],
                        "entity_type": row[4],
                        "icon": row[5],
                        "color": row[6],
                        "usage_count": row[7] if row[7] else 0,
                        "match_type": "alias",
                        "matched_alias": row[8],
                        "synonyms": []  # Initialize for frontend
                    }
                    
                    # Get all synonyms for this concept
                    syn_result = db.execute(text("""
                        SELECT alias_text FROM tag_aliases_v2
                        WHERE concept_id = :concept_id
                    """), {"concept_id": concept["id"]})
                    concept["synonyms"] = [row[0] for row in syn_result]
                    
                    results.append(concept)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching concepts: {str(e)}")