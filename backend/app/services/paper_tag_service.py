"""
Service for paper tag suggestions and management
"""
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

from app.services.llm_manager import get_llm_manager

logger = logging.getLogger(__name__)

class PaperTagService:
    def __init__(self, user_id: str = "default"):
        self.llm_manager = get_llm_manager()
        self.user_id = user_id
        self.task_type = 'paper_tag_suggestion'
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict:
        """Load prompts from configuration"""
        prompts_path = Path(__file__).parent.parent.parent / 'prompts_config.json'
        if prompts_path.exists():
            with open(prompts_path, 'r') as f:
                all_prompts = json.load(f)
                return all_prompts.get('paper_tag_suggestion', {})
        return {}
    
    def suggest_tags_from_paper(self, db: Session, paper_id: int, max_tags: int = 10) -> List[Dict[str, any]]:
        """
        Suggest tags based on paper content using LLM
        """
        try:
            # Get paper with sections
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if not paper:
                logger.error(f"Paper {paper_id} not found")
                return []
            
            # Prepare content for tag generation
            content_parts = []
            
            # Add title and abstract
            if paper.title:
                content_parts.append(f"Title: {paper.title}")
            if paper.abstract:
                content_parts.append(f"Abstract: {paper.abstract[:1000]}")
            
            # Add key sections
            sections = db.query(PaperSection).filter(
                PaperSection.paper_id == paper_id
            ).order_by(PaperSection.position).limit(3).all()
            
            for section in sections:
                if section.content:
                    content_parts.append(f"{section.title}: {section.content[:500]}")
            
            full_content = "\n\n".join(content_parts)

            # Use LLM to generate tags via LLMManager
            system_prompt = self.prompts.get('system', '')
            user_template = self.prompts.get('user_template', '')
            user_prompt = user_template.format(
                author=paper.authors if hasattr(paper, 'authors') else 'Unknown',
                text=full_content[:3000],
                max_tags=max_tags
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            try:
                llm_response = self.llm_manager.completion_sync(
                    task_type=self.task_type,
                    messages=messages,
                    user_id=self.user_id
                )
                response = llm_response.choices[0].message.content
                
                # Parse tags from response
                tags = []
                if response:
                    # Clean and split tags
                    tag_list = response.strip().split(',')
                    for tag in tag_list[:max_tags]:
                        tag = tag.strip().lower().replace(' ', '-')
                        if tag and len(tag) > 2:
                            tags.append(tag)
                
                # Get existing tags for this paper
                existing_tags = db.query(PaperTag.tag).filter(
                    PaperTag.paper_id == paper_id
                ).all()
                existing_tag_set = {tag[0] for tag in existing_tags}
                
                # Get usage counts for suggested tags
                suggestions = []
                for tag in tags:
                    if tag not in existing_tag_set:
                        # Count how many times this tag is used
                        usage_count = db.query(func.count(PaperTag.id)).filter(
                            PaperTag.tag == tag
                        ).scalar()
                        
                        suggestions.append({
                            'tag': tag,
                            'type': 'ai_suggested',
                            'usage_count': usage_count,
                            'confidence': 0.8  # Could be calculated based on context
                        })
                
                return suggestions
                
            except Exception as e:
                logger.error(f"Error calling LLM for tag suggestions: {e}")
                return self._fallback_tag_extraction(full_content)
            
        except Exception as e:
            logger.error(f"Error suggesting tags for paper {paper_id}: {e}")
            return []
    
    def _fallback_tag_extraction(self, content: str) -> List[Dict[str, any]]:
        """
        Fallback method to extract tags using simple keyword extraction
        """
        # Common research keywords
        keywords = [
            'machine-learning', 'deep-learning', 'neural-network',
            'transformer', 'attention', 'optimization', 'algorithm',
            'dataset', 'benchmark', 'evaluation', 'performance',
            'natural-language', 'computer-vision', 'reinforcement-learning'
        ]
        
        suggestions = []
        content_lower = content.lower()
        
        for keyword in keywords:
            if keyword.replace('-', ' ') in content_lower or keyword in content_lower:
                suggestions.append({
                    'tag': keyword,
                    'type': 'keyword_extracted',
                    'usage_count': 0,
                    'confidence': 0.5
                })
        
        return suggestions[:10]
    
    def get_popular_tags(self, db: Session, limit: int = 20) -> List[Dict[str, any]]:
        """
        Get most popular tags across all papers
        """
        try:
            popular_tags = db.query(
                PaperTag.tag,
                func.count(PaperTag.id).label('count')
            ).group_by(PaperTag.tag).order_by(
                func.count(PaperTag.id).desc()
            ).limit(limit).all()
            
            return [
                {'tag': tag, 'count': count}
                for tag, count in popular_tags
            ]
        except Exception as e:
            logger.error(f"Error getting popular tags: {e}")
            return []
    
    def get_related_tags(self, db: Session, tag: str, limit: int = 10) -> List[str]:
        """
        Get tags that frequently co-occur with the given tag
        """
        try:
            # Find papers with this tag
            papers_with_tag = db.query(PaperTag.paper_id).filter(
                PaperTag.tag == tag
            ).subquery()
            
            # Find other tags on those papers
            related_tags = db.query(
                PaperTag.tag,
                func.count(PaperTag.id).label('count')
            ).filter(
                PaperTag.paper_id.in_(papers_with_tag),
                PaperTag.tag != tag
            ).group_by(PaperTag.tag).order_by(
                func.count(PaperTag.id).desc()
            ).limit(limit).all()
            
            return [tag for tag, _ in related_tags]
            
        except Exception as e:
            logger.error(f"Error getting related tags: {e}")
            return []
    
    def create_tag_hierarchy(self, db: Session) -> Dict[str, List[str]]:
        """
        Create a hierarchical structure of tags based on co-occurrence
        """
        # Define parent categories
        categories = {
            'methods': ['machine-learning', 'deep-learning', 'neural-network', 
                       'reinforcement-learning', 'supervised-learning', 'unsupervised-learning'],
            'architectures': ['transformer', 'cnn', 'rnn', 'lstm', 'gpt', 'bert', 'vae', 'gan'],
            'applications': ['nlp', 'computer-vision', 'speech-recognition', 'robotics', 
                           'recommendation-systems', 'time-series'],
            'tasks': ['classification', 'regression', 'clustering', 'generation', 
                     'translation', 'summarization', 'question-answering'],
            'evaluation': ['benchmark', 'dataset', 'metrics', 'evaluation', 'ablation', 'comparison'],
            'optimization': ['gradient-descent', 'adam', 'sgd', 'loss-function', 'regularization'],
            'theory': ['theory', 'analysis', 'proof', 'complexity', 'convergence']
        }
        
        # Get all tags with counts
        all_tags = db.query(
            PaperTag.tag,
            func.count(PaperTag.id).label('count')
        ).group_by(PaperTag.tag).all()
        
        # Build hierarchy
        hierarchy = {}
        uncategorized = []
        
        for tag, count in all_tags:
            categorized = False
            for category, keywords in categories.items():
                # Check if tag matches any keyword in category
                for keyword in keywords:
                    if keyword in tag or tag in keyword:
                        if category not in hierarchy:
                            hierarchy[category] = []
                        hierarchy[category].append({'tag': tag, 'count': count})
                        categorized = True
                        break
                if categorized:
                    break
            
            if not categorized:
                uncategorized.append({'tag': tag, 'count': count})
        
        # Sort tags within categories by count
        for category in hierarchy:
            hierarchy[category].sort(key=lambda x: x['count'], reverse=True)
        
        hierarchy['other'] = sorted(uncategorized, key=lambda x: x['count'], reverse=True)
        
        return hierarchy