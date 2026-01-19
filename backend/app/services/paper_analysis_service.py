"""
Extensible Paper Analysis Service using LLM Manager
Migrated to use unified LLM Manager with LiteLLM
Generates various types of analyses and summaries for research papers
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.services.llm_manager import get_llm_manager

logger = logging.getLogger(__name__)

class PaperAnalysisService:
    """Service for generating various analyses of research papers"""

    def __init__(self, user_id: str = "default"):
        """Initialize with LLM Manager"""
        self.llm_manager = get_llm_manager()
        self.user_id = user_id

        # Task types from litellm_config.yaml
        self.task_type_standard = 'paper_analysis'
        self.task_type_deep = 'paper_analysis_deep'

        # Load prompts configuration
        with open('prompts_config.json', 'r') as f:
            prompts_config = json.load(f)
            self.analysis_configs = prompts_config.get('paper_analyses', {})

        # Get model attribution
        task_info = self.llm_manager.get_task_info(self.task_type_standard)
        self.model_name = task_info['model'] if task_info else 'unknown'
    
    def get_available_analyses(self) -> List[Dict[str, str]]:
        """
        Get list of available analysis types with metadata
        
        Returns:
            List of analysis configurations with name, description, and category
        """
        analyses = []
        for key, config in self.analysis_configs.items():
            analyses.append({
                'id': key,
                'name': config.get('name', key),
                'description': config.get('description', ''),
                'category': config.get('category', 'general')
            })
        
        # Sort by category, then by name
        analyses.sort(key=lambda x: (x['category'], x['name']))
        return analyses
    
    def get_analyses_by_category(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get analyses grouped by category
        
        Returns:
            Dictionary with categories as keys and lists of analyses as values
        """
        by_category = {}
        for analysis in self.get_available_analyses():
            category = analysis['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(analysis)
        return by_category
    
    def generate_analysis(
        self, 
        paper_id: int,
        analysis_type: str,
        paper_content: Optional[str] = None,
        db: Optional[Any] = None  # MongoDB database connection
    ) -> Dict[str, Any]:
        """
        Generate a specific type of analysis for a paper
        
        Args:
            paper_id: ID of the paper to analyze
            analysis_type: Type of analysis to generate (e.g., 'layman_summary')
            paper_content: Optional paper content (will fetch from DB if not provided)
            db: Database session (required if paper_content not provided)
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Get analysis configuration
            if analysis_type not in self.analysis_configs:
                return {
                    'success': False,
                    'error': f'Unknown analysis type: {analysis_type}'
                }
            
            analysis_config = self.analysis_configs[analysis_type]
            
            # Get paper content if not provided
            if not paper_content:
                if not db:
                    return {
                        'success': False,
                        'error': 'Database session required when paper_content not provided'
                    }
                
                paper = db.query(Paper).filter(Paper.id == paper_id).first()
                if not paper:
                    return {
                        'success': False,
                        'error': f'Paper {paper_id} not found'
                    }
                
                paper_content = paper.content or ''
                if not paper_content:
                    return {
                        'success': False,
                        'error': 'Paper has no content to analyze'
                    }
            
            # Claude Opus 4.1 has 200k token context (~800k chars)
            # Most papers are 20-50 pages (~40k-100k chars), so we can send the full content
            # Only warn if content is extremely large (>500k chars, which is ~125 pages of dense text)
            
            content_length = len(paper_content)
            # Rough estimate: 1 token ≈ 4 chars, 200k tokens ≈ 800k chars
            # Let's be conservative and warn at 500k chars
            max_safe_length = 500000  
            needs_truncation = content_length > max_safe_length
            
            if needs_truncation:
                logger.warning(f"Paper {paper_id} has {content_length} chars, which may exceed token limits")
                # Still don't truncate - send full content and let the LLM handle it
                # Modern models like Claude Opus can handle very long contexts
            
            logger.info(f"Generating {analysis_type} for paper {paper_id}")
            
            # Prepare prompts
            system_prompt = analysis_config.get('system', '')
            user_template = analysis_config.get('user_template', '')
            user_prompt = user_template.format(paper_content=paper_content)

            # Choose task type based on analysis complexity
            # Estimate tokens: roughly 1 token per 4 characters
            estimated_tokens = content_length // 4

            # For complex analyses (review, switt_analysis) or large papers, use deep analysis
            if analysis_type in ['review', 'switt_analysis'] or estimated_tokens > 150000:
                task_type = self.task_type_deep
                logger.info(f"Using deep analysis model (estimated {estimated_tokens} tokens)")
            else:
                task_type = self.task_type_standard
                logger.info(f"Using standard analysis model (estimated {estimated_tokens} tokens)")

            # Convert to OpenAI message format
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Call LLM Manager
            try:
                response = self.llm_manager.completion_sync(
                    task_type=task_type,
                    messages=messages,
                    user_id=self.user_id
                )
                result = response.choices[0].message.content
                model_used = response.model if hasattr(response, 'model') else self.model_name
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                result = None
                model_used = 'unknown'
            
            if result:
                response_data = {
                    'success': True,
                    'paper_id': paper_id,
                    'analysis_type': analysis_type,
                    'analysis_name': analysis_config.get('name', analysis_type),
                    'content': result,
                    'generated_at': datetime.utcnow().isoformat(),
                    'model_used': model_used,
                    'content_length': content_length,
                    'full_content_used': True  # We're now sending full content
                }

                # Save to database if db session is available
                if db:
                    self.save_analysis_to_db(
                        db=db,
                        paper_id=paper_id,
                        analysis_type=analysis_type,
                        content=result,
                        model_used=model_used
                    )

                return response_data
            else:
                return {
                    'success': False,
                    'error': 'Failed to generate analysis'
                }
                
        except Exception as e:
            logger.error(f"Error generating {analysis_type} analysis: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_multiple_analyses(
        self,
        paper_id: int,
        analysis_types: List[str],
        paper_content: Optional[str] = None,
        db: Optional[Any] = None  # MongoDB database connection
    ) -> Dict[str, Any]:
        """
        Generate multiple analyses for a paper
        
        Args:
            paper_id: ID of the paper to analyze
            analysis_types: List of analysis types to generate
            paper_content: Optional paper content (will fetch once and reuse)
            db: Database session
            
        Returns:
            Dictionary with results for each analysis type
        """
        # Fetch paper content once if needed
        if not paper_content and db:
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if paper:
                paper_content = paper.content or ''
        
        results = {}
        for analysis_type in analysis_types:
            result = self.generate_analysis(
                paper_id=paper_id,
                analysis_type=analysis_type,
                paper_content=paper_content,
                db=db
            )
            results[analysis_type] = result
        
        return {
            'paper_id': paper_id,
            'analyses': results,
            'total_requested': len(analysis_types),
            'successful': sum(1 for r in results.values() if r.get('success', False))
        }
    
    # Removed _call_llm_with_langchain - now using LLMManager directly
    
    def save_analysis_to_db(
        self,
        db: Any,  # MongoDB database
        paper_id: int,
        analysis_type: str,
        content: str,
        model_used: str = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save generated analysis to database for permanent storage
        
        Args:
            db: Database session
            paper_id: Paper ID
            analysis_type: Type of analysis
            content: Generated analysis content
            model_used: LLM model that was used
            metadata: Optional metadata about the analysis
            
        Returns:
            Success boolean
        """
        try:
            from app.models.papers import PaperAnalysis
            
            # Check if analysis already exists
            existing = db.query(PaperAnalysis).filter(
                PaperAnalysis.paper_id == paper_id,
                PaperAnalysis.analysis_type == analysis_type
            ).first()
            
            if existing:
                # Update existing analysis
                existing.content = content
                existing.model_used = model_used
                existing.updated_at = datetime.utcnow()
                logger.info(f"Updated existing {analysis_type} analysis for paper {paper_id}")
            else:
                # Create new analysis
                analysis = PaperAnalysis(
                    paper_id=paper_id,
                    analysis_type=analysis_type,
                    content=content,
                    model_used=model_used
                )
                db.add(analysis)
                logger.info(f"Saved new {analysis_type} analysis for paper {paper_id}")
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving analysis to database: {e}")
            db.rollback()
            return False
    
    def get_saved_analyses(self, db: Any, paper_id: int) -> Dict[str, Any]:  # MongoDB database
        """
        Retrieve all saved analyses for a paper
        
        Args:
            db: Database session
            paper_id: Paper ID
            
        Returns:
            Dictionary with analysis_type as keys and analysis data as values
        """
        try:
            from app.models.papers import PaperAnalysis
            
            analyses = db.query(PaperAnalysis).filter(
                PaperAnalysis.paper_id == paper_id
            ).all()
            
            result = {}
            for analysis in analyses:
                result[analysis.analysis_type] = {
                    'success': True,
                    'content': analysis.content,
                    'model_used': analysis.model_used,
                    'generated_at': analysis.generated_at.isoformat() if analysis.generated_at else None,
                    'analysis_name': self.analysis_configs.get(analysis.analysis_type, {}).get('name', analysis.analysis_type)
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving saved analyses: {e}")
            return {}