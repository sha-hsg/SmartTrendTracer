"""
LangChain-based LLM Service with Gemini support using configuration files
"""
import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser


class LangChainLLMService:
    """LLM Service using LangChain with support for multiple models including Gemini"""
    
    def __init__(self):
        # Load configurations
        self.load_configs()
        
        # Get API keys from environment
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Initialize models based on llm.json configuration
        self.models = {}
        self.setup_models()
    
    def load_configs(self):
        """Load configuration from llm.json and prompts_config.json"""
        config_dir = Path(__file__).parent.parent.parent  # backend directory
        
        # Load LLM configuration
        llm_config_path = config_dir / "llm.json"
        if llm_config_path.exists():
            with open(llm_config_path, 'r') as f:
                self.llm_config = json.load(f)
        else:
            self.llm_config = {"models": {}}
        
        # Load prompts configuration
        prompts_config_path = config_dir / "prompts_config.json"
        if prompts_config_path.exists():
            with open(prompts_config_path, 'r') as f:
                self.prompts_config = json.load(f)
        else:
            self.prompts_config = {}
    
    def setup_models(self):
        """Set up models based on configuration"""
        # Set up Google models if API key is available
        if self.google_api_key:
            # Set up Gemini 2.5 Pro for tag reorganization (from llm.json)
            if "tag_reorganization_full" in self.llm_config.get("models", {}):
                config = self.llm_config["models"]["tag_reorganization_full"]
                if config["provider"] == "google":
                    self.models["gemini-2.5-pro"] = ChatGoogleGenerativeAI(
                        model="gemini-2.5-pro",  # Use the correct model name
                        google_api_key=self.google_api_key,
                        temperature=config.get("temperature", 0.2),
                        max_tokens=config.get("max_tokens", 50000),
                        convert_system_message_to_human=True
                    )
            
            # Set up other Gemini models from config
            for model_key, model_config in self.llm_config.get("models", {}).items():
                if model_config.get("provider") == "google" and model_key != "tag_reorganization_full":
                    model_name = model_config.get("model")
                    if model_name and model_name not in self.models:
                        self.models[model_name] = ChatGoogleGenerativeAI(
                            model=model_name,
                            google_api_key=self.google_api_key,
                            temperature=model_config.get("temperature", 0.3),
                            max_tokens=model_config.get("max_tokens", 8192),
                            convert_system_message_to_human=True
                        )
        
        # Set up OpenAI models from config if API key is available
        if self.openai_api_key:
            for model_key, model_config in self.llm_config.get("models", {}).items():
                if model_config.get("provider") == "openai":
                    model_name = model_config.get("model")
                    if model_name and model_name not in self.models:
                        self.models[model_name] = ChatOpenAI(
                            model=model_name,
                            openai_api_key=self.openai_api_key,
                            temperature=model_config.get("temperature", 0.3),
                            max_tokens=model_config.get("max_tokens", 4000)
                        )
        
        # Set up Anthropic models from config if API key is available
        if self.anthropic_api_key:
            for model_key, model_config in self.llm_config.get("models", {}).items():
                if model_config.get("provider") == "anthropic":
                    model_name = model_config.get("model")
                    if model_name and model_name not in self.models:
                        self.models[model_name] = ChatAnthropic(
                            model=model_name,
                            anthropic_api_key=self.anthropic_api_key,
                            temperature=model_config.get("temperature", 0.3),
                            max_tokens=model_config.get("max_tokens", 4000)
                        )
    
    def generate_completion(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.3,
        max_tokens: int = 8192,
        system_prompt: Optional[str] = None,
        response_format: Optional[str] = None
    ) -> str:
        """
        Generate a completion using the specified model
        
        Args:
            prompt: The user prompt
            model: Model to use (gemini-2.0-flash-exp, gemini-1.5-pro, gpt-4o-mini, etc.)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            response_format: Optional response format (e.g., "json")
        
        Returns:
            Generated text response
        """
        # Select model
        if model not in self.models:
            # Fall back to available model
            if self.google_api_key and "gemini-2.0-flash-exp" in self.models:
                model = "gemini-2.0-flash-exp"
            elif self.openai_api_key and "gpt-4o-mini" in self.models:
                model = "gpt-4o-mini"
            else:
                raise ValueError(f"No available models. Please set GOOGLE_API_KEY or OPENAI_API_KEY")
        
        llm = self.models[model]
        
        # Update temperature and max_tokens if different from defaults
        if hasattr(llm, 'temperature'):
            llm.temperature = temperature
        if hasattr(llm, 'max_tokens'):
            llm.max_tokens = max_tokens
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        # Select parser based on response format
        if response_format == "json":
            parser = JsonOutputParser()
            # Add JSON instruction to prompt if using Gemini
            if "gemini" in model.lower():
                messages[-1].content += "\n\nPlease respond with valid JSON only, no markdown formatting or code blocks."
        else:
            parser = StrOutputParser()
        
        # Create chain and invoke
        chain = llm | parser
        
        try:
            response = chain.invoke(messages)
            
            # If JSON format requested but got string, try to parse it
            if response_format == "json" and isinstance(response, str):
                # Try to extract JSON from the response if it's wrapped in markdown
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
                # Try to parse
                try:
                    response = json.loads(response)
                except json.JSONDecodeError:
                    # If parsing fails, return the string
                    pass
            
            # Convert dict/list to JSON string if needed
            if response_format == "json" and not isinstance(response, str):
                response = json.dumps(response)
            
            return response
            
        except Exception as e:
            print(f"Error generating completion with {model}: {e}")
            raise
    
    def generate_tag_reorganization(
        self,
        tags_context: Dict[str, Any],
        use_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive tag reorganization using configuration
        
        Args:
            tags_context: Dictionary containing all tags and their context
            use_model: Model to use (default from llm.json)
        
        Returns:
            Reorganization proposal as a dictionary
        """
        # Get model from config if not specified
        if use_model is None:
            model_config = self.llm_config.get("models", {}).get("tag_reorganization_full", {})
            use_model = model_config.get("model", "gemini-2.5-pro")
        
        # Get prompts from configuration
        tag_reorg_config = self.prompts_config.get("tag_reorganization", {})
        if not tag_reorg_config:
            raise ValueError("tag_reorganization prompts not found in prompts_config.json")
        system_prompt = tag_reorg_config.get("system")
        if not system_prompt:
            raise ValueError("tag_reorganization.system prompt not configured in prompts_config.json")
        
        # Format the user prompt template
        user_template = tag_reorg_config.get("user_template", "")
        # Format average usage separately
        avg_usage = tags_context['statistics']['average_usage']
        avg_usage_str = f"{avg_usage:.1f}" if isinstance(avg_usage, (int, float)) else str(avg_usage)
        
        prompt = user_template.format(
            total_tags=tags_context['statistics']['total_tags'],
            tags_json=json.dumps(tags_context['tags'], indent=2),
            total_taggings=tags_context['statistics']['total_taggings'],
            average_usage=avg_usage_str
        )

        # Get max_tokens from config
        model_config = self.llm_config.get("models", {}).get("tag_reorganization_full", {})
        max_tokens = model_config.get("max_tokens", 50000)
        
        try:
            print(f"Starting tag reorganization with {use_model}, max_tokens={max_tokens}")
            print(f"Processing {tags_context['statistics']['total_tags']} tags...")
            
            response = self.generate_completion(
                prompt=prompt,
                model=use_model,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=max_tokens,  # Use configured max tokens
                response_format="json"
            )
            
            # Parse response if it's a string
            if isinstance(response, str):
                return json.loads(response)
            return response
            
        except Exception as e:
            print(f"Error generating reorganization: {e}")
            # Return a minimal valid structure on error
            return {
                "hierarchy": {},
                "root_categories": [],
                "deprecated_tags": [],
                "merge_proposals": [],
                "new_categories_suggested": [],
                "confidence_score": 0.0,
                "reasoning": f"Error occurred: {str(e)}"
            }
    
    def summarize_tweets(
        self,
        tweet_context: Dict[str, Any],
        use_model: Optional[str] = None
    ) -> str:
        """
        Generate a comprehensive summary of tweet collections focusing on content
        
        Args:
            tweet_context: Dictionary containing tweets and metadata
            use_model: Model to use (default from llm.json)
        
        Returns:
            Content summary as a string
        """
        # Get model from config if not specified
        if use_model is None:
            model_config = self.llm_config.get("models", {}).get("summarization", {})
            use_model = model_config.get("model", "gpt-4o-mini")
            
        # Get the appropriate prompt configuration
        # Use ai_expert_summary for AI/ML content, otherwise use general summarization
        tweets = tweet_context.get("tweets", [])
        
        # Format tweets for the prompt
        tweet_texts = []
        for tweet in tweets[:50]:  # Limit to 50 tweets for context
            tweet_text = f"@{tweet['author']}: {tweet['text']}"
            if tweet.get('likes', 0) > 100 or tweet.get('retweets', 0) > 50:
                # Add engagement info for highly engaged tweets
                tweet_text += f" [🔥 {tweet['likes']} likes, {tweet['retweets']} retweets]"
            tweet_texts.append(tweet_text)
        
        tweets_formatted = "\n\n".join(tweet_texts)
        
        # Check if tweets are AI/ML related
        ai_keywords = ['ai', 'ml', 'gpt', 'llm', 'model', 'neural', 'deep learning', 
                      'machine learning', 'artificial intelligence', 'transformer',
                      'openai', 'anthropic', 'google', 'gemini', 'claude']
        
        tweets_text_lower = tweets_formatted.lower()
        is_ai_content = any(keyword in tweets_text_lower for keyword in ai_keywords)
        
        # Select appropriate prompt based on content
        if is_ai_content:
            prompt_config = self.prompts_config.get("ai_expert_summary", {})
        else:
            prompt_config = self.prompts_config.get("summarization_system", {})
        
        system_prompt = prompt_config.get("system", "You are a helpful assistant that summarizes tweets.")
        user_template = prompt_config.get("user_template", "Summarize these tweets:\n{tweets}")
        
        # Format the user prompt
        user_prompt = user_template.replace("{tweets}", tweets_formatted)
        
        # Add context about the collection
        period = tweet_context.get("period", "recent")
        total_count = tweet_context.get("total_count", len(tweets))
        
        context_info = f"\n\n[Context: {total_count} tweets from {period} period]"
        user_prompt += context_info
        
        try:
            # Get max_tokens from config
            model_config = self.llm_config.get("models", {}).get("summarization", {})
            max_tokens = model_config.get("max_tokens", 1000)
            temperature = model_config.get("temperature", 0.3)
            
            print(f"Generating tweet summary with {use_model}...")
            print(f"Processing {len(tweets)} tweets (AI content: {is_ai_content})")
            
            summary = self.generate_completion(
                prompt=user_prompt,
                model=use_model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format="text"
            )
            
            # Ensure we have a valid summary
            if not summary or summary.strip() == "":
                # Fallback: Create a basic thematic summary
                themes = self._extract_basic_themes(tweets)
                summary = f"Collection of {total_count} tweets covering: {', '.join(themes[:5])}. "
                summary += f"Key authors include {', '.join(set(t['author'] for t in tweets[:5]))}."
                
            return summary
            
        except Exception as e:
            print(f"Error generating tweet summary: {e}")
            # Return a basic summary on error
            themes = self._extract_basic_themes(tweets)
            return f"Collection of {total_count} tweets from {period}. Main topics: {', '.join(themes[:3])}."
    
    def _extract_basic_themes(self, tweets: list) -> list:
        """
        Extract basic themes from tweets using simple keyword analysis
        """
        from collections import Counter
        import re
        
        # Common words to exclude
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'been', 'be',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                     'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
                     'i', 'you', 'we', 'they', 'he', 'she', 'it', 'my', 'your', 'our',
                     'their', 'his', 'her', 'its', 'just', 'now', 'here', 'there', 'about',
                     'up', 'out', 'off', 'over', 'into', 'through', 'during', 'before',
                     'after', 'above', 'below', 'between', 'under', 'again', 'further',
                     'then', 'once', 'rt', 'via', 'amp', 'https', 'http', 'com', 'org'}
        
        # Extract words from all tweets
        all_words = []
        for tweet in tweets:
            text = tweet.get('text', '')
            # Remove URLs, mentions, and special characters
            text = re.sub(r'http[s]?://\S+', '', text)
            text = re.sub(r'@\w+', '', text)
            text = re.sub(r'[^a-zA-Z\s]', '', text)
            
            words = text.lower().split()
            # Filter out stop words and short words
            words = [w for w in words if w not in stop_words and len(w) > 3]
            all_words.extend(words)
        
        # Count word frequency
        word_counts = Counter(all_words)
        
        # Get top themes
        themes = []
        for word, count in word_counts.most_common(10):
            if count > 1:  # Only include words that appear multiple times
                themes.append(word.title())
        
        return themes if themes else ['AI Updates', 'Technology', 'Research']


# Singleton instance
_langchain_service = None

def get_langchain_llm_service() -> LangChainLLMService:
    """Get or create the singleton LangChain LLM service instance"""
    global _langchain_service
    if _langchain_service is None:
        _langchain_service = LangChainLLMService()
    return _langchain_service