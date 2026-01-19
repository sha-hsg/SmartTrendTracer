"""
LLM Preferences API
Allows users to view available models and manage their LLM preferences
"""
import os
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.services.llm_manager import get_llm_manager

router = APIRouter()


@router.get("/status")
async def get_api_key_status():
    """
    Check which API keys are configured in environment.
    Used by frontend to show warnings when keys are missing.

    Returns:
        Dictionary with provider names and their configuration status
    """
    # Check for common API keys
    api_keys = {
        "openai": {
            "configured": bool(os.getenv("OPENAI_API_KEY")),
            "env_var": "OPENAI_API_KEY",
            "provider": "OpenAI"
        },
        "anthropic": {
            "configured": bool(os.getenv("ANTHROPIC_API_KEY")),
            "env_var": "ANTHROPIC_API_KEY",
            "provider": "Anthropic (Claude)"
        },
        "google": {
            "configured": bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")),
            "env_var": "GOOGLE_API_KEY or GEMINI_API_KEY",
            "provider": "Google (Gemini)"
        },
        "xai": {
            "configured": bool(os.getenv("XAI_API_KEY")),
            "env_var": "XAI_API_KEY",
            "provider": "xAI (Grok)"
        }
    }

    configured_count = sum(1 for k in api_keys.values() if k["configured"])
    total_count = len(api_keys)

    # Build list of missing keys
    missing = [
        {"provider": v["provider"], "env_var": v["env_var"]}
        for k, v in api_keys.items() if not v["configured"]
    ]

    return {
        "status": "ok" if configured_count > 0 else "error",
        "configured_count": configured_count,
        "total_providers": total_count,
        "all_configured": configured_count == total_count,
        "providers": api_keys,
        "missing": missing,
        "message": (
            "All API keys configured" if configured_count == total_count
            else f"Missing {total_count - configured_count} API key(s). Add them to ~/.env"
        )
    }


# Pydantic models for request/response
class ModelInfo(BaseModel):
    """Information about a specific model configuration"""
    model: str
    provider: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class TaskInfo(BaseModel):
    """Information about a task type"""
    task_type: str
    model: str
    provider: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class UserPreference(BaseModel):
    """User's model preference for a task"""
    task_type: str
    model_name: str


class PreferencesUpdate(BaseModel):
    """Batch update of user preferences"""
    preferences: List[UserPreference]


@router.get("/models", response_model=Dict[str, List[ModelInfo]])
async def get_available_models():
    """
    Get all available models grouped by task type

    Returns:
        Dictionary with task types as keys and lists of model configurations as values

    Example:
        {
            "tag_suggestion": [
                {
                    "model": "claude-sonnet-4-20250514",
                    "provider": "anthropic",
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                {
                    "model": "gpt-4o",
                    "provider": "openai",
                    "temperature": 0.3,
                    "max_tokens": 1000
                }
            ],
            ...
        }
    """
    try:
        llm_manager = get_llm_manager()
        models = llm_manager.get_available_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available models: {str(e)}")


