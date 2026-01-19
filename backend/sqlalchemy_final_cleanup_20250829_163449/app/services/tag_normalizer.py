"""
Tag normalization service
Handles tag case normalization and synonym resolution
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import re

class TagNormalizer:
    """Service for normalizing tags and resolving synonyms"""
    
    # Known proper capitalizations for common terms
    PROPER_FORMS = {
        'openai': 'OpenAI',
        'deepmind': 'DeepMind',
        'anthropic': 'Anthropic',
        'chatgpt': 'ChatGPT',
        'gpt-4': 'GPT-4',
        'gpt-3': 'GPT-3',
        'gpt-4o': 'GPT-4o',
        'gpt-5': 'GPT-5',
        'claude': 'Claude',
        'gemini': 'Gemini',
        'llama': 'LLaMA',
        'mistral': 'Mistral',
        'huggingface': 'HuggingFace',
        'tensorflow': 'TensorFlow',
        'pytorch': 'PyTorch',
        'javascript': 'JavaScript',
        'typescript': 'TypeScript',
        'github': 'GitHub',
        'gitlab': 'GitLab',
        'linkedin': 'LinkedIn',
        'youtube': 'YouTube',
        'microsoft': 'Microsoft',
        'google': 'Google',
        'amazon': 'Amazon',
        'facebook': 'Facebook',
        'meta': 'Meta',
        'tesla': 'Tesla',
        'spacex': 'SpaceX',
        'nvidia': 'NVIDIA',
        'ai': 'AI',
        'ml': 'ML',
        'nlp': 'NLP',
        'llm': 'LLM',
        'agi': 'AGI',
        'api': 'API',
        'gpu': 'GPU',
        'cpu': 'CPU',
        'rlhf': 'RLHF',
        'rag': 'RAG',
        'lora': 'LoRA',
        'peft': 'PEFT',
        'qwen': 'Qwen',
        'qwen-2': 'Qwen-2',
        'qwen-2.5': 'Qwen-2.5',
        'llms': 'LLMs',
        'gemma': 'Gemma',
        'gemma-2': 'Gemma-2',
        'llama-3': 'LLaMA-3',
        'llama-3.1': 'LLaMA-3.1',
        'sota': 'SOTA',
        'vllm': 'vLLM',
        'bert': 'BERT',
        'clip': 'CLIP',
        'gan': 'GAN',
        'vae': 'VAE',
        'rnn': 'RNN',
        'cnn': 'CNN',
        'lstm': 'LSTM',
        'gru': 'GRU'
    }
    
    def __init__(self, db: Session):
        self.db = db
        self._synonym_cache = None
        
    def normalize_tag(self, tag: str) -> str:
        """
        Normalize a tag to its proper form
        
        Steps:
        1. Check if it's a known proper form
        2. Check if it has a synonym relationship
        3. Apply smart capitalization rules
        4. Default to lowercase for new tags
        """
        if not tag:
            return tag
            
        # Remove leading/trailing whitespace
        tag = tag.strip()
        
        # Check if it's already in a known proper form
        tag_lower = tag.lower()
        if tag_lower in self.PROPER_FORMS:
            return self.PROPER_FORMS[tag_lower]
        
        # Check for synonym relationships
        primary = self.get_primary_tag(tag)
        if primary and primary != tag:
            return primary
        
        # Apply smart capitalization rules for new tags
        return self.smart_capitalize(tag)
    
    def get_primary_tag(self, tag: str) -> Optional[str]:
        """Get the primary tag for a given tag (if it's a synonym)"""
        # Check if this tag is a synonym in the new schema
        cursor = self.db.execute(
            text("""
                SELECT tc.tag 
                FROM tag_synonyms ts 
                JOIN tag_concepts tc ON ts.concept_id = tc.id 
                WHERE ts.synonym_tag = :tag
            """),
            {"tag": tag}
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Check if this tag is a concept itself
        cursor = self.db.execute(
            text("SELECT tag FROM tag_concepts WHERE tag = :tag LIMIT 1"),
            {"tag": tag}
        )
        result = cursor.fetchone()
        
        if result:
            return tag
        
        return None
    
    def get_all_synonyms(self, tag: str) -> List[str]:
        """Get all synonyms for a tag (including the tag itself)"""
        synonyms = [tag]
        
        # Get primary tag if this is a synonym
        primary = self.get_primary_tag(tag)
        if primary and primary != tag:
            synonyms.append(primary)
            tag = primary
        
        # Find the concept ID for this tag
        cursor = self.db.execute(
            text("SELECT id FROM tag_concepts WHERE tag = :tag"),
            {"tag": tag}
        )
        result = cursor.fetchone()
        
        if result:
            concept_id = result[0]
            # Get all synonyms of this concept
            cursor = self.db.execute(
                text("SELECT synonym_tag FROM tag_synonyms WHERE concept_id = :concept_id"),
                {"concept_id": concept_id}
            )
            
            for row in cursor.fetchall():
                if row[0] not in synonyms:
                    synonyms.append(row[0])
        
        return synonyms
    
    def smart_capitalize(self, tag: str) -> str:
        """
        Apply smart capitalization rules for tags
        
        Rules:
        1. Known acronyms → uppercase
        2. Multi-word tags → Title Case for clear terms
        3. Single words → lowercase by default
        """
        # Check for acronyms (2-5 uppercase letters)
        if re.match(r'^[A-Z]{2,5}$', tag.replace('-', '').replace('&', '')):
            return tag.upper()
        
        # Multi-word tags
        if '-' in tag or '_' in tag or ' ' in tag:
            words = re.split(r'[-_ ]', tag)
            
            # Check each word
            capitalized_words = []
            for word in words:
                word_lower = word.lower()
                
                # Check if it's a known term
                if word_lower in self.PROPER_FORMS:
                    capitalized_words.append(self.PROPER_FORMS[word_lower])
                # Check if it's an acronym
                elif len(word) <= 5 and word.isupper():
                    capitalized_words.append(word)
                # Check if it's already properly capitalized
                elif word and word[0].isupper() and word[1:].islower():
                    capitalized_words.append(word)
                else:
                    # Default to lowercase for uncertain words
                    capitalized_words.append(word_lower)
            
            # Rejoin with original separator
            if '-' in tag:
                return '-'.join(capitalized_words)
            elif '_' in tag:
                return '_'.join(capitalized_words)
            else:
                return ' '.join(capitalized_words)
        
        # Single word - default to lowercase unless it's a clear proper noun
        if tag and tag[0].isupper() and tag[1:].islower():
            # Looks like a proper noun, check if it's in our known forms
            tag_lower = tag.lower()
            if tag_lower in self.PROPER_FORMS:
                return self.PROPER_FORMS[tag_lower]
        
        # Default to lowercase for new single-word tags
        return tag.lower()
    
    def create_synonym(self, primary_tag: str, synonym_tag: str) -> bool:
        """Create a synonym relationship between two tags"""
        try:
            # Normalize the primary tag first
            primary_tag = self.normalize_tag(primary_tag)
            
            # Find or create the concept
            cursor = self.db.execute(
                text("SELECT id FROM tag_concepts WHERE tag = :tag"),
                {"tag": primary_tag}
            )
            result = cursor.fetchone()
            
            if not result:
                # Create a new concept
                cursor = self.db.execute(
                    text("""
                        INSERT INTO tag_concepts (tag, display_name, level) 
                        VALUES (:tag, :display_name, 0)
                    """),
                    {"tag": primary_tag, "display_name": primary_tag}
                )
                self.db.commit()
                
                # Get the concept ID
                cursor = self.db.execute(
                    text("SELECT id FROM tag_concepts WHERE tag = :tag"),
                    {"tag": primary_tag}
                )
                result = cursor.fetchone()
            
            concept_id = result[0]
            
            # Check if synonym already exists
            cursor = self.db.execute(
                text("SELECT id FROM tag_synonyms WHERE concept_id = :concept_id AND synonym_tag = :synonym"),
                {"concept_id": concept_id, "synonym": synonym_tag}
            )
            
            if not cursor.fetchone():
                # Insert new synonym
                self.db.execute(
                    text("INSERT INTO tag_synonyms (concept_id, synonym_tag, created_at) VALUES (:concept_id, :synonym, datetime('now'))"),
                    {"concept_id": concept_id, "synonym": synonym_tag}
                )
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            self.db.rollback()
            print(f"Error creating synonym: {e}")
            return False
    
    def merge_duplicate_tags(self, primary_tag: str, duplicate_tag: str) -> Dict:
        """
        Merge a duplicate tag into a primary tag
        Updates all references and creates a synonym relationship
        """
        from app.models import Tag
        from app.models.substack import ArticleTag
        
        result = {
            'tweets_updated': 0,
            'articles_updated': 0,
            'duplicates_removed': 0,
            'synonym_created': False
        }
        
        try:
            # Update tweet tags
            tweet_tags = self.db.query(Tag).filter(Tag.tag == duplicate_tag).all()
            
            for tag in tweet_tags:
                # Check if primary tag already exists for this tweet
                existing = self.db.query(Tag).filter(
                    Tag.tweet_id == tag.tweet_id,
                    Tag.tag == primary_tag
                ).first()
                
                if existing:
                    # Remove duplicate
                    self.db.delete(tag)
                    result['duplicates_removed'] += 1
                else:
                    # Update to primary tag
                    tag.tag = primary_tag
                    result['tweets_updated'] += 1
            
            # Update article tags
            article_tags = self.db.query(ArticleTag).filter(
                ArticleTag.tag == duplicate_tag
            ).all()
            
            for tag in article_tags:
                # Check if primary tag already exists for this article
                existing = self.db.query(ArticleTag).filter(
                    ArticleTag.article_id == tag.article_id,
                    ArticleTag.tag == primary_tag
                ).first()
                
                if existing:
                    # Remove duplicate
                    self.db.delete(tag)
                    result['duplicates_removed'] += 1
                else:
                    # Update to primary tag
                    tag.tag = primary_tag
                    result['articles_updated'] += 1
            
            # Create synonym relationship
            if self.create_synonym(primary_tag, duplicate_tag):
                result['synonym_created'] = True
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            raise e
        
        return result

def get_tag_normalizer(db: Session) -> TagNormalizer:
    """Factory function to create a TagNormalizer instance"""
    return TagNormalizer(db)