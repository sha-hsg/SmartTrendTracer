"""
Extensible Paper Analysis Service using LangChain
Generates various types of analyses and summaries for research papers
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from langchain.schema import HumanMessage, SystemMessage
from app.services.llm_service import LLMService
from sqlalchemy.orm import Session
from app.models.papers import Paper

logger = logging.getLogger(__name__)

class PaperAnalysisService:
    """Service for generating various analyses of research papers"""
    
    def __init__(self):
        self.llm_service = LLMService()
        # Load configurations
        with open('prompts_config.json', 'r') as f:
            prompts_config = json.load(f)
            self.analysis_configs = prompts_config.get('paper_analyses', {})
        
        with open('llm.json', 'r') as f:
            llm_config = json.load(f)
            self.model_configs = llm_config.get('models', {})
    
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
        db: Optional[Session] = None
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
            
            # Choose model based on paper size and analysis complexity
            # Estimate tokens: roughly 1 token per 4 characters
            estimated_tokens = content_length // 4
            
            # For papers over 150K tokens (600K chars), use Gemini 2.5 Pro
            # For smaller papers, we can still use Claude if preferred
            if estimated_tokens > 150000:
                logger.info(f"Paper has ~{estimated_tokens} tokens, using Gemini 2.5 Pro for large context")
                if analysis_type in ['review', 'switt_analysis']:
                    model_key = 'paper_analysis_deep'  # Gemini 2.5 Pro with high output
                else:
                    model_key = 'paper_analysis'  # Gemini 2.5 Pro standard
            else:
                # For smaller papers, we can use Claude if the user prefers Claude's style
                logger.info(f"Paper has ~{estimated_tokens} tokens, can use Claude or Gemini")
                if analysis_type in ['review', 'switt_analysis']:
                    # For complex analyses, prefer Gemini for consistency
                    model_key = 'paper_analysis_deep'
                else:
                    # For standard analyses on smaller papers, use Gemini by default
                    # but you could make this configurable
                    model_key = 'paper_analysis'
            
            model_config = self.model_configs.get(model_key)
            if not model_config:
                logger.warning(f"No {model_key} model configured, falling back to default")
                model_config = self.model_configs.get('paper_analysis', {})
            
            # Generate analysis using LangChain
            result = self._call_llm_with_langchain(
                model_config=model_config,
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            if result:
                response = {
                    'success': True,
                    'paper_id': paper_id,
                    'analysis_type': analysis_type,
                    'analysis_name': analysis_config.get('name', analysis_type),
                    'content': result,
                    'generated_at': datetime.utcnow().isoformat(),
                    'model_used': model_config.get('model', 'unknown'),
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
                        model_used=model_config.get('model', 'unknown')
                    )
                
                return response
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
        db: Optional[Session] = None
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
    
    def _call_llm_with_langchain(
        self,
        model_config: Dict,
        system_prompt: str,
        user_prompt: str
    ) -> Optional[str]:
        """
        Call LLM using LangChain with proper provider handling
        
        Args:
            model_config: Model configuration from llm.json
            system_prompt: System message for the LLM
            user_prompt: User message for the LLM
            
        Returns:
            Generated text or None if failed
        """
        try:
            # Get the LangChain client
            client = self.llm_service._get_client(model_config)
            
            if client is None:
                logger.error("Could not get LLM client")
                return None
            
            # Prepare messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # Call the LLM
            response = client.invoke(messages)
            
            # Extract content from response
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Error calling LLM with LangChain: {e}")
            
            # Try fallback to direct call if available
            if hasattr(self.llm_service, '_call_llm_with_provider'):
                try:
                    return self.llm_service._call_llm_with_provider(
                        model_config=model_config,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
            
            return None
    
    def save_analysis_to_db(
        self,
        db: Session,
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
    
    def get_saved_analyses(self, db: Session, paper_id: int) -> Dict[str, Any]:
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