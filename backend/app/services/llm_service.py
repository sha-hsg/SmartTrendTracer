"""
LLM Service for tag suggestions and content analysis
Uses configuration from llm.json and prompts_config.json
Supports multiple providers: OpenAI, Anthropic, Google
"""
import json
import os
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
        
        # Keep OpenAI client for backward compatibility
        openai_key = os.getenv(self.llm_config['api_settings']['api_key_env'])
        if openai_key:
            self.client = OpenAI(api_key=openai_key)
        
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
                    max_tokens_to_sample=model_config.get('max_tokens', 1000)
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
    
    def generate_completion(self, prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.3, max_tokens: int = 1000) -> str:
        """Generate a completion using the LLM"""
        try:
            # Check cache first
            cache_key = self._get_cache_key(prompt, model)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
            
            # Get API key from environment
            openai_api_key = os.getenv(self.llm_config['api_settings']['api_key_env'])
            
            # Create client based on model
            if "gpt" in model.lower() or "o1" in model.lower():
                # Use OpenAI
                if not openai_api_key:
                    raise ValueError("OpenAI API key not found")
                
                client = OpenAI(api_key=openai_api_key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                result = response.choices[0].message.content.strip()
            elif "claude" in model.lower():
                # For Claude models, we need to use a different approach
                # For now, fallback to GPT-4o-mini as we don't have Anthropic client setup in this method
                if not openai_api_key:
                    raise ValueError("OpenAI API key not found")
                
                # Use GPT-4o-mini as fallback for Claude requests
                client = OpenAI(api_key=openai_api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                result = response.choices[0].message.content.strip()
            else:
                # Default to GPT-4o-mini for unknown models
                if not openai_api_key:
                    raise ValueError("OpenAI API key not found")
                
                client = OpenAI(api_key=openai_api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                result = response.choices[0].message.content.strip()
            
            # Cache the result
            self._save_to_cache(cache_key, result)
            
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
        
        Guidelines:
        - Create specific tags like "transformer-architecture" not just "AI"
        - Include both broad and specific tags
        - Use lowercase with hyphens for multi-word tags
        - Focus on searchable, meaningful tags
        - Capture the essence of the article's contribution"""
        
        user_prompt = f"""Article by {author}:

{article_text[:8000]}

Generate {max_tags} specific tags for this article. Return as a JSON array.
Example: ["machine-learning-ethics", "gpt-4-applications", "prompt-engineering", ...]"""
        
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

# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create the singleton LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service