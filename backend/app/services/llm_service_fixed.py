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
from langchain_google_genai import ChatGoogleGenerativeAI
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
    def __init__(self):
        """Initialize LLM service with configuration"""
        # Load configurations
        with open('llm.json', 'r') as f:
            self.llm_config = json.load(f)
        
        with open('prompts_config.json', 'r') as f:
            self.prompts = json.load(f)
        
        # Initialize clients dictionary for different providers
        self.clients = {}
        
        # Note: We NO LONGER keep a single OpenAI client
        # All API calls go through provider-specific clients
        
        # Cache for responses
        self._cache = {}
        self._cache_timestamps = {}
    
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
                if 'o1' in model or model_config.get('is_reasoning', False):
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
                api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not found in environment")
                self.clients[client_key] = ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=api_key,
                    temperature=model_config.get('temperature', 0.3),
                    max_tokens=model_config.get('max_tokens', 1000)
                )
                logger.info(f"Created Google client for model {model}")
            else:
                # Unknown provider
                raise ValueError(f"Unknown provider: {provider}. Supported: openai, anthropic, google")
        
        return self.clients[client_key]
    
    def _call_llm_with_logging(self, client, messages: List, model_config: Dict, task: str) -> Tuple[str, bool]:
        """
        Call LLM with proper logging and error handling
        Returns: (response_content, success)
        """
        provider = model_config.get('provider', 'openai')
        model = model_config.get('model', 'unknown')
        
        # Estimate tokens
        prompt_text = ' '.join([m.content if hasattr(m, 'content') else str(m) for m in messages])
        prompt_tokens = self._estimate_tokens(prompt_text)
        
        start_time = time.time()
        try:
            # Make the API call through LangChain
            response = client.invoke(messages)
            duration = time.time() - start_time
            
            # Extract content
            if hasattr(response, 'content'):
                content = response.content
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
            
            return content, True
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            # Log failed usage
            self._log_llm_usage(
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                response_tokens=0,
                duration=duration,
                task=task,
                success=False,
                error=error_msg
            )
            
            raise e
    
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
            content, success = self._call_llm_with_logging(
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
        
        # Get the prompt configuration
        prompt_config = self.prompts.get('tweet_tag_suggestion')
        if not prompt_config:
            logger.error("No tweet_tag_suggestion prompt configured")
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
            response_text, success = self._call_llm_with_logging(
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

# Export the fixed service
def get_llm_service():
    """Get singleton instance of LLM service"""
    if not hasattr(get_llm_service, '_instance'):
        get_llm_service._instance = LLMService()
    return get_llm_service._instance