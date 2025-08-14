"""
Article Summarization Service using LLMs
"""
import os
import json
from typing import Dict, List, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

from app.models import get_db
from app.models.substack import SubstackArticle

class ArticleSummarizer:
    """Service for generating article summaries using LLMs"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.prompts = self._load_prompts()
        self.model_name = None  # Store the model name for attribution
    
    def _initialize_llm(self):
        """Initialize LLM based on configuration"""
        config_path = Path(__file__).parent.parent.parent / 'llm.json'  # Go up to backend folder
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Get configuration from models section
                summarizer_config = config.get('models', {}).get('article_summarizer', {})
        else:
            summarizer_config = {}
        
        provider = summarizer_config.get('provider', 'anthropic')
        model = summarizer_config.get('model', 'claude-3-5-sonnet-20241022')
        temperature = summarizer_config.get('temperature', 0.3)
        max_tokens = summarizer_config.get('max_tokens', 1500)
        
        if provider == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            self.model_name = model  # Store model name
            return ChatAnthropic(
                model=model,
                anthropic_api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
        elif provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            self.model_name = model  # Store model name
            return ChatOpenAI(
                model=model,
                openai_api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
        elif provider == 'google':
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment")
            self.model_name = model  # Store model name
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=temperature,
                max_tokens_to_sample=max_tokens
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _load_prompts(self) -> Dict:
        """Load prompts from configuration"""
        prompts_path = Path(__file__).parent.parent.parent / 'prompts_config.json'  # Go up to backend folder
        if prompts_path.exists():
            with open(prompts_path, 'r') as f:
                all_prompts = json.load(f)
                return all_prompts.get('article_summarization', {})
        
        # Return empty dict if file doesn't exist - prompts should be in config
        return {}
    
    def summarize_article(self, article_id: int, db: Session) -> Dict:
        """Generate summary for an article"""
        article = db.query(SubstackArticle).filter(
            SubstackArticle.id == article_id
        ).first()
        
        if not article:
            raise ValueError(f"Article {article_id} not found")
        
        # If already summarized, return existing summary
        if article.summary and article.summarized:
            return {
                "summary": article.summary,
                "key_points": article.key_points or [],
                "model_used": self.model_name  # Include model attribution
            }
        
        # Prepare content (limit to reasonable length)
        content = article.content_markdown or article.preview or ""
        
        # Check if content is empty or too short
        if not content or len(content.strip()) < 50:
            raise ValueError(f"Article {article_id} has insufficient content for summarization")
        
        if len(content) > 15000:
            content = content[:15000] + "..."
        
        # Generate summary
        try:
            # Get prompts from config - no fallbacks allowed
            system_prompt = self.prompts.get('system')
            summary_template = self.prompts.get('summary_prompt')
            
            # Ensure prompts are loaded from config
            if not system_prompt or not summary_template:
                raise ValueError("article_summarization prompts not configured in prompts_config.json")
            
            # Format the prompt
            summary_prompt = summary_template.format(
                title=article.title or "Untitled",
                author=article.author.name if article.author else "Unknown",
                content=content
            )
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=summary_prompt)
            ]
            
            response = self.llm.invoke(messages)
            summary_text = response.content
            
            # Extract key points
            key_points = self._extract_key_points(content)
            
            # Save to database
            article.summary = summary_text
            article.key_points = key_points
            article.summarized = True
            db.commit()
            
            return {
                "summary": summary_text,
                "key_points": key_points,
                "model_used": self.model_name  # Include model attribution
            }
            
        except Exception as e:
            print(f"Error summarizing article: {e}")
            raise
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content"""
        try:
            key_points_prompt = self.prompts.get('key_points_prompt')
            system_prompt = self.prompts.get('key_points_system', self.prompts.get('system'))
            
            if not key_points_prompt or not system_prompt:
                raise ValueError("key_points prompts not configured in prompts_config.json")
            
            prompt = key_points_prompt.format(
                content=content[:8000]  # Limit content length
            )
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse bullet points from response
            lines = response.content.split('\n')
            key_points = []
            for line in lines:
                line = line.strip()
                if line and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                    # Remove bullet character and clean
                    point = line.lstrip('•-* ').strip()
                    if point:
                        key_points.append(point)
            
            return key_points[:7]  # Limit to 7 points
            
        except Exception as e:
            print(f"Error extracting key points: {e}")
            return []
    
    def batch_summarize(self, db: Session, limit: int = 10) -> int:
        """Summarize multiple unsummarized articles"""
        articles = db.query(SubstackArticle).filter(
            SubstackArticle.summarized == False,
            SubstackArticle.deleted == False
        ).limit(limit).all()
        
        summarized_count = 0
        for article in articles:
            try:
                print(f"Summarizing: {article.title[:60]}...")
                self.summarize_article(article.id, db)
                summarized_count += 1
            except Exception as e:
                print(f"Failed to summarize article {article.id}: {e}")
                continue
        
        return summarized_count