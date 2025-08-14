"""
spaCy-based tag extraction for intelligent fallback
Uses NER, POS tagging, and noun phrase extraction
"""
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not available, will use simple fallback")

from typing import List, Set
import re
from collections import Counter

class SpacyTagger:
    def __init__(self):
        """Initialize spaCy with English model"""
        if not SPACY_AVAILABLE:
            self.nlp = None
            return
            
        try:
            # Try to load the model
            self.nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy model loaded successfully")
        except OSError:
            print("⚠️ spaCy model not found")
            self.nlp = None
        except Exception as e:
            print(f"⚠️ Error loading spaCy: {e}")
            self.nlp = None
    
    def extract_tags(self, text: str, max_tags: int = 5) -> List[str]:
        """
        Extract intelligent tags using spaCy NLP
        
        Args:
            text: The text to extract tags from
            max_tags: Maximum number of tags to return
            
        Returns:
            List of extracted tags
        """
        # If spaCy not available, return empty list
        if self.nlp is None:
            return []
            
        # Process text with spaCy
        doc = self.nlp(text)
        
        tags = []
        tag_candidates = []
        
        # 1. Extract Named Entities
        entities = self._extract_entities(doc)
        tag_candidates.extend(entities)
        
        # 2. Extract important noun phrases
        noun_phrases = self._extract_noun_phrases(doc)
        tag_candidates.extend(noun_phrases)
        
        # 3. Extract key terms based on POS patterns
        key_terms = self._extract_key_terms(doc)
        tag_candidates.extend(key_terms)
        
        # 4. Extract hashtags (if any)
        hashtags = re.findall(r'#(\w+)', text)
        tag_candidates.extend([h.lower() for h in hashtags])
        
        # 5. Score and rank candidates
        ranked_tags = self._rank_candidates(tag_candidates, doc)
        
        # 6. Clean and format tags
        final_tags = []
        seen = set()
        for tag in ranked_tags:
            clean_tag = self._clean_tag(tag)
            if clean_tag and clean_tag not in seen and len(clean_tag) > 2:
                final_tags.append(clean_tag)
                seen.add(clean_tag)
                if len(final_tags) >= max_tags:
                    break
        
        # 7. Add domain-specific tags if space remains
        if len(final_tags) < max_tags:
            domain_tags = self._add_domain_tags(text, final_tags)
            final_tags.extend(domain_tags[:max_tags - len(final_tags)])
        
        return final_tags
    
    def _extract_entities(self, doc) -> List[str]:
        """Extract named entities as potential tags"""
        entities = []
        for ent in doc.ents:
            # Focus on relevant entity types
            if ent.label_ in ['ORG', 'PRODUCT', 'PERSON', 'GPE', 'EVENT', 'WORK_OF_ART']:
                entities.append(ent.text.lower())
        return entities
    
    def _extract_noun_phrases(self, doc) -> List[str]:
        """Extract meaningful noun phrases"""
        noun_phrases = []
        for chunk in doc.noun_chunks:
            # Skip very common/generic phrases
            if len(chunk.text) > 3 and not all(token.is_stop for token in chunk):
                # Get the core noun phrase without determiners
                core_phrase = ' '.join([token.text for token in chunk 
                                       if not token.is_stop and token.pos_ != 'DET'])
                if core_phrase:
                    noun_phrases.append(core_phrase.lower())
        return noun_phrases
    
    def _extract_key_terms(self, doc) -> List[str]:
        """Extract key terms based on POS patterns"""
        key_terms = []
        
        # Extract compound nouns
        for i, token in enumerate(doc[:-1]):
            if token.pos_ == 'NOUN' and doc[i + 1].pos_ == 'NOUN':
                compound = f"{token.text} {doc[i + 1].text}"
                key_terms.append(compound.lower())
        
        # Extract important single nouns (not stop words)
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN'] and 
                not token.is_stop and 
                len(token.text) > 2 and
                token.text.lower() not in ['http', 'https', 'com']):
                key_terms.append(token.text.lower())
        
        return key_terms
    
    def _rank_candidates(self, candidates: List[str], doc) -> List[str]:
        """Rank candidate tags by importance"""
        # Count frequency
        freq_counter = Counter(candidates)
        
        # Score based on various factors
        scores = {}
        for candidate in set(candidates):
            score = 0
            
            # Frequency score
            score += freq_counter[candidate] * 2
            
            # Length preference (not too short, not too long)
            word_count = len(candidate.split())
            if word_count == 1:
                score += 1
            elif word_count == 2:
                score += 2
            elif word_count == 3:
                score += 1
            
            # Capitalize proper nouns get a boost
            if any(word[0].isupper() for word in candidate.split() if word):
                score += 1
            
            # Technical terms get a boost
            if any(term in candidate.lower() for term in 
                   ['ai', 'ml', 'gpt', 'api', 'model', 'data', 'neural', 'tech']):
                score += 2
            
            scores[candidate] = score
        
        # Sort by score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [tag for tag, _ in ranked]
    
    def _clean_tag(self, tag: str) -> str:
        """Clean and format a tag"""
        # Remove extra whitespace
        tag = ' '.join(tag.split())
        
        # Replace spaces with hyphens
        tag = tag.replace(' ', '-')
        
        # Remove special characters except hyphens
        tag = re.sub(r'[^a-z0-9\-]', '', tag.lower())
        
        # Remove trailing/leading hyphens
        tag = tag.strip('-')
        
        return tag
    
    def _add_domain_tags(self, text: str, existing_tags: List[str]) -> List[str]:
        """Add domain-specific tags based on context"""
        domain_tags = []
        text_lower = text.lower()
        
        # AI/ML specific patterns
        patterns = {
            'announcement': ['announced', 'announcing', 'introduces', 'launching'],
            'research': ['paper', 'study', 'research', 'findings'],
            'update': ['updated', 'new version', 'v2', 'v3', 'release'],
            'collaboration': ['partnership', 'collaboration', 'working with', 'joined'],
            'performance': ['faster', 'improved', 'better', 'performance', 'benchmark'],
            'open-source': ['open source', 'open-source', 'github', 'repository'],
            'tutorial': ['how to', 'guide', 'tutorial', 'learn'],
            'discussion': ['thoughts', 'opinion', 'debate', 'discuss'],
            'breaking-news': ['breaking', 'just in', 'alert'],
        }
        
        for tag, keywords in patterns.items():
            if tag not in existing_tags:
                if any(keyword in text_lower for keyword in keywords):
                    domain_tags.append(tag)
        
        return domain_tags


# Singleton instance
_spacy_tagger = None

def get_spacy_tagger() -> SpacyTagger:
    """Get or create spaCy tagger instance"""
    global _spacy_tagger
    if _spacy_tagger is None:
        _spacy_tagger = SpacyTagger()
    return _spacy_tagger