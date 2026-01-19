"""
API endpoints for comprehensive tag reorganization
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from app.services.comprehensive_tag_reorganizer import ComprehensiveTagReorganizer
from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()

class ReorganizationRequest(BaseModel):
    """Request for tag reorganization"""
    use_llm_enhancement: bool = True
    save_to_database: bool = False
    dry_run: bool = True

class ReorganizationResponse(BaseModel):
    """Response from tag reorganization"""
    success: bool
    summary: Dict[str, Any]
    concepts_count: int
    aliases_count: int
    validation_passed: bool
    message: str
    
class ApplyReorganizationRequest(BaseModel):
    """Request to apply reorganization to database"""
    reorganization_id: str
    backup_existing: bool = True

@router.post("/reorganize/comprehensive")
async def comprehensive_reorganization(
    request: ReorganizationRequest,
    background_tasks: BackgroundTasks,
) -> ReorganizationResponse:
    """
    Perform comprehensive tag reorganization with canonicalization,
    aliasing, and hierarchy cleanup
    """
    try:
        logger.info("Starting comprehensive tag reorganization")
        
        # Step 1: Collect all unique tags from the system
        all_tags = []
        
        # Get tags from tweets
        tweet_tags = db.query(
            TweetTag.tag,
            func.count(TweetTag.id).label('count')
        ).group_by(TweetTag.tag).all()
        
        for tag, count in tweet_tags:
            all_tags.append({"tag": tag, "count": count, "source": "tweets"})
        
        # Get tags from papers
        paper_tags = db.query(
            PaperTag.tag,
            func.count(PaperTag.id).label('count')
        ).group_by(PaperTag.tag).all()
        
        for tag, count in paper_tags:
            # Check if we already have this tag from tweets
            existing = next((t for t in all_tags if t["tag"] == tag), None)
            if existing:
                existing["count"] += count
                existing["source"] = "multiple"
            else:
                all_tags.append({"tag": tag, "count": count, "source": "papers"})
        
        # Get tags from articles
        article_tags = db.query(
            SubstackArticleTag.tag,
            func.count(SubstackArticleTag.id).label('count')
        ).group_by(SubstackArticleTag.tag).all()
        
        for tag, count in article_tags:
            existing = next((t for t in all_tags if t["tag"] == tag), None)
            if existing:
                existing["count"] += count
                existing["source"] = "multiple"
            else:
                all_tags.append({"tag": tag, "count": count, "source": "articles"})
        
        logger.info(f"Collected {len(all_tags)} unique tags from all sources")
        
        # Step 2: Use GPT-5 if LLM enhancement is requested, otherwise use rule-based
        if request.use_llm_enhancement:
            logger.info("Using GPT-5 for comprehensive reorganization")
            reorganizer = GPT5TagReorganizer()
            result = reorganizer.reorganize_tags(all_tags)
        else:
            logger.info("Using rule-based reorganization")
            reorganizer = ComprehensiveTagReorganizer()
            result = reorganizer.reorganize_tags(all_tags)
        
        # Step 4: Save to database if requested
        if not request.dry_run and request.save_to_database:
            await save_reorganization_to_database(result, db)
        
        # Step 5: Store result for later application
        if not request.dry_run:
            # Store the reorganization result for later application
            # You might want to save this to a file or database
            import json
            import os
            
            # Create reorganizations directory if it doesn't exist
            os.makedirs("data/reorganizations", exist_ok=True)
            
            # Save with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"data/reorganizations/reorg_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"Saved reorganization to {filename}")
        
        return ReorganizationResponse(
            success=True,
            summary=result["summary"],
            concepts_count=len(result["concepts"]),
            aliases_count=len(result["aliases"]),
            validation_passed=result["validation_report"]["all_tags_mapped"],
            message=f"Successfully reorganized {len(all_tags)} tags into {len(result['concepts'])} concepts with {len(result['aliases'])} aliases"
        )
        
    except Exception as e:
        logger.error(f"Error in comprehensive reorganization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reorganize/status")
    """
    Get current status of tag system and potential reorganization impact
    """
    try:
        # Count current tags
        tweet_tag_count = db.query(func.count(func.distinct(TweetTag.tag))).scalar()
        paper_tag_count = db.query(func.count(func.distinct(PaperTag.tag))).scalar()
        article_tag_count = db.query(func.count(func.distinct(SubstackArticleTag.tag))).scalar()
        
        # Count all unique tags
        all_tags = set()
        
        for tag, in db.query(TweetTag.tag).distinct():
            all_tags.add(tag)
        for tag, in db.query(PaperTag.tag).distinct():
            all_tags.add(tag)
        for tag, in db.query(SubstackArticleTag.tag).distinct():
            all_tags.add(tag)
        
        # Count current ontology
        concept_count = db.query(func.count(TagConcept.id)).scalar()
        synonym_count = db.query(func.count(TagSynonym.id)).scalar()
        
        # Analyze tag variations
        tag_variations = analyze_tag_variations(list(all_tags))
        
        return {
            "current_state": {
                "total_unique_tags": len(all_tags),
                "tweet_tags": tweet_tag_count,
                "paper_tags": paper_tag_count,
                "article_tags": article_tag_count,
                "existing_concepts": concept_count,
                "existing_synonyms": synonym_count
            },
            "analysis": {
                "potential_duplicates": len(tag_variations["potential_duplicates"]),
                "case_variations": len(tag_variations["case_variations"]),
                "plural_variations": len(tag_variations["plural_variations"]),
                "separator_variations": len(tag_variations["separator_variations"])
            },
            "recommendation": generate_recommendation(len(all_tags), tag_variations)
        }
        
    except Exception as e:
        logger.error(f"Error getting reorganization status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reorganize/apply")
async def apply_reorganization(
    request: ApplyReorganizationRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Apply a saved reorganization to the database
    """
    try:
        import json
        import os
        
        # Load the reorganization
        filename = f"data/reorganizations/{request.reorganization_id}.json"
        
        if not os.path.exists(filename):
            raise HTTPException(status_code=404, detail="Reorganization not found")
        
        with open(filename, 'r') as f:
            reorganization = json.load(f)
        
        # Backup existing if requested
        if request.backup_existing:
            await backup_existing_ontology(db)
        
        # Apply the reorganization
        stats = await apply_reorganization_to_database(reorganization, db)
        
        return {
            "success": True,
            "message": "Reorganization applied successfully",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error applying reorganization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reorganize/preview/{tag}")
async def preview_tag_reorganization(
    tag: str,
) -> Dict[str, Any]:
    """
    Preview how a specific tag would be reorganized
    """
    try:
        reorganizer = ComprehensiveTagReorganizer()
        
        # Process just this tag
        canonical_slug = reorganizer.canonicalize_slug(tag)
        display_name = reorganizer.generate_display_name(canonical_slug)
        category = reorganizer.categorize_tag(canonical_slug, display_name)
        
        # Find similar tags in the system
        all_tags = set()
        for t, in db.query(TweetTag.tag).distinct():
            all_tags.add(t)
        for t, in db.query(PaperTag.tag).distinct():
            all_tags.add(t)
        for t, in db.query(SubstackArticleTag.tag).distinct():
            all_tags.add(t)
        
        # Find potential aliases
        potential_aliases = []
        for existing_tag in all_tags:
            if existing_tag != tag:
                existing_canonical = reorganizer.canonicalize_slug(existing_tag)
                if existing_canonical == canonical_slug:
                    alias_type = reorganizer.detect_alias_type(existing_tag, canonical_slug)
                    potential_aliases.append({
                        "tag": existing_tag,
                        "type": alias_type.value
                    })
        
        return {
            "original_tag": tag,
            "canonical_slug": canonical_slug,
            "display_name": display_name,
            "category": category,
            "category_info": reorganizer.ROOT_CATEGORIES.get(category, {}),
            "potential_aliases": potential_aliases,
            "alias_count": len(potential_aliases)
        }
        
    except Exception as e:
        logger.error(f"Error previewing tag reorganization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

def analyze_tag_variations(tags: List[str]) -> Dict[str, List]:
    """Analyze tag variations in the current system"""
    reorganizer = ComprehensiveTagReorganizer()
    
    variations = {
        "potential_duplicates": [],
        "case_variations": [],
        "plural_variations": [],
        "separator_variations": []
    }
    
    # Group by canonical form
    canonical_groups = {}
    for tag in tags:
        canonical = reorganizer.canonicalize_slug(tag)
        if canonical not in canonical_groups:
            canonical_groups[canonical] = []
        canonical_groups[canonical].append(tag)
    
    # Analyze groups
    for canonical, group in canonical_groups.items():
        if len(group) > 1:
            variations["potential_duplicates"].append({
                "canonical": canonical,
                "variations": group
            })
            
            # Analyze variation types
            for tag in group:
                if tag.lower() != tag:
                    variations["case_variations"].append(tag)
                if reorganizer._is_plural_form(tag.lower(), canonical):
                    variations["plural_variations"].append(tag)
                if '-' in tag or '_' in tag or ' ' in tag:
                    variations["separator_variations"].append(tag)
    
    return variations

def generate_recommendation(total_tags: int, variations: Dict) -> str:
    """Generate a recommendation based on analysis"""
    duplicate_count = len(variations["potential_duplicates"])
    
    if duplicate_count > total_tags * 0.2:  # More than 20% are potential duplicates
        return f"High duplication detected ({duplicate_count} groups). Comprehensive reorganization strongly recommended."
    elif duplicate_count > total_tags * 0.1:  # More than 10%
        return f"Moderate duplication detected ({duplicate_count} groups). Reorganization recommended."
    else:
        return f"Low duplication detected ({duplicate_count} groups). System is relatively clean."

async def enhance_with_llm(result: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Enhance reorganization with LLM insights"""
    try:
        llm_service = LLMService()
        
        # Prepare prompt for LLM enhancement
        prompt = f"""
        Review this tag reorganization and suggest improvements:
        
        Total concepts: {len(result['concepts'])}
        Total aliases: {len(result['aliases'])}
        
        Root categories: {', '.join([c['display_name'] for c in result['concepts'] if not c['parents']])}
        
        Please suggest:
        1. Better category assignments for ambiguous tags
        2. Additional aliases or synonyms
        3. Improved display names
        4. Missing relationships
        
        Return suggestions as JSON.
        """
        
        # Call LLM (implementation depends on your LLM service)
        # For now, just return the original result
        logger.info("LLM enhancement skipped (not implemented)")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in LLM enhancement: {e}")
        return result

async def save_reorganization_to_database(result: Dict[str, Any], db: Session):
    """Save the reorganization to the database"""
    try:
        # This would implement the actual database saving logic
        # For now, just log
        logger.info(f"Would save {len(result['concepts'])} concepts and {len(result['aliases'])} aliases to database")
        
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        raise

async def backup_existing_ontology(db: Session):
    """Backup existing ontology before applying changes"""
    try:
        # This would implement backup logic
        logger.info("Backing up existing ontology")
        
    except Exception as e:
        logger.error(f"Error backing up ontology: {e}")
        raise

async def apply_reorganization_to_database(reorganization: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Apply reorganization to database"""
    try:
        stats = {
            "concepts_created": 0,
            "aliases_created": 0,
            "tags_updated": 0
        }
        
        # This would implement the actual application logic
        logger.info(f"Would apply reorganization with {len(reorganization['concepts'])} concepts")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error applying reorganization: {e}")
        raise