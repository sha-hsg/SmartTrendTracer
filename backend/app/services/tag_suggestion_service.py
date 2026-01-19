"""
Tag Suggestion Service using LLM Manager
Migrated to use unified LLM Manager with LiteLLM
"""
import json
from typing import List, Dict, Optional
from pathlib import Path

from app.services.llm_manager import get_llm_manager


class TagSuggestionService:
    """Service for generating tag suggestions using LLM Manager"""

    def __init__(self, user_id: str = "default"):
        """
        Initialize TagSuggestionService

        Args:
            user_id: User ID for preference lookup (default: "default")
        """
        self.llm_manager = get_llm_manager()
        self.user_id = user_id
        self.task_type = 'tag_suggestion'
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
                return all_prompts.get('tag_suggestion', {})

        return {}

    def suggest_tags(
        self,
        tweet_text: str,
        author: str = "Unknown",
        max_tags: int = 10
    ) -> List[str]:
        """
        Generate tag suggestions for a tweet

        Args:
            tweet_text: The tweet content
            author: Tweet author username
            max_tags: Maximum number of tags to suggest

        Returns:
            List of suggested tags with special marker for API success
        """
        # Check if content is empty or too short
        if not tweet_text or len(tweet_text.strip()) < 10:
            return []

        # Generate suggestions
        try:
            # Get prompts from config
            system_prompt = self.prompts.get('system')
            tag_template = self.prompts.get('user_template')

            # Ensure prompts are loaded from config
            if not system_prompt or not tag_template:
                raise ValueError("tag_suggestion prompts not configured in prompts_config.json")

            # Format the prompt
            user_prompt = tag_template.format(
                tweet_text=tweet_text,
                author=author,
                max_tags=max_tags
            )

            # Call LLM Manager with OpenAI message format
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = self.llm_manager.completion_sync(
                task_type=self.task_type,
                messages=messages,
                user_id=self.user_id
            )

            suggestion_text = response.choices[0].message.content

            # Parse tags from response (expecting comma-separated or line-separated tags)
            tags = self._parse_tags(suggestion_text)

            # Add success marker for API detection
            tags.append("__api_success__")

            return tags

        except Exception as e:
            print(f"Error suggesting tags: {e}")
            # Return empty list on error (no fallback to maintain consistency)
            return []

    def _parse_tags(self, text: str) -> List[str]:
        """
        Parse tags from LLM response

        Args:
            text: Raw response text from LLM

        Returns:
            List of cleaned tag strings
        """
        tags = []

        # Try to parse as JSON array first
        try:
            import re
            # Look for JSON array in response
            json_match = re.search(r'\[([^\]]+)\]', text)
            if json_match:
                json_text = '[' + json_match.group(1) + ']'
                parsed = json.loads(json_text)
                if isinstance(parsed, list):
                    tags = [str(tag).strip() for tag in parsed if tag]
                    return tags
        except:
            pass

        # Fallback: Parse as comma-separated or newline-separated
        # Split by commas or newlines
        lines = text.replace(',', '\n').split('\n')

        for line in lines:
            line = line.strip()

            # Remove common prefixes
            for prefix in ['- ', '* ', '• ', '1. ', '2. ', '3. ', '4. ', '5. ',
                          '6. ', '7. ', '8. ', '9. ', '10. ']:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()

            # Remove quotes
            line = line.strip('"\'')

            # Skip empty lines and explanatory text
            if line and len(line) > 1 and len(line) < 50:
                # Convert to lowercase and kebab-case
                tag = line.lower().replace(' ', '-')
                if tag:
                    tags.append(tag)

        return tags[:10]  # Limit to 10 tags

    def suggest_tags_with_model_info(
        self,
        tweet_text: str,
        author: str = "Unknown",
        max_tags: int = 10
    ) -> Dict:
        """
        Generate tag suggestions with model attribution

        Args:
            tweet_text: The tweet content
            author: Tweet author username
            max_tags: Maximum number of tags to suggest

        Returns:
            Dict with tags, model_used, and success status
        """
        try:
            tags = self.suggest_tags(tweet_text, author, max_tags)

            # Check if API was successful
            api_success = "__api_success__" in tags
            if api_success:
                tags = [tag for tag in tags if tag != "__api_success__"]

            # Get actual model used from response
            return {
                "tags": tags,
                "model_used": self.model_name if api_success else "fallback",
                "success": api_success
            }

        except Exception as e:
            print(f"Error in suggest_tags_with_model_info: {e}")
            return {
                "tags": [],
                "model_used": "error",
                "success": False
            }

    def set_user_preference(self, model_name: str):
        """
        Set user's preferred model for tag suggestion

        Args:
            model_name: Model name from litellm_config.yaml
        """
        self.llm_manager.set_user_preference(
            task_type=self.task_type,
            model_name=model_name,
            user_id=self.user_id
        )

    def get_available_models(self) -> List[Dict]:
        """Get list of available models for tag suggestion"""
        all_models = self.llm_manager.get_available_models()
        return all_models.get(self.task_type, [])
