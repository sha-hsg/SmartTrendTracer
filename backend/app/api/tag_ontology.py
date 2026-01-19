"""
API endpoints for managing tag ontology and hierarchical relationships
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict
from pydantic import BaseModel

router = APIRouter()

# Pydantic models for requests/responses
class ConceptCreate(BaseModel):
    tag: str
    display_name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class ConceptUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None

class SynonymCreate(BaseModel):
    synonym_tag: str

class ParentInfo(BaseModel):
    id: int
    tag: str
    display_name: str

class ChildInfo(BaseModel):
    id: int
    tag: str
    display_name: str
    child_count: int

class UsageStats(BaseModel):
    tweet_count: int
    article_count: int
    total_count: int

class ConceptResponse(BaseModel):
    id: int
    tag: str
    display_name: str
    description: Optional[str]
    parent_id: Optional[int]
    parent: Optional[ParentInfo] = None
    children: Optional[List[ChildInfo]] = None
    level: int
    child_count: int
    descendant_count: int
    synonyms: List[str]
    path: str
    usage_stats: Optional[UsageStats] = None

class TreeNode(BaseModel):
    id: int
    tag: str
    display_name: str
    description: Optional[str]
    child_count: int
    descendant_count: int
    synonyms: List[str]
    children: List['TreeNode']

TreeNode.model_rebuild()

@router.get("/tree", response_model=List[TreeNode])
    """Get the complete tag hierarchy as a tree"""
    service = TagOntologyService(db)
    return service.get_hierarchy_tree()

@router.get("/concepts", response_model=List[ConceptResponse])
def get_all_concepts(
    parent_id: Optional[int] = Query(None),
    level: Optional[int] = Query(None),
):
    """Get all tag concepts, optionally filtered by parent or level"""
    query = db.query(TagConcept)
    
    if parent_id is not None:
        query = query.filter(TagConcept.parent_id == parent_id)
    if level is not None:
        query = query.filter(TagConcept.level == level)
    
    concepts = query.order_by(TagConcept.display_name).all()
    
    return [
        ConceptResponse(
            id=c.id,
            tag=c.tag,
            display_name=c.display_name,
            description=c.description,
            parent_id=c.parent_id,
            level=c.level,
            child_count=c.child_count,
            descendant_count=c.descendant_count,
            synonyms=[s.synonym_tag for s in c.synonyms],
            path=c.path
        )
        for c in concepts
    ]

@router.get("/concept/{concept_id}", response_model=ConceptResponse)
    """Get a specific tag concept by ID with extended information"""
    concept = db.query(TagConcept).filter(TagConcept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    
    # Get parent information
    parent_info = None
    if concept.parent_id:
        parent = db.query(TagConcept).filter(TagConcept.id == concept.parent_id).first()
        if parent:
            parent_info = ParentInfo(
                id=parent.id,
                tag=parent.tag,
                display_name=parent.display_name
            )
    
    # Get children information
    children_info = []
    children = db.query(TagConcept).filter(TagConcept.parent_id == concept.id).all()
    for child in children:
        children_info.append(ChildInfo(
            id=child.id,
            tag=child.tag,
            display_name=child.display_name,
            child_count=child.child_count
        ))
    
    # Get usage statistics
    usage_stats = None
    try:
        # Get all tags that map to this concept (including synonyms)
        mapped_tags = db.query(TagMapping.tag_name).filter(
            TagMapping.concept_id == concept.id
        ).all()
        tag_names = [t[0] for t in mapped_tags]
        tag_names.append(concept.tag)  # Include the concept's own tag
        
        # Count tweets with these tags
        from app.models import Tweet, SubstackArticle, tweet_tags, substack_article_tags
        
        tweet_count = db.query(Tweet).join(tweet_tags).join(Tag).filter(
            Tag.name.in_(tag_names)
        ).distinct().count()
        
        # Count articles with these tags
        article_count = db.query(SubstackArticle).join(substack_article_tags).join(Tag).filter(
            Tag.name.in_(tag_names)
        ).distinct().count()
        
        usage_stats = UsageStats(
            tweet_count=tweet_count,
            article_count=article_count,
            total_count=tweet_count + article_count
        )
    except Exception as e:
        print(f"Error getting usage stats: {e}")
        # Continue without usage stats if there's an error
    
    return ConceptResponse(
        id=concept.id,
        tag=concept.tag,
        display_name=concept.display_name,
        description=concept.description,
        parent_id=concept.parent_id,
        parent=parent_info,
        children=children_info if children_info else None,
        level=concept.level,
        child_count=concept.child_count,
        descendant_count=concept.descendant_count,
        synonyms=[s.synonym_tag for s in concept.synonyms],
        path=concept.path,
        usage_stats=usage_stats
    )

@router.post("/concept", response_model=ConceptResponse)
    """Create a new tag concept"""
    # Check if tag already exists
    existing = db.query(TagConcept).filter(TagConcept.tag == concept.tag.lower().replace(' ', '-')).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists")
    
    # Check if synonym exists
    existing_syn = db.query(TagSynonym).filter(
        TagSynonym.synonym_tag == concept.tag.lower().replace(' ', '-')
    ).first()
    if existing_syn:
        raise HTTPException(status_code=400, detail="Tag exists as a synonym")
    
    service = TagOntologyService(db)
    new_concept = service.create_concept(
        tag=concept.tag,
        display_name=concept.display_name,
        description=concept.description,
        parent_id=concept.parent_id
    )
    
    return ConceptResponse(
        id=new_concept.id,
        tag=new_concept.tag,
        display_name=new_concept.display_name,
        description=new_concept.description,
        parent_id=new_concept.parent_id,
        level=new_concept.level,
        child_count=new_concept.child_count,
        descendant_count=new_concept.descendant_count,
        synonyms=[],
        path=new_concept.path
    )

@router.put("/concept/{concept_id}", response_model=ConceptResponse)
def update_concept(
    concept_id: int,
    update: ConceptUpdate,
):
    """Update a tag concept"""
    concept = db.query(TagConcept).filter(TagConcept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    
    if update.display_name:
        concept.display_name = update.display_name
    if update.description is not None:
        concept.description = update.description
    
    # Handle parent change
    if update.parent_id is not None and update.parent_id != concept.parent_id:
        # Prevent circular references
        if update.parent_id:
            parent = db.query(TagConcept).filter(TagConcept.id == update.parent_id).first()
            if parent and concept.id in [int(id) for id in parent.path.strip('/').split('/') if id]:
                raise HTTPException(status_code=400, detail="Cannot create circular hierarchy")
        
        service = TagOntologyService(db)
        service.move_concept(concept_id, update.parent_id)
    else:
        db.commit()
    
    db.refresh(concept)
    
    return ConceptResponse(
        id=concept.id,
        tag=concept.tag,
        display_name=concept.display_name,
        description=concept.description,
        parent_id=concept.parent_id,
        level=concept.level,
        child_count=concept.child_count,
        descendant_count=concept.descendant_count,
        synonyms=[s.synonym_tag for s in concept.synonyms],
        path=concept.path
    )

@router.delete("/concept/{concept_id}")
    """Delete a tag concept and all its relationships"""
    concept = db.query(TagConcept).filter(TagConcept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    
    # Check if has children
    if concept.child_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete concept with children")
    
    db.delete(concept)
    db.commit()
    
    # Rebuild mappings
    TagMapping.rebuild_mappings(db)
    
    return {"message": "Concept deleted successfully"}

@router.post("/concept/{concept_id}/synonym")
def add_synonym(
    concept_id: int,
    synonym: SynonymCreate,
):
    """Add a synonym to a concept"""
    concept = db.query(TagConcept).filter(TagConcept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    
    # Check if synonym already exists
    existing = db.query(TagSynonym).filter(
        TagSynonym.synonym_tag == synonym.synonym_tag.lower().replace(' ', '-')
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Synonym already exists")
    
    # Check if it's a concept tag
    existing_concept = db.query(TagConcept).filter(
        TagConcept.tag == synonym.synonym_tag.lower().replace(' ', '-')
    ).first()
    if existing_concept:
        raise HTTPException(status_code=400, detail="Tag exists as a concept")
    
    service = TagOntologyService(db)
    new_synonym = service.add_synonym(concept_id, synonym.synonym_tag)
    
    return {"message": "Synonym added successfully", "synonym": new_synonym.synonym_tag}

@router.delete("/synonym/{synonym_id}")
    """Delete a synonym"""
    synonym = db.query(TagSynonym).filter(TagSynonym.id == synonym_id).first()
    if not synonym:
        raise HTTPException(status_code=404, detail="Synonym not found")
    
    db.delete(synonym)
    db.commit()
    
    # Rebuild mappings
    TagMapping.rebuild_mappings(db)
    
    return {"message": "Synonym deleted successfully"}

@router.get("/resolve/{tag}")
    """Resolve a tag to its canonical concept and get all related tags"""
    normalized_tag = tag.lower().replace(' ', '-')
    
    # Check if it's a concept
    concept = db.query(TagConcept).filter(TagConcept.tag == normalized_tag).first()
    
    # Check if it's a synonym
    if not concept:
        synonym = db.query(TagSynonym).filter(TagSynonym.synonym_tag == normalized_tag).first()
        if synonym:
            concept = synonym.concept
    
    if not concept:
        return {
            "found": False,
            "tag": normalized_tag,
            "canonical": None,
            "related_tags": [normalized_tag]
        }
    
    # Get all related tags
    related_tags = list(concept.get_all_related_tags(db))
    
    return {
        "found": True,
        "tag": normalized_tag,
        "canonical": {
            "id": concept.id,
            "tag": concept.tag,
            "display_name": concept.display_name,
            "description": concept.description,
            "level": concept.level
        },
        "related_tags": related_tags,
        "ancestors": [
            {"id": a.id, "tag": a.tag, "display_name": a.display_name}
            for a in concept.get_ancestors(db)
        ],
        "children": [
            {"id": c.id, "tag": c.tag, "display_name": c.display_name}
            for c in db.query(TagConcept).filter(TagConcept.parent_id == concept.id).all()
        ]
    }

@router.get("/filter-tags/{tag}")
    """Get all tags to use when filtering by a specific tag"""
    service = TagOntologyService(db)
    tags = service.get_tags_for_filtering(tag)
    
    if not tags:
        # Tag not in ontology, just return the tag itself
        return {"source_tag": tag, "filter_tags": [tag.lower().replace(' ', '-')]}
    
    return {"source_tag": tag, "filter_tags": tags}

@router.post("/rebuild-mappings")
    """Rebuild the tag mapping cache (admin operation)"""
    TagMapping.rebuild_mappings(db)
    return {"message": "Tag mappings rebuilt successfully"}

@router.get("/stats")
    """Get statistics about the tag ontology"""
    total_concepts = db.query(TagConcept).count()
    total_synonyms = db.query(TagSynonym).count()
    total_mappings = db.query(TagMapping).count()
    
    # Get depth of hierarchy
    max_level = db.query(TagConcept.level).order_by(TagConcept.level.desc()).first()
    max_depth = max_level[0] if max_level else 0
    
    # Get concepts with most children
    top_parents = db.query(
        TagConcept.display_name,
        TagConcept.child_count,
        TagConcept.descendant_count
    ).filter(
        TagConcept.child_count > 0
    ).order_by(
        TagConcept.descendant_count.desc()
    ).limit(5).all()
    
    return {
        "total_concepts": total_concepts,
        "total_synonyms": total_synonyms,
        "total_mappings": total_mappings,
        "hierarchy_depth": max_depth + 1,
        "top_parent_concepts": [
            {
                "name": p[0],
                "direct_children": p[1],
                "total_descendants": p[2]
            }
            for p in top_parents
        ]
    }

@router.post("/import-existing-tags")
    """Import existing tags as uncategorized concepts"""
    # Get all unique tags from the Tag table
    existing_tags = db.query(Tag.tag).distinct().all()
    
    service = TagOntologyService(db)
    imported = 0
    skipped = 0
    
    for (tag,) in existing_tags:
        # Check if already exists as concept or synonym
        concept = db.query(TagConcept).filter(TagConcept.tag == tag.lower()).first()
        synonym = db.query(TagSynonym).filter(TagSynonym.synonym_tag == tag.lower()).first()
        
        if not concept and not synonym:
            try:
                service.create_concept(
                    tag=tag,
                    display_name=tag.replace('-', ' ').title(),
                    description=f"Auto-imported from existing tags",
                    parent_id=None  # Top level, uncategorized
                )
                imported += 1
            except:
                skipped += 1
        else:
            skipped += 1
    
    return {
        "imported": imported,
        "skipped": skipped,
        "total": len(existing_tags)
    }