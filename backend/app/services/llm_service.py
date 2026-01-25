"""
Fixed LLM Service for tag suggestions and content analysis
Uses configuration from llm.json and prompts_config.json
Supports multiple providers: OpenAI, Anthropic, Google
FIXED: Proper provider routing and comprehensive logging
"""
import json
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from langchain_anthropic import ChatAnthropic
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    ChatGoogleGenerativeAI = None
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import httpx
from functools import lru_cache
import hashlib
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

# Create a dedicated LLM usage logger
llm_logger = logging.getLogger('llm_usage')
llm_logger.setLevel(logging.INFO)

class LLMService:
    # Circuit breaker configuration
    CIRCUIT_FAILURE_THRESHOLD = 5  # Open circuit after 5 consecutive failures
    CIRCUIT_RESET_TIMEOUT = 300  # Reset after 5 minutes (300 seconds)

    def __init__(self):
        """Initialize LLM service with configuration"""
        # Load configurations using absolute paths (CFG-006)
        # Config files are in backend/ directory (parent of app/services/)
        from pathlib import Path
        config_dir = Path(__file__).parent.parent.parent
        llm_config_path = config_dir / 'llm.json'
        prompts_config_path = config_dir / 'prompts_config.json'

        with open(llm_config_path, 'r') as f:
            self.llm_config = json.load(f)

        with open(prompts_config_path, 'r') as f:
            self.prompts = json.load(f)

        # Initialize clients dictionary for different providers
        self.clients = {}

        # Note: We NO LONGER keep a single OpenAI client
        # All API calls go through provider-specific clients

        # Cache for responses
        self._cache = {}
        self._cache_timestamps = {}

        # Circuit breaker state per provider (OBS-004)
        # Format: {provider: {'failures': int, 'last_failure': datetime, 'state': 'closed'|'open'|'half-open'}}
        self._circuit_state = {}
    
    def _log_llm_usage(self, provider: str, model: str, prompt_tokens: int, response_tokens: int, 
                       duration: float, task: str, success: bool = True, error: str = None):
        """Log LLM usage for monitoring and debugging"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'provider': provider,
            'model': model,
            'task': task,
            'prompt_tokens': prompt_tokens,
            'response_tokens': response_tokens,
            'total_tokens': prompt_tokens + response_tokens,
            'duration_seconds': round(duration, 2),
            'success': success,
            'error': error
        }
        
        # Log to dedicated LLM logger
        if success:
            llm_logger.info(f"LLM_USAGE: {json.dumps(log_entry)}")
        else:
            llm_logger.error(f"LLM_ERROR: {json.dumps(log_entry)}")
        
        # Also log summary to main logger
        if success:
            logger.info(f"LLM Call: {provider}/{model} for {task} - {prompt_tokens}+{response_tokens}={prompt_tokens+response_tokens} tokens in {duration:.2f}s")
        else:
            logger.error(f"LLM Failed: {provider}/{model} for {task} - Error: {error}")
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count"""
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4

    def _get_circuit_state(self, provider: str) -> dict:
        """Get current circuit breaker state for a provider"""
        if provider not in self._circuit_state:
            self._circuit_state[provider] = {
                'failures': 0,
                'last_failure': None,
                'state': 'closed'
            }
        return self._circuit_state[provider]

    def _check_circuit(self, provider: str) -> bool:
        """
        Check if circuit allows requests. Returns True if request should proceed.

        Circuit states:
        - closed: Normal operation, requests proceed
        - open: Too many failures, requests fail fast
        - half-open: Testing if service recovered, allow one probe request
        """
        circuit = self._get_circuit_state(provider)

        if circuit['state'] == 'closed':
            return True

        if circuit['state'] == 'open':
            # Check if timeout has elapsed
            if circuit['last_failure']:
                elapsed = (datetime.now() - circuit['last_failure']).total_seconds()
                if elapsed >= self.CIRCUIT_RESET_TIMEOUT:
                    # Move to half-open, allow probe request
                    circuit['state'] = 'half-open'
                    logger.info(f"Circuit breaker for {provider}: HALF-OPEN (allowing probe request)")
                    return True
            # Still open, fail fast
            logger.warning(f"Circuit breaker for {provider}: OPEN (failing fast)")
            return False

        # half-open: allow the probe request
        return True

    def _record_success(self, provider: str):
        """Record successful request, potentially closing the circuit"""
        circuit = self._get_circuit_state(provider)
        if circuit['state'] != 'closed':
            logger.info(f"Circuit breaker for {provider}: CLOSED (recovered)")
        circuit['failures'] = 0
        circuit['state'] = 'closed'

    def _record_failure(self, provider: str):
        """Record failed request, potentially opening the circuit"""
        circuit = self._get_circuit_state(provider)
        circuit['failures'] += 1
        circuit['last_failure'] = datetime.now()

        if circuit['state'] == 'half-open':
            # Probe failed, back to open
            circuit['state'] = 'open'
            logger.warning(f"Circuit breaker for {provider}: OPEN (probe failed, {circuit['failures']} total failures)")
        elif circuit['failures'] >= self.CIRCUIT_FAILURE_THRESHOLD:
            circuit['state'] = 'open'
            logger.warning(f"Circuit breaker for {provider}: OPEN (threshold reached: {circuit['failures']} failures)")

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for all providers (for monitoring)"""
        status = {
            'config': {
                'failure_threshold': self.CIRCUIT_FAILURE_THRESHOLD,
                'reset_timeout_seconds': self.CIRCUIT_RESET_TIMEOUT
            },
            'providers': {}
        }

        for provider, circuit in self._circuit_state.items():
            time_since_failure = None
            time_until_reset = None

            if circuit['last_failure']:
                elapsed = (datetime.now() - circuit['last_failure']).total_seconds()
                time_since_failure = round(elapsed, 1)
                if circuit['state'] == 'open':
                    time_until_reset = max(0, round(self.CIRCUIT_RESET_TIMEOUT - elapsed, 1))

            status['providers'][provider] = {
                'state': circuit['state'],
                'failures': circuit['failures'],
                'last_failure': circuit['last_failure'].isoformat() if circuit['last_failure'] else None,
                'time_since_failure_seconds': time_since_failure,
                'time_until_reset_seconds': time_until_reset
            }

        # Add providers that haven't been used yet
        known_providers = ['openai', 'anthropic', 'google', 'xai']
        for provider in known_providers:
            if provider not in status['providers']:
                status['providers'][provider] = {
                    'state': 'closed',
                    'failures': 0,
                    'last_failure': None,
                    'time_since_failure_seconds': None,
                    'time_until_reset_seconds': None
                }

        return status

    def reset_circuit_breaker(self, provider: str) -> bool:
        """Manually reset circuit breaker for a provider"""
        if provider in self._circuit_state:
            self._circuit_state[provider] = {
                'failures': 0,
                'last_failure': None,
                'state': 'closed'
            }
            logger.info(f"Circuit breaker for {provider}: MANUALLY RESET to closed")
            return True
        return False

    def _get_client(self, model_config: Dict):
        """Get or create client for the specified provider"""
        provider = model_config.get('provider', 'openai')
        model = model_config.get('model')
        
        # Log the model selection
        logger.info(f"Getting client for provider={provider}, model={model}")
        
        # Create unique key for this configuration
        client_key = f"{provider}:{model}"
        
        if client_key not in self.clients:
            if provider == 'anthropic':
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not found in environment")
                self.clients[client_key] = ChatAnthropic(
                    model=model,
                    anthropic_api_key=api_key,
                    temperature=model_config.get('temperature', 0.3),
                    max_tokens=model_config.get('max_tokens', 1000)
                )
                logger.info(f"Created Anthropic client for model {model}")
            elif provider == 'openai':
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment")
                # Check if it's a reasoning model that needs special handling
                if model and ('o1' in model or model_config.get('is_reasoning', False)):
                    # For reasoning models, we might need the raw OpenAI client
                    # But we'll wrap it in a compatible interface
                    self.clients[client_key] = ChatOpenAI(
                        model=model,
                        openai_api_key=api_key,
                        temperature=model_config.get('temperature', 1),  # o1 models require temp=1
                        max_tokens=model_config.get('max_tokens', 1000)
                    )
                else:
                    self.clients[client_key] = ChatOpenAI(
                        model=model,
                        openai_api_key=api_key,
                        temperature=model_config.get('temperature', 0.3),
                        max_tokens=model_config.get('max_tokens', 1000)
                    )
                logger.info(f"Created OpenAI client for model {model}")
            elif provider == 'google':
                if not GOOGLE_AVAILABLE:
                    raise ValueError("Google Gemini provider not available. Install langchain-google-genai package.")
                api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not found in environment")
                # Strip 'gemini/' prefix if present - ChatGoogleGenerativeAI expects just the model name
                google_model = model.replace('gemini/', '') if model and model.startswith('gemini/') else (model or '')
                self.clients[client_key] = ChatGoogleGenerativeAI(
                    model=google_model,
                    google_api_key=api_key,
                    temperature=model_config.get('temperature', 0.3),
                    max_tokens=model_config.get('max_tokens', 1000)
                )
                logger.info(f"Created Google client for model {model}")
            else:
                # Unknown provider
                raise ValueError(f"Unknown provider: {provider}. Supported: openai, anthropic, google")
        
        return self.clients[client_key]
    
    def _call_llm_with_logging(self, client, messages: List, model_config: Dict, task: str, max_retries: int = 3) -> Tuple[str, bool]:
        """
        Call LLM with proper logging, error handling, retry logic, and circuit breaker.
        Returns: (response_content, success)
        """
        provider = model_config.get('provider', 'openai')
        model = model_config.get('model', 'unknown')

        # Check circuit breaker before making request (OBS-004)
        if not self._check_circuit(provider):
            raise RuntimeError(f"Circuit breaker open for {provider}. Service unavailable after repeated failures.")

        # Estimate tokens
        prompt_text = ' '.join([m.content if hasattr(m, 'content') else str(m) for m in messages])
        prompt_tokens = self._estimate_tokens(prompt_text)

        last_exception = None
        for attempt in range(max_retries):
            start_time = time.time()
            try:
                # Make the API call through LangChain
                response = client.invoke(messages)
                duration = time.time() - start_time

                # Extract content - handle different response formats
                if hasattr(response, 'content'):
                    content = response.content
                    logger.info(f"Response content type: {type(content)}, value preview: {str(content)[:200] if content else 'None'}")
                    # Gemini 3 models may return list of content blocks
                    if isinstance(content, list):
                        # Extract text from content blocks
                        text_parts = []
                        for part in content:
                            if isinstance(part, str):
                                text_parts.append(part)
                            elif hasattr(part, 'text'):
                                text_parts.append(part.text)
                            elif isinstance(part, dict) and 'text' in part:
                                text_parts.append(part['text'])
                        content = '\n'.join(text_parts)
                    elif not isinstance(content, str):
                        # Fallback: convert to string
                        content = str(content)
                else:
                    content = str(response)

                response_tokens = self._estimate_tokens(content)

                # Log successful usage
                self._log_llm_usage(
                    provider=provider,
                    model=model,
                    prompt_tokens=prompt_tokens,
                    response_tokens=response_tokens,
                    duration=duration,
                    task=task,
                    success=True
                )

                # Record success for circuit breaker
                self._record_success(provider)

                return content, True

            except Exception as e:
                duration = time.time() - start_time
                error_msg = str(e)
                last_exception = e

                # Classify error type for better debugging (OBS-001)
                error_type = type(e).__name__
                if 'connection' in error_msg.lower() or 'network' in error_msg.lower():
                    error_category = 'network'
                elif '429' in error_msg or 'rate limit' in error_msg.lower():
                    error_category = 'rate_limit'
                elif any(code in error_msg for code in ['500', '502', '503', '504']):
                    error_category = 'server_error'
                elif 'timeout' in error_msg.lower():
                    error_category = 'timeout'
                elif 'invalid' in error_msg.lower() or 'parse' in error_msg.lower():
                    error_category = 'parsing'
                elif 'auth' in error_msg.lower() or '401' in error_msg or '403' in error_msg:
                    error_category = 'auth'
                else:
                    error_category = 'unknown'

                # Check if error is transient (rate limit, server error)
                is_transient = error_category in ['rate_limit', 'server_error', 'timeout', 'network']

                if is_transient and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1  # Exponential backoff: 2s, 3s, 5s
                    logger.warning(f"Transient error ({error_category}) on attempt {attempt + 1}/{max_retries}: {error_type}: {error_msg}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                # Log failed usage with enhanced context (final attempt or non-transient error)
                self._log_llm_usage(
                    provider=provider,
                    model=model,
                    prompt_tokens=prompt_tokens,
                    response_tokens=0,
                    duration=duration,
                    task=task,
                    success=False,
                    error=f"[{error_category}] {error_type}: {error_msg}"
                )

                # Log full exception details for debugging
                logger.error(f"LLM call failed for task '{task}' after {attempt + 1} attempt(s): "
                            f"provider={provider}, model={model}, category={error_category}, "
                            f"error={error_type}: {error_msg}", exc_info=True)

                # Record failure for circuit breaker (only on final failure or non-transient errors)
                self._record_failure(provider)

                raise e

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("LLM call failed after all retries")
    
    def get_completion(self, prompt_type: str, **kwargs) -> Optional[str]:
        """
        Get completion from LLM based on prompt type
        FIXED: Always uses the correct provider-specific client
        """
        # Check if prompt type exists
        if prompt_type not in self.prompts:
            logger.error(f"Prompt type '{prompt_type}' not found in prompts_config.json")
            return None
        
        prompt_template = self.prompts[prompt_type]
        
        # Get the model configuration for this prompt type
        model_key = prompt_template.get('model', 'general')
        model_config = self.llm_config['models'].get(model_key)
        if not model_config:
            logger.error(f"Model '{model_key}' not found in llm.json")
            return None
        
        # Build the prompt
        user_prompt = prompt_template['user_template'].format(**kwargs)
        
        try:
            # Get the appropriate client for this provider
            client = self._get_client(model_config)
            
            # Check if this is a reasoning model
            is_reasoning = model_config.get('is_reasoning', False)
            
            # Build messages
            if is_reasoning:
                # Reasoning models: combine system and user prompts
                combined_prompt = f"{prompt_template['system']}\n\n{user_prompt}"
                messages = [HumanMessage(content=combined_prompt)]
            else:
                messages = [
                    SystemMessage(content=prompt_template['system']),
                    HumanMessage(content=user_prompt)
                ]
            
            # Make the API call with logging
            content, _ = self._call_llm_with_logging(
                client=client,
                messages=messages,
                model_config=model_config,
                task=prompt_type
            )

            return content
            
        except Exception as e:
            logger.error(f"Error in get_completion: {e}")
            return None
    
    def suggest_tags(self, tweet_text: str, author: str) -> List[str]:
        """
        Suggest tags for a tweet using LLM
        FIXED: Uses the correct provider based on configuration
        """
        # Handle empty or very short text
        if not tweet_text or len(tweet_text.strip()) < 10:
            logger.info(f"Text too short for tag generation, using fallback")
            return self._fallback_tag_extraction(tweet_text)
        
        # Get the model configuration
        model_config = self.llm_config['models'].get('tag_suggestion')
        if not model_config:
            logger.error("No tag_suggestion model configured")
            return []
        
        # Get the prompt configuration (try both names for compatibility)
        prompt_config = self.prompts.get('tweet_tag_suggestion') or self.prompts.get('tag_suggestion')
        if not prompt_config:
            logger.error("No tag suggestion prompt configured")
            return []
        
        try:
            # Get the appropriate client
            client = self._get_client(model_config)
            
            # Build the prompts
            system_prompt = prompt_config.get('system', '')
            user_template = prompt_config.get('user_template', '')
            user_prompt = user_template.replace('{author}', author or 'Unknown')
            user_prompt = user_prompt.replace('{text}', tweet_text)
            user_prompt = user_prompt.replace('{max_tags}', '5')
            
            # Build messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # Make the API call with logging
            response_text, _ = self._call_llm_with_logging(
                client=client,
                messages=messages,
                model_config=model_config,
                task='tag_suggestion'
            )
            
            # Parse response
            try:
                import re
                json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                if json_match:
                    tags = json.loads(json_match.group())
                else:
                    tags = []
            except:
                tags = []
            
            logger.info(f"Generated {len(tags)} tags for tweet")
            return tags
            
        except Exception as e:
            logger.error(f"Error in suggest_tags: {e}")
            return self._fallback_tag_extraction(tweet_text)
    
    def _fallback_tag_extraction(self, text: str) -> List[str]:
        """Simple keyword extraction fallback"""
        if not text:
            return []
        
        # Simple keyword extraction
        keywords = []
        important_words = ['AI', 'ML', 'GPT', 'LLM', 'model', 'data', 'neural', 'transformer']
        text_lower = text.lower()
        
        for word in important_words:
            if word.lower() in text_lower:
                keywords.append(word.lower())
        
        return keywords[:5]  # Limit to 5 tags
    
    async def generate_completion_async(self, prompt: str, model: Optional[str] = None, temperature: float = 0.3, max_tokens: int = 1000) -> str:
        """
        Async version of generate_completion for compatibility
        Simply wraps the sync version since LangChain handles async internally
        """
        import asyncio
        from functools import partial

        # Run the sync version in an executor using partial for proper typing
        loop = asyncio.get_event_loop()
        func = partial(self.generate_completion, prompt, model, temperature, max_tokens)
        return await loop.run_in_executor(None, func)
    
    def generate_completion(self, prompt: str, model: Optional[str] = None, temperature: float = 0.3, max_tokens: int = 1000) -> str:
        """
        Generate a completion using the LLM - compatibility method for paper analysis
        
        Args:
            prompt: The prompt text
            model: Model name (e.g., 'gemini-2.5-pro', 'claude-opus-4-1-20250805')
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or empty string on failure
        """
        try:
            # If a specific model is provided, find its configuration
            model_config = None
            if model:
                # Search for the model in our configs
                for _, config in self.llm_config['models'].items():
                    if config.get('model') == model:
                        model_config = config
                        break
                
                if not model_config:
                    # Create a basic config for the requested model
                    if 'gemini' in model.lower():
                        model_config = {
                            'provider': 'google',
                            'model': model,
                            'temperature': temperature,
                            'max_tokens': max_tokens
                        }
                    elif 'claude' in model.lower():
                        model_config = {
                            'provider': 'anthropic',
                            'model': model,
                            'temperature': temperature,
                            'max_tokens': max_tokens
                        }
                    elif 'gpt' in model.lower() or 'o1' in model.lower():
                        model_config = {
                            'provider': 'openai',
                            'model': model,
                            'temperature': temperature,
                            'max_tokens': max_tokens
                        }
                    else:
                        logger.error(f"Unknown model: {model}")
                        return ""
            else:
                # Use default general model
                model_config = self.llm_config['models'].get('chat_general', {})
            
            # Get the appropriate client
            client = self._get_client(model_config)
            
            # Build messages (just user message for simple completion)
            messages = [HumanMessage(content=prompt)]
            
            # Make the API call with logging
            content, success = self._call_llm_with_logging(
                client=client,
                messages=messages,
                model_config=model_config,
                task='generate_completion'
            )
            
            return content if success else ""
            
        except Exception as e:
            logger.error(f"Error in generate_completion: {e}")
            return ""

# Module-level singleton instance (lazy initialization)
_llm_service_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get singleton instance of LLM service"""
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance