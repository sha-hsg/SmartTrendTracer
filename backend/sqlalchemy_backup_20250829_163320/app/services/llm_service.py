"""
LLM Service for tag suggestions and content analysis
Uses configuration from llm.json and prompts_config.json
Supports multiple providers: OpenAI, Anthropic, Google
"""
import json
import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import httpx
from functools import lru_cache
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

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
        
        # Keep OpenAI client for backward compatibility with timeout
        openai_key = os.getenv(self.llm_config['api_settings']['api_key_env'])
        if openai_key:
            # Set timeout to 90 seconds (leaving 30s buffer for frontend's 120s timeout)
            self.client = OpenAI(
                api_key=openai_key,
                timeout=httpx.Timeout(90.0, connect=10.0)
            )
        
        # Cache for responses
        self._cache = {}
        self._cache_timestamps = {}
    
    def _get_client(self, model_config: Dict):
        """Get or create client for the specified provider"""
        provider = model_config.get('provider', 'openai')
        model = model_config.get('model')
        
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
            elif provider == 'openai':
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment")
                self.clients[client_key] = ChatOpenAI(
                    model=model,
                    openai_api_key=api_key,
                    temperature=model_config.get('temperature', 0.3),
                    max_tokens=model_config.get('max_tokens', 1000)
                )
            elif provider == 'google':
                api_key = os.getenv('GOOGLE_API_KEY')
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY not found in environment")
                self.clients[client_key] = ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=api_key,
                    temperature=model_config.get('temperature', 0.3),
                    max_tokens=model_config.get('max_tokens', 1000)
                )
            else:
                # Fallback to OpenAI client
                api_key = os.getenv('OPENAI_API_KEY')
                if api_key:
                    self.clients[client_key] = ChatOpenAI(
                        model=model,
                        openai_api_key=api_key,
                        temperature=model_config.get('temperature', 0.3),
                        max_tokens=model_config.get('max_tokens', 1000)
                    )
        
        return self.clients[client_key]
    
    def _get_cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key for prompt+model combination"""
        content = f"{model}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get cached response if still valid"""
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key)
            if timestamp:
                age = (datetime.now() - timestamp).total_seconds()
                ttl = self.prompts['settings']['cache_ttl_seconds']
                if age < ttl:
                    return self._cache[key]
        return None
    
    def _save_to_cache(self, key: str, value: Any):
        """Save response to cache"""
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now()
    
    def suggest_tags(self, tweet_text: str, author: str) -> List[str]:
        """
        Suggest tags for a tweet using LLM
        
        Args:
            tweet_text: The tweet content
            author: The tweet author username
            
        Returns:
            List of suggested tags
        """
        # Handle empty or very short text
        if not tweet_text or len(tweet_text.strip()) < 10:
            print(f"DEBUG: Using fallback - Tweet text too short for tag generation (length: {len(tweet_text.strip())}): '{tweet_text[:50]}...'")
            return self._fallback_tag_extraction(tweet_text)
        
        # For retweets, try to extract the actual content
        full_text = tweet_text
        if tweet_text.startswith('RT @'):
            # Check if we have the full retweet text
            if '…' in tweet_text or len(tweet_text) < 100:
                # Truncated retweet - extract what we can
                parts = tweet_text.split(':', 1)
                if len(parts) > 1:
                    full_text = parts[1].strip()
                    # If still truncated, use fallback
                    if '…' in full_text or len(full_text) < 30:
                        print(f"DEBUG: Using fallback - Truncated retweet detected (ellipsis: {'…' in full_text}, length: {len(full_text)}): '{tweet_text[:80]}...'")
                        print(f"DEBUG: Reason - Retweets with ellipsis or very short content cannot be properly analyzed by LLM")
                        return self._fallback_tag_extraction(tweet_text)
        
        # Get model configuration
        model_config = self.llm_config['models']['tag_suggestion']
        model_name = model_config['model']
        provider = model_config.get('provider', 'openai')
        
        # Build prompt
        prompt_template = self.prompts['tag_suggestion']
        user_prompt = prompt_template['user_template'].format(
            author=author,
            text=full_text
        )
        
        # Check cache
        cache_key = self._get_cache_key(user_prompt, model_name)
        cached = self._get_from_cache(cache_key)
        if cached:
            # Check if cached result has the API marker
            if "__api_success__" not in cached:
                # Old cache format, invalidate it
                cached = None
            else:
                return cached
        
        try:
            # Get the appropriate client
            client = self._get_client(model_config)
            
            # Check if this is a reasoning model (o1-mini, o1-preview, etc.)
            is_reasoning = model_config.get('is_reasoning', False)
            
            # Use LangChain for all providers
            if hasattr(client, 'invoke'):  # LangChain client
                if is_reasoning:
                    # Reasoning models: combine system and user prompts
                    combined_prompt = f"{prompt_template['system']}\n\n{user_prompt}"
                    messages = [HumanMessage(content=combined_prompt)]
                else:
                    # Standard models with system message
                    messages = [
                        SystemMessage(content=prompt_template['system']),
                        HumanMessage(content=user_prompt)
                    ]
                
                response = client.invoke(messages)
                content = response.content
            else:
                # Legacy OpenAI client (for backward compatibility)
                if is_reasoning:
                    combined_prompt = f"{prompt_template['system']}\n\n{user_prompt}"
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "user", "content": combined_prompt}
                        ],
                        max_completion_tokens=model_config.get('max_tokens', 500)
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": prompt_template['system']},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=model_config.get('temperature', 0.3),
                        max_tokens=model_config.get('max_tokens', 500)
                    )
                content = response.choices[0].message.content
            
            # Parse response
            
            # Try to parse as JSON array
            try:
                # Extract JSON from response if wrapped in text
                import re
                json_match = re.search(r'\[.*?\]', content, re.DOTALL)
                if json_match:
                    tags = json.loads(json_match.group())
                else:
                    tags = json.loads(content)
                
                # Clean up tags but preserve capitalization for AI suggestions
                cleaned_tags = []
                for tag in tags:
                    if tag:
                        # Just replace spaces with hyphens, preserve capitalization
                        tag = str(tag).strip().replace(' ', '-')
                        cleaned_tags.append(tag)
                
                tags = cleaned_tags[:5]  # Limit to 5 tags
                
            except json.JSONDecodeError:
                # Fallback: extract words that look like tags
                tags = re.findall(r'["\']([\w-]+)["\']', content)
                tags = tags[:5]
            
            # Cache the result
            self._save_to_cache(cache_key, tags)
            
            # Mark that we successfully used the API
            if tags:
                tags.append("__api_success__")  # Internal marker
            
            return tags
            
        except Exception as e:
            print(f"DEBUG: Using fallback - Error calling LLM API: {e}")
            print(f"DEBUG: Reason - API call failed, using local NLP fallback for: '{tweet_text[:80]}...'")
            # Fallback to simple extraction
            return self._fallback_tag_extraction(tweet_text)
    
    def _fallback_tag_extraction(self, text: str) -> List[str]:
        """Intelligent fallback tag extraction using spaCy when LLM fails"""
        try:
            # Try to use spaCy for intelligent extraction
            from app.services.spacy_tagger import get_spacy_tagger
            spacy_tagger = get_spacy_tagger()
            tags = spacy_tagger.extract_tags(text, max_tags=5)
            if tags:
                print(f"DEBUG: spaCy fallback successful, extracted {len(tags)} tags")
                return tags
        except Exception as e:
            print(f"DEBUG: spaCy fallback failed: {e}, using simple keyword extraction")
            print(f"DEBUG: Reason - spaCy model not available or error in NLP processing")
        
        # If spaCy fails, fall back to simple keyword extraction
        tags = []
        
        # Extract hashtags
        import re
        hashtags = re.findall(r'#(\w+)', text)  # Don't lowercase here, normalize later
        tags.extend(hashtags[:2])
        
        # Extract @mentions as potential topics
        mentions = re.findall(r'@(\w+)', text)
        mentions = [m for m in mentions if m.lower() not in ['sama', 'openai', 'emollick', 'stanfordnlp', 'anthropicai', 'googledeepmi', 'huggingface']]
        tags.extend(mentions[:1])
        
        # Extract known AI keywords
        ai_keywords = [
            'gpt', 'chatgpt', 'llm', 'transformer', 'bert', 'claude', 'bard',
            'diffusion', 'neural', 'model', 'dataset', 'training', 'inference',
            'prompt', 'embedding', 'vector', 'attention', 'tokenization',
            'fine-tuning', 'rlhf', 'alignment', 'multimodal', 'benchmark',
            'open-source', 'api', 'safety', 'ethics', 'bias', 'evaluation'
        ]
        
        text_lower = text.lower()
        found_keywords = []
        for keyword in ai_keywords:
            if keyword in text_lower and keyword not in [t.lower() for t in tags]:
                found_keywords.append(keyword)
        
        tags.extend(found_keywords[:2])
        
        # Limit to 5 tags total
        tags = tags[:5]
        
        # Clean up tags - normalize for fallback
        cleaned_tags = []
        for tag in tags:
            if tag:
                # For fallback, we do normalize to lowercase
                tag = tag.strip().lower().replace(' ', '-')
                if tag not in cleaned_tags:
                    cleaned_tags.append(tag)
        
        print(f"DEBUG: Simple fallback extracted {len(cleaned_tags)} tags: {cleaned_tags}")
        return cleaned_tags
    
    def get_model_used(self, task_type: str = 'tag_suggestion') -> str:
        """
        Get the model name used for a specific task type
        
        Args:
            task_type: The type of task (e.g., 'tag_suggestion', 'summarization')
            
        Returns:
            The model name being used
        """
        if task_type in self.llm_config['models']:
            model_config = self.llm_config['models'][task_type]
            return model_config.get('model', 'Unknown')
        return 'Unknown'
    
    async def generate_completion_async(self, prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.3, max_tokens: int = 1000):
        """Generate a completion using the LLM asynchronously"""
        import asyncio
        
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate_completion,
            prompt,
            model,
            temperature,
            max_tokens
        )
    
    def _call_llm(self, prompt: str, model_config: Dict) -> str:
        """
        Internal method to call LLM with model configuration
        Used by various services for backward compatibility
        """
        model = model_config.get('model', 'gpt-4o-mini')
        temperature = model_config.get('temperature', 0.3)
        max_tokens = model_config.get('max_tokens', 1000)
        
        return self.generate_completion(prompt, model, temperature, max_tokens)
    
    async def generate_with_model(self, model_key: str, prompt_key: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a response using a specific model from config with a specific prompt template
        
        Args:
            model_key: Key from llm.json models section (e.g., 'orphan_tag_assignment')
            prompt_key: Key from prompts_config.json (e.g., 'assign_orphan_tags')
            **kwargs: Variables to format into the prompt template
            
        Returns:
            Parsed JSON response from the model
        """
        import logging
        import json
        logger = logging.getLogger(__name__)
        
        # Get model config
        model_config = self.llm_config['models'].get(model_key)
        if not model_config:
            raise ValueError(f"Model key '{model_key}' not found in llm.json")
        
        # Get prompt config
        prompt_config = self.prompts.get(prompt_key)
        if not prompt_config:
            raise ValueError(f"Prompt key '{prompt_key}' not found in prompts_config.json")
        
        # Format the prompt
        system_prompt = prompt_config.get('system', '')
        user_template = prompt_config.get('user_template', '')
        
        # Format user prompt with kwargs
        try:
            user_prompt = user_template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing required parameter for prompt template: {e}")
            raise ValueError(f"Missing required parameter for prompt template: {e}")
        
        # Get model parameters
        model_name = model_config.get('model')
        temperature = model_config.get('temperature', 0.3)
        max_tokens = model_config.get('max_tokens', 1000)
        
        logger.info(f"Calling {model_name} for {model_key} with {prompt_key} prompt")
        
        # Generate response
        full_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
        response = self.generate_completion(
            prompt=full_prompt,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Parse JSON response if expected
        output_format = prompt_config.get('output_format', 'text')
        if output_format == 'json':
            try:
                # Clean JSON if needed
                if isinstance(response, str):
                    # Remove markdown code blocks if present
                    if '```json' in response:
                        response = response.split('```json')[1].split('```')[0]
                    elif '```' in response:
                        response = response.split('```')[1].split('```')[0]
                    response = response.strip()
                
                return json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Raw response: {response}")
                return {"error": "Failed to parse response", "raw": response}
        
        return {"response": response}
    
    def generate_text(self, prompt: str, system_message: str = None, max_tokens: int = 1000, temperature: float = 0.7, model: str = None) -> str:
        """
        Generate text with optional system message
        Used by paper repository service
        
        Args:
            prompt: The user prompt
            system_message: Optional system message
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation
            model: Optional model to use (if not provided, uses tag_suggestion model)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # DEBUG: Log all parameters
        logger.info(f"[DEBUG] ============ generate_text CALLED ============")
        logger.info(f"[DEBUG] - prompt length: {len(prompt)} chars")
        logger.info(f"[DEBUG] - system_message length: {len(system_message) if system_message else 0} chars")
        logger.info(f"[DEBUG] - max_tokens: {max_tokens}")
        logger.info(f"[DEBUG] - temperature: {temperature}")
        logger.info(f"[DEBUG] - model provided: {model}")
        
        # Check if this looks like a paper (has substantial content)
        if len(prompt) > 10000:
            logger.info(f"[DEBUG] >>> LARGE PROMPT DETECTED - Likely full paper!")
            logger.info(f"[DEBUG] >>> Exact prompt size: {len(prompt)} characters")
            # Log a sample from the middle to verify it's not truncated
            middle_pos = len(prompt) // 2
            logger.info(f"[DEBUG] >>> Sample from middle of prompt: ...{prompt[middle_pos:middle_pos+200]}...")
        else:
            logger.info(f"[DEBUG] >>> Small prompt - possibly truncated or abstract only")
        
        # Combine system message and prompt if provided
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        # Use provided model or default from config
        if model is None:
            model_config = self.llm_config['models'].get('tag_suggestion', {})
            model = model_config.get('model', 'gpt-4o-mini')
            logger.warning(f"[DEBUG] WARNING: No model provided, defaulting to tag_suggestion: {model}")
        else:
            logger.info(f"[DEBUG] Using provided model: {model}")
        
        logger.info(f"[DEBUG] CALLING generate_completion with:")
        logger.info(f"[DEBUG] - Model: {model}")
        logger.info(f"[DEBUG] - Max tokens: {max_tokens}")
        logger.info(f"[DEBUG] - Temperature: {temperature}")
        logger.info(f"[DEBUG] - Full prompt length: {len(full_prompt)} chars")
        
        return self.generate_completion(full_prompt, model, temperature, max_tokens)
    
    def generate_completion(self, prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.3, max_tokens: int = 1000) -> str:
        """Generate a completion using the LLM - uses config from llm.json"""
        import logging
        import time
        logger = logging.getLogger(__name__)
        
        logger.info(f"[DEBUG] generate_completion START:")
        logger.info(f"[DEBUG] - Model: {model}")
        logger.info(f"[DEBUG] - Max tokens: {max_tokens}")
        logger.info(f"[DEBUG] - Temperature: {temperature}")
        logger.info(f"[DEBUG] - Prompt length: {len(prompt)} chars")
        
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(prompt, model)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"[DEBUG] CACHE HIT - returning cached result")
                return cached_result
            
            logger.info(f"[DEBUG] CACHE MISS - making API call")
            
            # Determine provider from model name or config
            provider = None
            model_config = None
            
            # Search for model in config to get provider
            for config_name, config in self.llm_config['models'].items():
                if config.get('model') == model:
                    provider = config.get('provider', 'openai')
                    model_config = config
                    logger.info(f"[DEBUG] Found model config '{config_name}' with provider: {provider}")
                    break
            
            # If not found in config, guess provider from model name
            if provider is None:
                if "claude" in model.lower():
                    provider = 'anthropic'
                elif "gemini" in model.lower():
                    provider = 'google'
                else:
                    provider = 'openai'
                logger.info(f"[DEBUG] Guessed provider from model name: {provider}")
            
            # Initialize result variable
            result = None
            
            # Create appropriate client based on provider
            if provider == 'anthropic':
                # Use LangChain for Claude models
                from langchain_anthropic import ChatAnthropic
                from langchain.schema import HumanMessage
                
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    logger.error("[DEBUG] ANTHROPIC_API_KEY not found, falling back to OpenAI")
                    # Fallback to OpenAI if no Anthropic key
                    provider = 'openai'
                else:
                    logger.info(f"[DEBUG] Using Anthropic API for Claude model: {model}")
                    client = ChatAnthropic(
                        model=model,
                        anthropic_api_key=api_key,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    api_start = time.time()
                    response = client.invoke([HumanMessage(content=prompt)])
                    api_end = time.time()
                    
                    result = response.content.strip() if hasattr(response, 'content') else str(response)
                    logger.info(f"[DEBUG] Anthropic API call took {api_end - api_start:.2f} seconds")
                    logger.info(f"[DEBUG] Response length: {len(result)} chars")
            
            if provider == 'google':
                # Use LangChain for Google models
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain.schema import HumanMessage
                
                api_key = os.getenv('GOOGLE_API_KEY')
                if not api_key:
                    logger.error("[DEBUG] GOOGLE_API_KEY not found, falling back to OpenAI")
                    provider = 'openai'
                else:
                    logger.info(f"[DEBUG] Using Google API for Gemini model: {model}")
                    client = ChatGoogleGenerativeAI(
                        model=model,
                        google_api_key=api_key,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    api_start = time.time()
                    response = client.invoke([HumanMessage(content=prompt)])
                    api_end = time.time()
                    
                    result = response.content.strip() if hasattr(response, 'content') else str(response)
                    logger.info(f"[DEBUG] Google API call took {api_end - api_start:.2f} seconds")
                    logger.info(f"[DEBUG] Response length: {len(result)} chars")
            
            if provider == 'openai':
                # Use OpenAI
                openai_api_key = os.getenv('OPENAI_API_KEY')
                if not openai_api_key:
                    raise ValueError("OpenAI API key not found")
                
                logger.info(f"[DEBUG] Using OpenAI API for model: {model}")
                client = OpenAI(
                    api_key=openai_api_key,
                    timeout=httpx.Timeout(90.0, connect=10.0)
                )
                
                api_start = time.time()
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                api_end = time.time()
                
                result = response.choices[0].message.content.strip()
                logger.info(f"[DEBUG] OpenAI API call took {api_end - api_start:.2f} seconds")
                logger.info(f"[DEBUG] Response length: {len(result)} chars")
            
            # Ensure we have a result
            if result is None:
                raise ValueError(f"Failed to generate completion - no result from provider {provider}")
            
            # Cache the result
            self._save_to_cache(cache_key, result)
            
            total_time = time.time() - start_time
            
            # Final summary
            logger.info(f"[DEBUG] ========== COMPLETION SUMMARY ==========")
            logger.info(f"[DEBUG] Model used: {model}")
            logger.info(f"[DEBUG] Input size: {len(prompt)} chars (~{len(prompt)/4:.0f} tokens)")
            logger.info(f"[DEBUG] Max output tokens: {max_tokens}")
            logger.info(f"[DEBUG] Output size: {len(result)} chars")
            logger.info(f"[DEBUG] Total time: {total_time:.2f} seconds")
            logger.info(f"[DEBUG] Speed: {len(prompt)/total_time:.0f} chars/sec processed")
            logger.info(f"[DEBUG] ========================================")
            
            return result
            
        except Exception as e:
            print(f"Error generating completion: {e}")
            # Return a simple fallback
            return "I apologize, but I'm unable to generate a response at this time. Please try again later."
    
    def suggest_article_tags(self, article_text: str, author: str, max_tags: int = 10) -> List[str]:
        """
        Suggest tags for a Substack article using LLM
        
        Args:
            article_text: The article content (title, subtitle, preview, and body)
            author: The article author name
            max_tags: Maximum number of tags to generate (default 10)
            
        Returns:
            List of suggested tags
        """
        # Handle empty or very short text
        if not article_text or len(article_text.strip()) < 50:
            print(f"DEBUG: Using fallback - Article text too short for tag generation (length: {len(article_text.strip())})")
            return self._fallback_tag_extraction(article_text)
        
        # Get model configuration
        model_config = self.llm_config['models']['tag_suggestion']
        model_name = model_config['model']
        provider = model_config.get('provider', 'openai')
        
        # Build prompt optimized for articles
        system_prompt = """You are an expert content tagger for long-form articles and essays. 
        Generate specific, descriptive tags that capture:
        1. Main topics and themes
        2. Key concepts, technologies, or methodologies mentioned
        3. Arguments or positions taken
        4. Type of content (tutorial, opinion, analysis, guide, etc.)
        5. Industry or domain relevance
        
        CRITICAL Guidelines:
        - Create specific tags like "transformer-architecture" not just "AI"
        - Include both broad and specific tags
        - Use hyphens for multi-word tags
        - PRESERVE NATURAL CAPITALIZATION - This is very important!
          * Acronyms should be UPPERCASE: "RLHF", "LLMs", "SOTA", "GPU", "API"
          * Model names preserve their style: "GPT-4", "Qwen-2.5", "LLaMA-3.1", "Gemma-2"
          * Company/product names: "OpenAI", "DeepMind", "ChatGPT", "GitHub"
          * Technical terms: keep standard casing
        - Focus on searchable, meaningful tags
        - Capture the essence of the article's contribution"""
        
        user_prompt = f"""Article by {author}:

{article_text[:8000]}

Generate {max_tags} specific tags for this article. Return as a JSON array.
IMPORTANT: Preserve natural capitalization for all tags!
Example with proper capitalization: ["machine-learning-ethics", "GPT-4-applications", "prompt-engineering", "RLHF", "OpenAI", "LLMs", "Qwen-2.5", "SOTA", "API-design"]"""
        
        # Check cache
        cache_key = self._get_cache_key(user_prompt, model_name)
        cached = self._get_from_cache(cache_key)
        if cached:
            if "__api_success__" in cached:
                return cached
        
        try:
            # Create client for the provider
            client = self._get_client(model_config)
            
            if provider == 'openai':
                # Use OpenAI client
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=model_config.get('temperature', 0.3),
                    max_tokens=model_config.get('max_tokens', 500)
                )
                content = response.choices[0].message.content
            else:
                # Use LangChain for other providers
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                response = client.invoke(messages)
                content = response.content
            
            # Parse response
            try:
                # Extract JSON from response if wrapped in text
                import re
                json_match = re.search(r'\[.*?\]', content, re.DOTALL)
                if json_match:
                    tags = json.loads(json_match.group())
                else:
                    tags = json.loads(content)
                
                # Clean up tags but preserve capitalization for certain terms
                cleaned_tags = []
                for tag in tags:
                    if tag:
                        # Just replace spaces with hyphens, preserve capitalization
                        tag = str(tag).strip().replace(' ', '-')
                        cleaned_tags.append(tag)
                
                tags = cleaned_tags[:max_tags]  # Limit to requested number
                
            except json.JSONDecodeError:
                # Fallback: extract words that look like tags
                tags = re.findall(r'["\']([\w-]+)["\']', content)
                tags = tags[:max_tags]
            
            # Cache the result
            self._save_to_cache(cache_key, tags)
            
            # Mark that we successfully used the API
            if tags:
                tags.append("__api_success__")  # Internal marker
            
            return tags
            
        except Exception as e:
            print(f"Error generating article tags with LLM: {e}")
            # Use spaCy fallback for articles
            return self._fallback_tag_extraction(article_text)
    
    def generate_tags_from_prompt(self, text: str, author: str = "", prompt_key: str = 'paper_tag_suggestion', max_tags: int = 30) -> List[str]:
        """
        Generate tags for papers using specific prompts from prompts_config.json
        
        Args:
            text: The paper text (title + abstract + content)
            author: The paper author(s)
            prompt_key: Key in prompts_config.json to use for prompts
            max_tags: Maximum number of tags to generate
            
        Returns:
            List of suggested tags
        """
        try:
            # Get prompt configuration
            if prompt_key not in self.prompts:
                logger.error(f"Prompt key '{prompt_key}' not found in prompts_config.json")
                return []
            
            prompt_config = self.prompts[prompt_key]
            
            # Get model configuration - use tag_suggestion model
            model_config = self.llm_config['models'].get('tag_suggestion', {})
            if not model_config:
                logger.error("No tag_suggestion model configured in llm.json")
                return []
            
            # Get the LLM client
            client = self._get_client(model_config)
            
            # Build the prompts
            system_prompt = prompt_config.get('system', '')
            user_template = prompt_config.get('user_template', '')
            
            # Replace template variables
            user_prompt = user_template.replace('{author}', author or 'Unknown')
            user_prompt = user_prompt.replace('{text}', text)
            user_prompt = user_prompt.replace('{max_tags}', str(max_tags))
            
            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # Call the LLM
            response = client.invoke(messages)
            response_text = response.content
            
            # Parse response based on output format
            output_format = prompt_config.get('output_format', 'json_array')
            
            if output_format == 'json_array':
                # Extract JSON array from response
                import json
                import re
                
                # Try to find JSON array in the response
                json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                if json_match:
                    tags = json.loads(json_match.group())
                else:
                    # Try to parse the entire response as JSON
                    tags = json.loads(response_text)
                
                # Ensure we have a list of strings
                if isinstance(tags, list):
                    tags = [str(tag) for tag in tags]
                else:
                    logger.warning("LLM did not return a list of tags")
                    tags = []
            else:
                # Handle other formats if needed
                tags = []
            
            logger.info(f"Generated {len(tags)} tags using {model_config.get('model')} for paper")
            return tags[:max_tags]  # Limit to max_tags
            
        except Exception as e:
            logger.error(f"Error generating paper tags with LLM: {e}")
            return []
    
    def generate_tags_with_full_context(self, text: str, author: str = "", prompt_key: str = 'paper_tag_suggestion', 
                                       model_key: str = 'paper_tag_suggestion_deep', max_tags: int = 30) -> List[str]:
        """
        Generate tags for papers using FULL context with high-context models
        
        Args:
            text: The FULL paper text (title + abstract + complete content)
            author: The paper author(s)
            prompt_key: Key in prompts_config.json to use for prompts
            model_key: Specific model to use (e.g., paper_tag_suggestion_deep for Gemini 2.5 Pro)
            max_tags: Maximum number of tags to generate
            
        Returns:
            List of suggested tags
        """
        try:
            # Get prompt configuration
            if prompt_key not in self.prompts:
                logger.error(f"Prompt key '{prompt_key}' not found in prompts_config.json")
                return self.generate_tags_from_prompt(text, author, prompt_key, max_tags)  # Fallback
            
            prompt_config = self.prompts[prompt_key]
            
            # Get model configuration - use specified high-context model
            model_config = self.llm_config['models'].get(model_key)
            if not model_config:
                logger.warning(f"Model '{model_key}' not found, falling back to regular tag suggestion")
                return self.generate_tags_from_prompt(text, author, prompt_key, max_tags)  # Fallback
            
            logger.info(f"Using {model_config.get('model')} ({model_config.get('provider')}) for full-context tag generation")
            logger.info(f"Paper size: {len(text)} characters")
            
            # Get the LLM client
            client = self._get_client(model_config)
            
            # Build the prompts
            system_prompt = prompt_config.get('system', '')
            user_template = prompt_config.get('user_template', '')
            
            # Replace template variables
            user_prompt = user_template.replace('{author}', author or 'Unknown')
            user_prompt = user_prompt.replace('{text}', text)
            user_prompt = user_prompt.replace('{max_tags}', str(max_tags))
            
            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # Call the LLM with full context
            response = client.invoke(messages)
            response_text = response.content
            
            # Parse response based on output format
            output_format = prompt_config.get('output_format', 'json_array')
            
            if output_format == 'json_array':
                # Extract JSON array from response
                import json
                import re
                
                # Try to find JSON array in the response
                json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                if json_match:
                    tags = json.loads(json_match.group())
                else:
                    # Try to parse the entire response as JSON
                    tags = json.loads(response_text)
                
                # Ensure we have a list of strings
                if isinstance(tags, list):
                    tags = [str(tag) for tag in tags]
                else:
                    logger.warning("LLM did not return a list of tags")
                    tags = []
            else:
                # Handle other formats if needed
                tags = []
            
            logger.info(f"Generated {len(tags)} tags using {model_config.get('model')} with full paper context")
            return tags[:max_tags]  # Limit to max_tags
            
        except Exception as e:
            logger.error(f"Error generating full-context paper tags with {model_key}: {e}")
            
            # If GPT-5 failed, try Gemini 2.5 Pro as fallback
            if model_key == 'paper_tag_suggestion_gpt5':
                logger.info("Falling back to Gemini 2.5 Pro (paper_tag_suggestion_deep)")
                try:
                    return self.generate_tags_with_full_context(
                        text=text,
                        author=author,
                        prompt_key=prompt_key,
                        model_key='paper_tag_suggestion_deep',  # Fallback to Gemini
                        max_tags=max_tags
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback to Gemini also failed: {fallback_error}")
            
            # Final fallback to regular method
            logger.warning("All high-context models failed, falling back to regular tag generation")
            return self.generate_tags_from_prompt(text, author, prompt_key, max_tags)
    
    def extract_paper_authors(self, header_text: str) -> Optional[str]:
        """
        Extract author information from paper header using LLM
        
        Args:
            header_text: The header section of the paper (between title and abstract)
            
        Returns:
            JSON string with extracted author information or None if extraction fails
        """
        try:
            # Get model configuration for author extraction
            model_config = self.llm_config['models'].get('paper_author_extraction')
            if not model_config:
                print("Warning: No paper_author_extraction model configured, using entity_extraction")
                model_config = self.llm_config['models'].get('entity_extraction')
            
            # Get prompt configuration
            prompt_config = self.prompts.get('paper_author_extraction')
            if not prompt_config:
                print("Error: No paper_author_extraction prompt configured")
                return None
            
            # Prepare the messages
            system_prompt = prompt_config['system']
            user_prompt = prompt_config['user_template'].format(header_text=header_text)
            
            # Get the appropriate LangChain client
            client = self._get_client(model_config)
            
            if client is None:
                print("Error: Could not get LLM client")
                return None
            
            # Call using LangChain
            try:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                
                response = client.invoke(messages)
                
                if hasattr(response, 'content'):
                    result = response.content
                else:
                    result = str(response)
                
                print(f"Successfully extracted authors from paper header")
                return result
                
            except Exception as e:
                print(f"Error calling LLM with LangChain: {e}")
                # Fallback to direct API call if available
                if hasattr(self, '_call_llm_with_provider'):
                    response = self._call_llm_with_provider(
                        model_config=model_config,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt
                    )
                    if response:
                        return response
                return None
                
        except Exception as e:
            print(f"Error extracting paper authors: {e}")
            return None
    
    def format_academic_text(self, text: str, section_type: str = 'general') -> str:
        """
        Format academic text using LLM to clean and improve readability
        
        Args:
            text: Raw text to format
            section_type: Type of section (conclusion, abstract, etc.)
            
        Returns:
            Formatted markdown text
        """
        try:
            # Check for empty text
            if not text or len(text.strip()) < 10:
                return text
            
            # Get prompt configuration
            prompt_config = self.prompts.get('academic_text_formatting')
            if not prompt_config:
                print("Academic text formatting prompt not found, returning raw text")
                return text
            
            # Build prompt
            system_prompt = prompt_config['system']
            user_prompt = prompt_config['user_template'].format(
                section_type=section_type,
                text=text
            )
            
            # Get model configuration - use a fast model for text formatting
            model_config = self.llm_config['models'].get('content_classification', 
                                                         self.llm_config['models']['tag_suggestion'])
            
            # Check cache
            cache_key = self._get_cache_key(user_prompt, model_config['model'])
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
            
            try:
                # Get the appropriate client
                client = self._get_client(model_config)
                
                # Check if this is a reasoning model
                is_reasoning = model_config.get('is_reasoning', False)
                
                # Use LangChain for all providers
                if hasattr(client, 'invoke'):
                    if is_reasoning:
                        # Reasoning models: combine system and user prompts
                        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
                        messages = [HumanMessage(content=combined_prompt)]
                    else:
                        # Standard models with system message
                        messages = [
                            SystemMessage(content=system_prompt),
                            HumanMessage(content=user_prompt)
                        ]
                    
                    response = client.invoke(messages)
                    
                    if hasattr(response, 'content'):
                        formatted_text = response.content
                    else:
                        formatted_text = str(response)
                    
                    # Clean up the response
                    formatted_text = formatted_text.strip()
                    
                    # Cache the result
                    self._save_to_cache(cache_key, formatted_text)
                    
                    print(f"Successfully formatted {section_type} text")
                    return formatted_text
                else:
                    # Legacy OpenAI client fallback
                    if is_reasoning:
                        messages = [{"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}]
                    else:
                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    
                    response = self.client.chat.completions.create(
                        model=model_config['model'],
                        messages=messages,
                        temperature=model_config.get('temperature', 0.3),
                        max_tokens=model_config.get('max_tokens', 2000)
                    )
                    
                    formatted_text = response.choices[0].message.content.strip()
                    
                    # Cache the result
                    self._save_to_cache(cache_key, formatted_text)
                    
                    return formatted_text
                    
            except Exception as e:
                print(f"Error formatting text with LLM: {e}")
                # Return cleaned raw text as fallback
                return self._basic_text_cleanup(text)
                
        except Exception as e:
            print(f"Error in format_academic_text: {e}")
            return text
    
    def _basic_text_cleanup(self, text: str) -> str:
        """
        Basic text cleanup without LLM
        """
        import re
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix sentence spacing
        text = re.sub(r'\.([A-Z])', r'. \1', text)
        
        # Break into paragraphs at reasonable points
        sentences = text.split('. ')
        paragraphs = []
        current_para = []
        
        for i, sentence in enumerate(sentences):
            current_para.append(sentence)
            # Create paragraph every 3-4 sentences
            if len(current_para) >= 3 and i < len(sentences) - 1:
                paragraphs.append('. '.join(current_para) + '.')
                current_para = []
        
        if current_para:
            paragraphs.append('. '.join(current_para))
            if not paragraphs[-1].endswith('.'):
                paragraphs[-1] += '.'
        
        return '\n\n'.join(paragraphs)

# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create the singleton LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service