"""
Debug endpoints for tag reorganization.
Provides inspection of current concept statistics.
"""

from fastapi import APIRouter

from .utils import logger

router = APIRouter()


@router.get("/debug/current-concepts")
async def get_debug_concepts():
    """
    Debug endpoint to get current concept statistics and samples
    """
    from app.services.concept_only_tag_service import ConceptOnlyTagService

    try:
        concept_service = ConceptOnlyTagService()

        # Get ALL concepts including unused ones to show the true count
        all_concepts = concept_service.get_all_concepts_with_counts(include_unused=True)

        # Analyze the data
        stats = {
            "total_concepts": len(all_concepts),
            "organized": 0,
            "unorganized": 0,
            "auto_generated": 0,
            "manual": 0,
            "by_content_type": {},
            "sample_concepts": [],
            "unorganized_samples": [],
            "usage_distribution": {
                "unused": 0,
                "low_usage": 0,  # 1-5 uses
                "medium_usage": 0,  # 6-20 uses
                "high_usage": 0  # 20+ uses
            }
        }

        for concept in all_concepts:
            # Check if organized (has parents)
            parents = concept.get('parents', [])
            if parents and len(parents) > 0:
                stats["organized"] += 1
            else:
                stats["unorganized"] += 1
                if len(stats["unorganized_samples"]) < 10:
                    stats["unorganized_samples"].append({
                        "id": concept.get('id'),
                        "slug": concept.get('slug'),
                        "display_name": concept.get('display_name'),
                        "count": concept.get('count', 0),
                        "auto_generated": concept.get('auto_generated', False)
                    })

            # Check source
            if concept.get('auto_generated'):
                stats["auto_generated"] += 1
            else:
                stats["manual"] += 1

            # Track content types
            for content_type in concept.get('content_types', []):
                stats["by_content_type"][content_type] = stats["by_content_type"].get(content_type, 0) + 1

            # Usage distribution
            count = concept.get('count', 0)
            if count == 0:
                stats["usage_distribution"]["unused"] += 1
            elif count <= 5:
                stats["usage_distribution"]["low_usage"] += 1
            elif count <= 20:
                stats["usage_distribution"]["medium_usage"] += 1
            else:
                stats["usage_distribution"]["high_usage"] += 1

            # Get samples
            if len(stats["sample_concepts"]) < 5:
                stats["sample_concepts"].append({
                    "id": concept.get('id'),
                    "slug": concept.get('slug'),
                    "display_name": concept.get('display_name'),
                    "parents": concept.get('parents', []),
                    "count": concept.get('count', 0)
                })

        logger.info(f"[DEBUG] Concept stats: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error in debug concepts endpoint: {e}")
        return {"error": str(e)}
