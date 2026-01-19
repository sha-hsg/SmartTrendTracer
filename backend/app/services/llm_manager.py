"""
Unified LLM Manager Service using LiteLLM
Provides centralized LLM access with automatic fallbacks, caching, and user preferences
"""

import os
import yaml
import logging
from typing import Optional, Dict, List, Any, Union
from pathlib import Path
from datetime import datetime, timezone
from litellm import Router, completion
from litellm.caching import Cache
from app.database.mongodb import get_database

logger = logging.getLogger(__name__)

# MongoDB Callback for LLM Usage Tracking
def custom_mongodb_callback(
    kwargs,                      # kwargs to completion
    completion_response,         # response from completion
    start_time, end_time         # start/end time
):
    """Log LLM usage to MongoDB"""
    try:
        db = get_database()

        # Calculate duration
        duration_ms = (end_time - start_time).total_seconds() * 1000

        # Extract information from kwargs and response
        # Use actual_model from metadata if available, otherwise fall back to model parameter
        metadata = kwargs.get("metadata", {})
        model = metadata.get("actual_model") or kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])

        # Get token usage from response
        usage = {}
        if hasattr(completion_response, 'usage') and completion_response.usage:
            usage = {
                "prompt_tokens": getattr(completion_response.usage, 'prompt_tokens', 0),
                "completion_tokens": getattr(completion_response.usage, 'completion_tokens', 0),
                "total_tokens": getattr(completion_response.usage, 'total_tokens', 0)
            }

        # Create log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc),
            "model": model,
            "task_type": kwargs.get("metadata", {}).get("task_type", "unknown"),
            "status": "success",
            "duration_ms": duration_ms,
            "tokens_used": usage.get("total_tokens", 0),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "user_id": kwargs.get("user", "system"),
            "messages_count": len(messages),
            "metadata": kwargs.get("metadata", {})
        }

        # Insert into MongoDB
        db.llm_usage.insert_one(log_entry)

    except Exception as e:
        logger.error(f"Failed to log LLM usage to MongoDB: {e}")


def custom_mongodb_failure_callback(
    kwargs,                      # kwargs to completion
    completion_response,         # response/exception from completion
    start_time, end_time         # start/end time
):
    """Log LLM failures to MongoDB"""
    try:
        db = get_database()

        # Calculate duration
        duration_ms = (end_time - start_time).total_seconds() * 1000

        # Extract information
        model = kwargs.get("model", "unknown")
        error_message = str(completion_response) if completion_response else "Unknown error"

        # Create log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc),
            "model": model,
            "task_type": kwargs.get("metadata", {}).get("task_type", "unknown"),
            "status": "failure",
            "duration_ms": duration_ms,
            "tokens_used": 0,
            "error": error_message,
            "user_id": kwargs.get("user", "system"),
            "metadata": kwargs.get("metadata", {})
        }

        # Insert into MongoDB
        db.llm_usage.insert_one(log_entry)

    except Exception as e:
        logger.error(f"Failed to log LLM failure to MongoDB: {e}")


