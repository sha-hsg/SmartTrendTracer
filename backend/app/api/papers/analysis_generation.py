"""
Paper analysis generation routes: single analysis generation (frontend wrapper).

The former generate-multiple / async background endpoints were removed —
the frontend generates analyses sequentially via this endpoint (see CLAUDE.md,
"Generate All Analyses" fix, January 4, 2026).
"""

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException

router = APIRouter()


@router.post("/{paper_id}/analyses/generate")
async def generate_analysis(paper_id: str, data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Generate a paper analysis (wrapper for frontend compatibility)"""
    # This is a wrapper endpoint for frontend compatibility
    # It calls the main create_analysis function
    from .analysis import create_analysis

    analysis_type = data.get('analysis_type')
    if not analysis_type:
        raise HTTPException(status_code=400, detail="analysis_type is required")
    regenerate = data.get('regenerate', False)  # Support regenerate flag from frontend
    model = data.get('model')  # Get model from frontend (LiteLLM handles model routing)

    try:
        analysis = await create_analysis(paper_id, analysis_type, regenerate=regenerate, model=model)

        # Wrap the response in the format the frontend expects
        return {
            "success": True,
            "analysis_type": analysis_type,
            "content": analysis.get("content", ""),
            "metadata": analysis.get("metadata", {}),
            "generated_at": analysis.get("generated_at"),
            "model_used": analysis.get("model_used") or analysis.get("model")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
