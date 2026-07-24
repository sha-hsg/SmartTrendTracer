"""
Article Summarization Service using LLM Manager
Migrated to use unified LLM Manager with LiteLLM
"""
import os
import json
from typing import Dict, List, Optional
from pathlib import Path

from app.services.llm_manager import get_llm_manager


class ArticleSummarizer:
    """Service for generating article summaries using LLM Manager"""

    def __init__(self, user_id: str = "default"):
        """
        Initialize ArticleSummarizer

        Args:
            user_id: User ID for preference lookup (default: "default")
        """
        self.llm_manager = get_llm_manager()
        self.user_id = user_id
        self.task_type = 'article_summarizer'  # Task type from litellm_config.yaml
        self.prompts = self._load_prompts()

        # Get task info for model attribution
        task_info = self.llm_manager.get_task_info(self.task_type)
        self.model_name = task_info['model'] if task_info else 'unknown'

    def _load_prompts(self) -> Dict:
        """Load prompts from configuration"""
        prompts_path = Path(__file__).parent.parent.parent / 'prompts_config.json'
        if prompts_path.exists():
            with open(prompts_path, 'r') as f:
                all_prompts = json.load(f)
                return all_prompts.get('article_summarization', {})

        return {}

    def summarize_article_content(
        self,
        content: str,
        title: str = "Untitled",
        author: str = "Unknown",
        model: str | None = None,
    ) -> Dict:
        """
        Generate summary for article content directly (MongoDB-compatible).
        This method works with content directly without database dependencies.

        Args:
            content: The article content (markdown or text)
            title: Article title
            author: Article author name

        Returns:
            Dict with summary, key_points, and model_used
        """
        # Check if content is empty or too short
        if not content or len(content.strip()) < 50:
            raise ValueError(f"Content has insufficient length for summarization")

        # Limit content to reasonable length
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
                title=title,
                author=author,
                content=content
            )

            # Call LLM Manager with OpenAI message format
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": summary_prompt}
            ]

            response = self.llm_manager.completion_sync(
                task_type=self.task_type,
                messages=messages,
                user_id=self.user_id,
                override_params={'model': model} if model else None,
            )

            summary_text = response.choices[0].message.content

            # Extract key points
            key_points = self._extract_key_points(content)

            # Get actual model used from response
            model_used = response.model if hasattr(response, 'model') else self.model_name

            return {
                "summary": summary_text,
                "key_points": key_points,
                "model_used": model_used
            }

        except Exception as e:
            print(f"Error summarizing content: {e}")
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

            # Call LLM Manager
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            response = self.llm_manager.completion_sync(
                task_type=self.task_type,
                messages=messages,
                user_id=self.user_id
            )

            # Parse bullet points from response
            lines = response.choices[0].message.content.split('\n')
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

    def set_user_preference(self, model_name: str):
        """
        Set user's preferred model for article summarization

        Args:
            model_name: Model name from litellm_config.yaml
        """
        self.llm_manager.set_user_preference(
            task_type=self.task_type,
            model_name=model_name,
            user_id=self.user_id
        )

    def get_available_models(self) -> List[Dict]:
        """Get list of available models for summarization"""
        all_models = self.llm_manager.get_available_models()
        return all_models.get(self.task_type, [])