class LLMManager:
    """
    Unified LLM Manager using LiteLLM Router

    Features:
    - Automatic fallback chains
    - Latency-based routing
    - In-memory caching (with Redis support)
    - User preference overrides
    - Support for 100+ LLM providers
    """

    _instance = None
    _router = None
    _config = None
    _user_preferences = {}  # In-memory cache for user model preferences
    _preferences_loaded = False  # Track if preferences have been loaded from MongoDB

    def __new__(cls):
        """Singleton pattern to ensure one router instance"""
        if cls._instance is None:
            cls._instance = super(LLMManager, cls).__new__(cls)
            cls._instance._initialize()
            cls._instance._load_preferences_from_mongodb()
        return cls._instance

    def _load_preferences_from_mongodb(self):
        """Load all user preferences from MongoDB into memory cache"""
        if self._preferences_loaded:
            return

        try:
            db = get_database()
            if db is None:
                logger.warning("MongoDB not available, preferences will not persist")
                self._preferences_loaded = True
                return

            # Load all preferences from MongoDB
            prefs = list(db.llm_preferences.find())
            for pref in prefs:
                user_id = pref.get('user_id', 'default')
                task_type = pref.get('task_type')
                model_name = pref.get('model_name')

                if task_type and model_name:
                    if user_id not in self._user_preferences:
                        self._user_preferences[user_id] = {}
                    self._user_preferences[user_id][task_type] = model_name

            self._preferences_loaded = True
            logger.info(f"Loaded {len(prefs)} LLM preferences from MongoDB")

        except Exception as e:
            logger.error(f"Failed to load preferences from MongoDB: {e}")
            self._preferences_loaded = True  # Mark as loaded to prevent repeated failures

    def _initialize(self):
        """Initialize LiteLLM Router with configuration"""
        if self._router is not None:
            return  # Already initialized

        # Load configuration
        config_path = Path(__file__).parent.parent.parent / "litellm_config.yaml"

        if not config_path.exists():
            logger.warning(f"LiteLLM config not found at {config_path}, using fallback configuration")
            self._config = self._get_fallback_config()
        else:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)

        # Initialize caching if enabled
        if self._config.get('router_settings', {}).get('caching', False):
            cache_params = self._config.get('router_settings', {}).get('cache_params', {})
            if cache_params.get('type') == 'redis':
                # Redis caching
                Cache(
                    type="redis",
                    host=cache_params.get('host', 'localhost'),
                    port=cache_params.get('port', 6379),
                    ttl=cache_params.get('ttl', 86400)
                )
                logger.info("✅ LiteLLM Redis caching enabled")
            else:
                # In-memory caching
                Cache(type="local")
                logger.info("✅ LiteLLM in-memory caching enabled")

        # Note: Callbacks are manually called in completion() and completion_sync()
        # because litellm callbacks don't work with Router.acompletion()

        # Create router
        try:
            model_list = self._config.get('model_list', [])
            router_settings = self._config.get('router_settings', {})

            self._router = Router(
                model_list=model_list,
                fallbacks=router_settings.get('fallbacks', []),
                context_window_fallbacks=router_settings.get('context_window_fallbacks', []),
                num_retries=router_settings.get('num_retries', 3),
                timeout=router_settings.get('timeout', 60),
                routing_strategy=router_settings.get('routing_strategy', 'latency-based-routing'),
                set_verbose=router_settings.get('set_verbose', False)
            )

            logger.info(f"✅ LiteLLM Router initialized with {len(model_list)} model configurations")
            logger.info(f"📊 Routing strategy: {router_settings.get('routing_strategy')}")
            logger.info(f"🔄 Fallback chains configured: {len(router_settings.get('fallbacks', []))}")
            logger.info(f"📝 MongoDB usage tracking enabled")

        except Exception as e:
            logger.error(f"❌ Failed to initialize LiteLLM Router: {e}")
            raise

    def _get_fallback_config(self) -> Dict:
        """Fallback configuration if litellm_config.yaml is missing"""
        return {
            'model_list': [
                {
                    'model_name': 'default',
                    'litellm_params': {
                        'model': 'gpt-4o-mini',
                        'api_key': os.getenv('OPENAI_API_KEY'),
                        'temperature': 0.3,
                        'max_tokens': 2000
                    }
                }
            ],
            'router_settings': {
                'num_retries': 3,
                'timeout': 60,
                'caching': True,
                'cache_params': {'type': 'local'}
            }
        }

    def set_user_preference(self, task_type: str, model_name: str, user_id: str = "default"):
        """
        Set user's model preference for a specific task type

        Args:
            task_type: Task type (e.g., "tag_suggestion", "summarization")
            model_name: Model name from litellm_config.yaml (None to delete)
            user_id: User identifier (default: "default")
        """
        # Update in-memory cache
        if user_id not in self._user_preferences:
            self._user_preferences[user_id] = {}

        if model_name is None:
            # Delete preference
            self._user_preferences[user_id].pop(task_type, None)

            # Delete from MongoDB
            try:
                db = get_database()
                if db is not None:
                    db.llm_preferences.delete_one({'user_id': user_id, 'task_type': task_type})
                    logger.info(f"✅ Deleted preference for user '{user_id}': {task_type} (removed from MongoDB)")
            except Exception as e:
                logger.error(f"Failed to delete preference from MongoDB: {e}")
        else:
            # Set preference
            self._user_preferences[user_id][task_type] = model_name

            # Persist to MongoDB
            try:
                db = get_database()
                if db is not None:
                    db.llm_preferences.update_one(
                        {'user_id': user_id, 'task_type': task_type},
                        {
                            '$set': {
                                'model_name': model_name,
                                'updated_at': datetime.now(timezone.utc)
                            },
                            '$setOnInsert': {
                                'created_at': datetime.now(timezone.utc)
                            }
                        },
                        upsert=True
                    )
                    logger.info(f"✅ Set preference for user '{user_id}': {task_type} -> {model_name} (saved to MongoDB)")
                else:
                    logger.info(f"✅ Set preference for user '{user_id}': {task_type} -> {model_name} (memory only)")
            except Exception as e:
                logger.error(f"Failed to save preference to MongoDB: {e}")
                logger.info(f"✅ Set preference for user '{user_id}': {task_type} -> {model_name} (memory only)")

    def get_user_preference(self, task_type: str, user_id: str = "default") -> Optional[str]:
        """
        Get user's model preference for a specific task type

        Args:
            task_type: Task type
            user_id: User identifier

        Returns:
            Model name or None if no preference set
        """
        return self._user_preferences.get(user_id, {}).get(task_type)

    def get_all_user_preferences(self, user_id: str = "default") -> Dict[str, str]:
        """Get all model preferences for a user"""
        return self._user_preferences.get(user_id, {})

    def get_available_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all available models grouped by task type

        Returns:
            Dictionary mapping task types to list of model configurations
        """
        models_by_task = {}

        for model_config in self._config.get('model_list', []):
            model_name = model_config.get('model_name')
            litellm_params = model_config.get('litellm_params', {})

            if model_name not in models_by_task:
                models_by_task[model_name] = []

            models_by_task[model_name].append({
                'model': litellm_params.get('model'),
                'provider': self._extract_provider(litellm_params.get('model', '')),
                'temperature': litellm_params.get('temperature'),
                'max_tokens': litellm_params.get('max_tokens'),
            })

        return models_by_task

    def _extract_provider(self, model_string: str) -> str:
        """Extract provider from model string (e.g., 'anthropic/claude-4' -> 'anthropic')"""
        if '/' in model_string:
            return model_string.split('/')[0]
        return 'openai'  # Default

    def _resolve_actual_model(self, task_type: str) -> str:
        """
        Resolve the actual model name from litellm_config for a given task type.

        Args:
            task_type: Task type (e.g., "tag_suggestion", "entity_extraction")

        Returns:
            Actual model name (e.g., "claude-sonnet-4-20250514")
            Falls back to task_type if not found in config
        """
        try:
            # Get first model configuration for this task type
            for model_config in self._config.get('model_list', []):
                if model_config.get('model_name') == task_type:
                    litellm_model = model_config.get('litellm_params', {}).get('model', '')

                    # Extract just the model name without provider prefix
                    # e.g., "anthropic/claude-sonnet-4-20250514" -> "claude-sonnet-4-20250514"
                    if '/' in litellm_model:
                        return litellm_model.split('/', 1)[1]
                    return litellm_model

            # Fallback: return task_type if not found
            logger.warning(f"No model config found for task_type '{task_type}', using task_type as model name")
            return task_type

        except Exception as e:
            logger.error(f"Error resolving model for task_type '{task_type}': {e}")
            return task_type

    async def completion(
        self,
        task_type: str,
        messages: List[Dict[str, str]],
        user_id: str = "default",
        override_params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Generate completion using the router

        Args:
            task_type: Task type (e.g., "tag_suggestion", "summarization")
            messages: Chat messages in OpenAI format
            user_id: User identifier for preference lookup
            override_params: Optional parameters to override config
            **kwargs: Additional parameters for LiteLLM

        Returns:
            LiteLLM completion response
        """
        # Check for user preference or use task_type for routing
        model_name = self.get_user_preference(task_type, user_id) or task_type

        # Resolve actual model name for logging (e.g., "claude-sonnet-4-20250514")
        actual_model_name = self._resolve_actual_model(task_type)

        # Merge parameters
        params = {
            'model': model_name,  # Keep task_type for Router routing
            'messages': messages,
            'metadata': {
                'task_type': task_type,
                'user_id': user_id,
                'actual_model': actual_model_name,  # Add actual model for logging
                **kwargs.get('metadata', {})
            },
            **kwargs
        }

        if override_params:
            params.update(override_params)

        try:
            logger.info(f"🤖 Calling LLM for task '{task_type}' with model '{actual_model_name}'")

            # Manual callback execution for Router calls (since litellm callbacks don't work with Router)
            import time
            from datetime import datetime, timezone
            start_time = datetime.now(timezone.utc)

            try:
                response = await self._router.acompletion(**params)
                end_time = datetime.now(timezone.utc)

                # Manually call success callback
                custom_mongodb_callback(params, response, start_time, end_time)

                logger.info(f"✅ LLM response received for task '{task_type}'")
                return response
            except Exception as llm_error:
                end_time = datetime.now(timezone.utc)

                # Manually call failure callback
                custom_mongodb_failure_callback(params, llm_error, start_time, end_time)
                raise

        except Exception as e:
            logger.error(f"❌ LLM completion failed for task '{task_type}': {e}")
            raise

    def completion_sync(
        self,
        task_type: str,
        messages: List[Dict[str, str]],
        user_id: str = "default",
        override_params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Synchronous version of completion

        Args:
            task_type: Task type
            messages: Chat messages
            user_id: User identifier
            override_params: Optional parameters
            **kwargs: Additional parameters

        Returns:
            LiteLLM completion response
        """
        # Check for user preference
        model_name = self.get_user_preference(task_type, user_id) or task_type

        # Resolve actual model name for logging (e.g., "claude-sonnet-4-20250514")
        actual_model_name = self._resolve_actual_model(task_type)

        # Merge parameters
        params = {
            'model': model_name,
            'messages': messages,
            'metadata': {
                'task_type': task_type,
                'user_id': user_id,
                'actual_model': actual_model_name,  # Add actual model for logging
                **kwargs.get('metadata', {})
            },
            **kwargs
        }

        if override_params:
            params.update(override_params)

        try:
            logger.info(f"🤖 Calling LLM (sync) for task '{task_type}' with model '{actual_model_name}'")

            # Manual callback execution for Router calls (since litellm callbacks don't work with Router)
            from datetime import datetime, timezone
            start_time = datetime.now(timezone.utc)

            try:
                response = self._router.completion(**params)
                end_time = datetime.now(timezone.utc)

                # Manually call success callback
                custom_mongodb_callback(params, response, start_time, end_time)

                logger.info(f"✅ LLM response received for task '{task_type}'")
                return response
            except Exception as llm_error:
                end_time = datetime.now(timezone.utc)

                # Manually call failure callback
                custom_mongodb_failure_callback(params, llm_error, start_time, end_time)
                raise

        except Exception as e:
            logger.error(f"❌ LLM completion failed for task '{task_type}': {e}")
            raise

    def get_task_info(self, task_type: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific task type

        Args:
            task_type: Task type name

        Returns:
            Dictionary with task configuration or None
        """
        for model_config in self._config.get('model_list', []):
            if model_config.get('model_name') == task_type:
                return {
                    'task_type': task_type,
                    'model': model_config.get('litellm_params', {}).get('model'),
                    'provider': self._extract_provider(
                        model_config.get('litellm_params', {}).get('model', '')
                    ),
                    'temperature': model_config.get('litellm_params', {}).get('temperature'),
                    'max_tokens': model_config.get('litellm_params', {}).get('max_tokens'),
                }
        return None

    def get_all_tasks(self) -> List[str]:
        """Get list of all available task types"""
        return list(set(
            model_config.get('model_name')
            for model_config in self._config.get('model_list', [])
        ))

    def reset(self):
        """Reset the singleton instance (useful for testing)"""
        LLMManager._instance = None
        LLMManager._router = None
        LLMManager._config = None
        LLMManager._user_preferences = {}


# Convenience function for easy imports
def get_llm_manager() -> LLMManager:
    """Get the LLM Manager singleton instance"""
    return LLMManager()