@router.get("/tasks", response_model=List[str])
async def get_all_tasks():
    """
    Get list of all available task types

    Returns:
        List of task type names

    Example:
        [
            "tag_suggestion",
            "article_summarizer",
            "entity_extraction",
            "ontology_suggestion",
            "paper_analysis",
            ...
        ]
    """
    try:
        llm_manager = get_llm_manager()
        tasks = llm_manager.get_all_tasks()
        return list(tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task types: {str(e)}")


@router.get("/tasks/{task_type}", response_model=TaskInfo)
async def get_task_info(task_type: str):
    """
    Get detailed information about a specific task type

    Args:
        task_type: Task type identifier (e.g., "tag_suggestion")

    Returns:
        Task configuration details including model, provider, and parameters

    Example:
        {
            "task_type": "tag_suggestion",
            "model": "claude-sonnet-4-20250514",
            "provider": "anthropic",
            "temperature": 0.3,
            "max_tokens": 1000
        }
    """
    try:
        llm_manager = get_llm_manager()
        info = llm_manager.get_task_info(task_type)

        if not info:
            raise HTTPException(status_code=404, detail=f"Task type '{task_type}' not found")

        return info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task info: {str(e)}")


@router.get("/preferences", response_model=Dict[str, str])
async def get_user_preferences(user_id: str = Query(default="default")):
    """
    Get all model preferences for a user

    Args:
        user_id: User identifier (default: "default")

    Returns:
        Dictionary with task types as keys and preferred model names as values

    Example:
        {
            "tag_suggestion": "summarization_comprehensive",
            "entity_extraction": "entity_extraction_gpt5"
        }
    """
    try:
        llm_manager = get_llm_manager()
        preferences = llm_manager.get_all_user_preferences(user_id)
        return preferences
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user preferences: {str(e)}")


@router.post("/preferences")
async def set_user_preference(
    preference: UserPreference,
    user_id: str = Query(default="default")
):
    """
    Set a user's model preference for a specific task type

    Args:
        preference: User preference with task_type and model_name
        user_id: User identifier (default: "default")

    Returns:
        Success message with updated preference

    Example Request Body:
        {
            "task_type": "tag_suggestion",
            "model_name": "summarization_comprehensive"
        }

    Example Response:
        {
            "success": true,
            "message": "Preference updated",
            "user_id": "default",
            "task_type": "tag_suggestion",
            "model_name": "summarization_comprehensive"
        }
    """
    try:
        llm_manager = get_llm_manager()

        # Validate task type exists
        task_info = llm_manager.get_task_info(preference.task_type)
        if not task_info:
            raise HTTPException(
                status_code=404,
                detail=f"Task type '{preference.task_type}' not found"
            )

        # Validate model exists
        available_models = llm_manager.get_available_models()
        if preference.task_type not in available_models:
            raise HTTPException(
                status_code=404,
                detail=f"No models available for task type '{preference.task_type}'"
            )

        # Set preference
        llm_manager.set_user_preference(
            task_type=preference.task_type,
            model_name=preference.model_name,
            user_id=user_id
        )

        return {
            "success": True,
            "message": "Preference updated",
            "user_id": user_id,
            "task_type": preference.task_type,
            "model_name": preference.model_name
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set preference: {str(e)}")


@router.put("/preferences/batch")
async def update_preferences_batch(
    update: PreferencesUpdate,
    user_id: str = Query(default="default")
):
    """
    Batch update multiple user preferences at once

    Args:
        update: Batch of preferences to update
        user_id: User identifier (default: "default")

    Returns:
        Summary of updates with success/failure counts

    Example Request Body:
        {
            "preferences": [
                {
                    "task_type": "tag_suggestion",
                    "model_name": "summarization_comprehensive"
                },
                {
                    "task_type": "entity_extraction",
                    "model_name": "entity_extraction_gpt5"
                }
            ]
        }

    Example Response:
        {
            "success": true,
            "updated": 2,
            "failed": 0,
            "user_id": "default",
            "preferences": {
                "tag_suggestion": "summarization_comprehensive",
                "entity_extraction": "entity_extraction_gpt5"
            }
        }
    """
    try:
        llm_manager = get_llm_manager()
        updated = 0
        failed = 0
        errors = []

        for pref in update.preferences:
            try:
                # Validate task type
                task_info = llm_manager.get_task_info(pref.task_type)
                if not task_info:
                    errors.append(f"Task type '{pref.task_type}' not found")
                    failed += 1
                    continue

                # Set preference
                llm_manager.set_user_preference(
                    task_type=pref.task_type,
                    model_name=pref.model_name,
                    user_id=user_id
                )
                updated += 1

            except Exception as e:
                errors.append(f"{pref.task_type}: {str(e)}")
                failed += 1

        # Get final state of preferences
        final_preferences = llm_manager.get_all_user_preferences(user_id)

        return {
            "success": failed == 0,
            "updated": updated,
            "failed": failed,
            "user_id": user_id,
            "preferences": final_preferences,
            "errors": errors if errors else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.delete("/preferences/{task_type}")
async def delete_user_preference(
    task_type: str,
    user_id: str = Query(default="default")
):
    """
    Remove a user's preference for a task (revert to default)

    Args:
        task_type: Task type identifier
        user_id: User identifier (default: "default")

    Returns:
        Success message

    Example Response:
        {
            "success": true,
            "message": "Preference removed, reverted to default",
            "user_id": "default",
            "task_type": "tag_suggestion"
        }
    """
    try:
        llm_manager = get_llm_manager()

        # Set preference to None (removes it)
        llm_manager.set_user_preference(
            task_type=task_type,
            model_name=None,
            user_id=user_id
        )

        return {
            "success": True,
            "message": "Preference removed, reverted to default",
            "user_id": user_id,
            "task_type": task_type
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete preference: {str(e)}")


@router.delete("/preferences")
async def clear_all_preferences(user_id: str = Query(default="default")):
    """
    Clear all preferences for a user (revert all to defaults)

    Args:
        user_id: User identifier (default: "default")

    Returns:
        Success message with count of cleared preferences

    Example Response:
        {
            "success": true,
            "message": "All preferences cleared",
            "user_id": "default",
            "cleared_count": 5
        }
    """
    try:
        llm_manager = get_llm_manager()

        # Get current preferences count
        current_prefs = llm_manager.get_all_user_preferences(user_id)
        count = len(current_prefs)

        # Clear all by setting each to None
        for task_type in current_prefs.keys():
            llm_manager.set_user_preference(
                task_type=task_type,
                model_name=None,
                user_id=user_id
            )

        return {
            "success": True,
            "message": "All preferences cleared",
            "user_id": user_id,
            "cleared_count": count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear preferences: {str(e)}")
