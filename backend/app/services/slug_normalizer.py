"""
Slug normalization service for converting tags to snake_case slugs
and maintaining display names.
"""
from typing import Tuple, Optional
import re

class SlugNormalizer:
    """Service for normalizing tags to snake_case slugs"""
    
    # Common acronyms that should stay uppercase in display names
    ACRONYMS = {
        'ai', 'ml', 'llm', 'llms', 'gpt', 'bert', 'api', 'url', 'uri', 'http', 'https',
        'nlp', 'cv', 'rl', 'gan', 'gans', 'vae', 'cnn', 'rnn', 'lstm', 'gru', 'mlp',
        'agi', 'sota', 'rlhf', 'sft', 'dpo', 'ppo', 'kl', 'elbo', 'vqvae', 'clip',
        'gpu', 'cpu', 'tpu', 'ram', 'vram', 'cuda', 'rocm', 'onnx', 'gguf', 'ggml',
        'pdf', 'html', 'xml', 'json', 'yaml', 'csv', 'sql', 'aws', 'gcp', 'azure',
        'bert', 'roberta', 't5', 'gpt2', 'gpt3', 'gpt4', 'gpt5', 'palm', 'llama',
        'rag', 'dspy', 'mcp', 'vllm', 'tgi', 'hf', 'mlx', 'jax', 'tvm', 'ort',
        'emnlp', 'acl', 'neurips', 'icml', 'iclr', 'cvpr', 'eccv', 'iccv', 'naacl'
    }
    
    @staticmethod
    def to_snake_case(text: str) -> str:
        """
        Convert any text to snake_case slug.
        
        Examples:
            "GPT-4" -> "gpt_4"
            "machine-learning" -> "machine_learning"
            "AI Safety" -> "ai_safety"
            "LLMs" -> "llms"
        """
        if not text:
            return ""
        
        # Convert to lowercase
        slug = text.lower()
        
        # Replace hyphens and spaces with underscores
        slug = slug.replace('-', '_').replace(' ', '_')
        
        # Remove any special characters except alphanumeric and underscores
        slug = re.sub(r'[^a-z0-9_]', '_', slug)
        
        # Replace multiple underscores with single
        slug = re.sub(r'_+', '_', slug)
        
        # Remove leading/trailing underscores
        slug = slug.strip('_')
        
        return slug
    
    @staticmethod
    def to_display_name(original_text: str) -> str:
        """
        Create a human-readable display name from the original text.
        
        Examples:
            "gpt-4" -> "GPT-4"
            "machine_learning" -> "Machine Learning"
            "ai-safety" -> "AI Safety"
            "llms" -> "LLMs"
        """
        if not original_text:
            return ""
        
        # Handle special cases for GPT models
        if original_text.lower().startswith('gpt-'):
            parts = original_text.split('-')
            return 'GPT-' + '-'.join(parts[1:])
        
        if original_text.lower().startswith('gpt_'):
            parts = original_text.split('_')
            return 'GPT-' + '-'.join(parts[1:])
        
        # Handle version numbers (e.g., "bert_v2" -> "BERT v2")
        if re.match(r'.*_v\d+$', original_text.lower()):
            base, version = original_text.rsplit('_v', 1)
            base_display = SlugNormalizer.to_display_name(base)
            return f"{base_display} v{version}"
        
        # Split by underscores, hyphens, or spaces
        parts = re.split(r'[-_\s]+', original_text)
        
        # Process each part
        display_parts = []
        for part in parts:
            part_lower = part.lower()
            
            # Check if it's an acronym
            if part_lower in SlugNormalizer.ACRONYMS:
                # Special handling for LLMs (plural)
                if part_lower == 'llms':
                    display_parts.append('LLMs')
                elif part_lower == 'gans':
                    display_parts.append('GANs')
                else:
                    display_parts.append(part.upper())
            # Check if it's a number
            elif part.isdigit():
                display_parts.append(part)
            # Check if it's already properly capitalized (e.g., "OpenAI")
            elif len(part) > 1 and part[0].isupper() and not part.isupper():
                display_parts.append(part)
            # Check if it's all uppercase (likely an acronym)
            elif part.isupper() and len(part) > 1:
                display_parts.append(part)
            # Otherwise, capitalize first letter
            else:
                display_parts.append(part.capitalize() if part else '')
        
        # Join with spaces
        return ' '.join(display_parts)
    
    @staticmethod
    def normalize(text: str) -> Tuple[str, str]:
        """
        Normalize text to both slug and display name.
        
        Returns:
            Tuple of (slug, display_name)
        """
        slug = SlugNormalizer.to_snake_case(text)
        display = SlugNormalizer.to_display_name(text)
        return slug, display
    
    @staticmethod
    def get_concept_id(slug: str, prefix: str = "c") -> str:
        """
        Generate a concept ID from a slug.
        
        Args:
            slug: The snake_case slug
            prefix: The prefix for the ID (default "c" for concept)
        
        Returns:
            A concept ID like "c_machine_learning"
        """
        return f"{prefix}_{slug}" if slug else ""


# Singleton instance
_normalizer = SlugNormalizer()

def to_snake_case(text: str) -> str:
    """Convert text to snake_case slug"""
    return _normalizer.to_snake_case(text)

def to_display_name(text: str) -> str:
    """Convert text to display name"""
    return _normalizer.to_display_name(text)

def normalize(text: str) -> Tuple[str, str]:
    """Normalize text to (slug, display_name)"""
    return _normalizer.normalize(text)