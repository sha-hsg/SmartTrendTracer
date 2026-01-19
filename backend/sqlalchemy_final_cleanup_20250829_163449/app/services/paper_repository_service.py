"""
Paper Repository Service
Manages paper storage, processing, and analyses
"""

import os
import hashlib
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from sqlalchemy.orm import Session
from ..models import get_db
from ..models.papers import Paper, PaperAnalysis
from ..models.paper_analysis import (
    AnalysisPrompt, PaperRepository, 
    AnalysisComparison, AnalysisType
)
from .pdf_processor_service import get_pdf_processor_service
from .llm_service import LLMService

logger = logging.getLogger(__name__)

class PaperRepositoryService:
    """Service for managing paper repository"""
    
    # Default storage paths
    REPOSITORY_BASE = Path("data/paper_repository")
    PDF_STORAGE = REPOSITORY_BASE / "pdfs"
    MARKDOWN_STORAGE = REPOSITORY_BASE / "markdown"
    IMAGES_STORAGE = REPOSITORY_BASE / "images"
    ANALYSES_STORAGE = REPOSITORY_BASE / "analyses"
    
    # Default analysis prompts
    DEFAULT_PROMPTS = {
        "summary": {
            "name": "Executive Summary",
            "system": "You are an expert scientific paper analyst. Provide concise, accurate summaries.",
            "template": """Provide a comprehensive executive summary of this research paper. Include:
1. Main research question/problem
2. Key methodology
3. Principal findings
4. Significance and impact
Keep it under 500 words.

Paper content:
{content}""",
            "icon": "📋",
            "color": "blue"
        },
        "key_contributions": {
            "name": "Key Contributions",
            "system": "You are an expert at identifying scientific contributions.",
            "template": """Identify and explain the key contributions of this paper. List:
1. Novel ideas or approaches
2. Technical innovations
3. Empirical findings
4. Theoretical advancements
Be specific and cite relevant sections.

Paper content:
{content}""",
            "icon": "🎯",
            "color": "green"
        },
        "methodology": {
            "name": "Methodology Analysis",
            "system": "You are an expert in research methodology and experimental design.",
            "template": """Analyze the research methodology used in this paper:
1. Research design and approach
2. Data collection methods
3. Analysis techniques
4. Validation methods
5. Statistical approaches (if applicable)
Evaluate the rigor and appropriateness of the methods.

Paper content:
{content}""",
            "icon": "🔬",
            "color": "purple"
        },
        "limitations": {
            "name": "Limitations & Critiques",
            "system": "You are a critical reviewer identifying limitations and potential issues.",
            "template": """Identify limitations and potential critiques of this work:
1. Acknowledged limitations by authors
2. Unacknowledged limitations
3. Methodological weaknesses
4. Scope restrictions
5. Potential biases
Be constructive and fair in your assessment.

Paper content:
{content}""",
            "icon": "⚠️",
            "color": "orange"
        },
        "future_work": {
            "name": "Future Research Directions",
            "system": "You are an expert at identifying research opportunities.",
            "template": """Based on this paper, identify:
1. Future work suggested by authors
2. Unexplored research questions
3. Potential extensions
4. Applications to other domains
5. Methodological improvements
Focus on actionable research directions.

Paper content:
{content}""",
            "icon": "🚀",
            "color": "teal"
        },
        "practical_applications": {
            "name": "Practical Applications",
            "system": "You are an expert at identifying real-world applications of research.",
            "template": """Identify practical applications of this research:
1. Industry applications
2. Product development opportunities
3. Policy implications
4. Educational applications
5. Societal impact
Be specific about implementation possibilities.

Paper content:
{content}""",
            "icon": "💡",
            "color": "yellow"
        },
        "related_work": {
            "name": "Related Work Analysis",
            "system": "You are an expert at analyzing scientific literature connections.",
            "template": """Analyze the related work and literature connections:
1. Key papers cited and their relevance
2. Research lineage and influences
3. Comparison with competing approaches
4. Gaps in literature review
5. Position within the field
Provide context for how this work fits in the broader landscape.

Paper content:
{content}""",
            "icon": "🔗",
            "color": "indigo"
        },
        "technical_depth": {
            "name": "Technical Deep Dive",
            "system": "You are a technical expert capable of deep analysis.",
            "template": """Provide a deep technical analysis:
1. Mathematical formulations and proofs
2. Algorithm details and complexity
3. Implementation considerations
4. Technical assumptions
5. Edge cases and failure modes
Focus on technical rigor and completeness.

Paper content:
{content}""",
            "icon": "⚙️",
            "color": "gray"
        },
        "impact_assessment": {
            "name": "Impact Assessment",
            "system": "You are an expert at assessing research impact and significance.",
            "template": """Assess the potential impact of this research:
1. Scientific impact (citations potential, field advancement)
2. Technological impact (enabling new technologies)
3. Economic impact (cost savings, new markets)
4. Social impact (benefits to society)
5. Long-term significance
Provide evidence-based assessment.

Paper content:
{content}""",
            "icon": "📊",
            "color": "red"
        }
    }
    
    def __init__(self):
        """Initialize repository service"""
        self._ensure_directories()
        self.llm_service = LLMService()
        self.pdf_processor = get_pdf_processor_service()
        logger.info("Paper Repository Service initialized")
    
    def _ensure_directories(self):
        """Ensure all repository directories exist"""
        for path in [self.PDF_STORAGE, self.MARKDOWN_STORAGE, 
                    self.IMAGES_STORAGE, self.ANALYSES_STORAGE]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def import_paper(self, 
                    pdf_path: str,
                    paper_data: Dict,
                    process_immediately: bool = True,
                    generate_analyses: List[str] = None) -> Dict:
        """
        Import a paper into the repository
        
        Args:
            pdf_path: Path to PDF file
            paper_data: Paper metadata
            process_immediately: Whether to process PDF to markdown
            generate_analyses: List of analysis types to generate
        
        Returns:
            Import result dictionary
        """
        db = next(get_db())
        
        try:
            # Calculate file hash
            pdf_hash = self._calculate_file_hash(pdf_path)
            
            # Check if paper already exists
            existing_repo = db.query(PaperRepository).filter(
                PaperRepository.pdf_hash == pdf_hash
            ).first()
            
            if existing_repo:
                return {
                    'success': False,
                    'error': 'Paper already exists in repository',
                    'paper_id': existing_repo.paper_id
                }
            
            # Create or get paper record
            paper = db.query(Paper).filter(
                Paper.arxiv_id == paper_data.get('arxiv_id')
            ).first()
            
            if not paper:
                paper = Paper(**paper_data)
                db.add(paper)
                db.flush()
            
            # Copy PDF to repository
            pdf_filename = f"{paper.id}_{Path(pdf_path).name}"
            repo_pdf_path = self.PDF_STORAGE / pdf_filename
            shutil.copy2(pdf_path, repo_pdf_path)
            
            # Create repository record
            repo = PaperRepository(
                paper_id=paper.id,
                pdf_original_path=str(repo_pdf_path),
                pdf_size_bytes=repo_pdf_path.stat().st_size,
                pdf_hash=pdf_hash,
                imported_at=datetime.utcnow()
            )
            db.add(repo)
            
            # Process PDF if requested
            if process_immediately:
                process_result = self._process_pdf(paper.id, str(repo_pdf_path))
                if process_result['success']:
                    repo.markdown_path = process_result['markdown_path']
                    repo.markdown_generated = True
                    repo.pdf_processed = True
                    repo.processed_at = datetime.utcnow()
                    
                    # Update paper content
                    paper.content = process_result['content']
                    paper.processor_used = process_result['processor_used']
            
            # Generate analyses if requested
            if generate_analyses:
                for analysis_type in generate_analyses:
                    self.generate_analysis(paper.id, analysis_type)
            
            db.commit()
            
            return {
                'success': True,
                'paper_id': paper.id,
                'repository_id': repo.id,
                'pdf_path': str(repo_pdf_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to import paper: {e}")
            db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            db.close()
    
    def _process_pdf(self, paper_id: int, pdf_path: str) -> Dict:
        """Process PDF to markdown with image extraction"""
        try:
            # Process with MinerU and extract images
            result = self.pdf_processor.process_pdf(pdf_path, paper_id=paper_id)
            
            if result['success']:
                # Save markdown
                md_filename = f"{paper_id}_content.md"
                md_path = self.MARKDOWN_STORAGE / md_filename
                
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(result['markdown'])
                
                return {
                    'success': True,
                    'markdown_path': str(md_path),
                    'content': result['markdown'],
                    'processor_used': result['method_used']
                }
            
            return {
                'success': False,
                'error': result.get('error', 'Processing failed')
            }
            
        except Exception as e:
            logger.error(f"Failed to process PDF: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_analysis(self, 
                         paper_id: int,
                         analysis_type: str,
                         custom_prompt: Optional[str] = None) -> Optional[int]:
        """
        Generate an analysis for a paper
        
        Args:
            paper_id: Paper ID
            analysis_type: Type of analysis
            custom_prompt: Custom prompt (for CUSTOM type)
        
        Returns:
            Analysis ID if successful, None otherwise
        """
        db = next(get_db())
        
        try:
            # Get paper and content
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if not paper:
                logger.error(f"Paper {paper_id} not found")
                return None
            
            # Get or create prompt
            if analysis_type == "custom":
                if not custom_prompt:
                    logger.error("Custom prompt required for custom analysis")
                    return None
                prompt_template = custom_prompt
                system_prompt = "You are an expert paper analyst."
                analysis_name = "Custom Analysis"
            else:
                if analysis_type not in self.DEFAULT_PROMPTS:
                    logger.error(f"Unknown analysis type: {analysis_type}")
                    return None
                
                prompt_config = self.DEFAULT_PROMPTS[analysis_type]
                prompt_template = prompt_config['template']
                system_prompt = prompt_config['system']
                analysis_name = prompt_config['name']
            
            # Format prompt with content
            formatted_prompt = prompt_template.format(
                content=paper.content[:50000]  # Limit content length
            )
            
            # Generate analysis with LLM
            response = self.llm_service.generate_text(
                prompt=formatted_prompt,
                system_message=system_prompt,
                max_tokens=2000,
                temperature=0.7
            )
            
            if not response:
                logger.error("Failed to generate analysis")
                return None
            
            # Mark previous versions as not latest
            db.query(PaperAnalysis).filter(
                PaperAnalysis.paper_id == paper_id,
                PaperAnalysis.analysis_type == analysis_type
            ).update({'is_latest': False})
            
            # Create analysis record
            analysis = PaperAnalysis(
                paper_id=paper_id,
                analysis_type=analysis_type,
                analysis_name=analysis_name,
                prompt_used=formatted_prompt,
                content=response,
                model_used=self.llm_service.model,
                word_count=len(response.split()),
                version=1,
                is_latest=True
            )
            
            db.add(analysis)
            db.commit()
            
            logger.info(f"Generated {analysis_type} analysis for paper {paper_id}")
            return analysis.id
            
        except Exception as e:
            logger.error(f"Failed to generate analysis: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def get_paper_analyses(self, paper_id: int) -> List[Dict]:
        """Get all analyses for a paper"""
        db = next(get_db())
        
        try:
            analyses = db.query(PaperAnalysis).filter(
                PaperAnalysis.paper_id == paper_id,
                PaperAnalysis.is_latest == True
            ).all()
            
            return [
                {
                    'id': a.id,
                    'type': a.analysis_type,
                    'name': a.analysis_name,
                    'content': a.content,
                    'model': a.model_used,
                    'created_at': a.created_at.isoformat() if a.created_at else None,
                    'word_count': a.word_count
                }
                for a in analyses
            ]
            
        finally:
            db.close()
    
    def compare_papers(self,
                       paper_ids: List[int],
                       analysis_type: str) -> Optional[Dict]:
        """Compare analyses across multiple papers"""
        db = next(get_db())
        
        try:
            # Get analyses for all papers
            analyses = db.query(PaperAnalysis).filter(
                PaperAnalysis.paper_id.in_(paper_ids),
                PaperAnalysis.analysis_type == analysis_type,
                PaperAnalysis.is_latest == True
            ).all()
            
            if len(analyses) < 2:
                logger.error("Need at least 2 papers with analyses to compare")
                return None
            
            # Prepare comparison prompt
            comparison_content = "\n\n".join([
                f"Paper {a.paper_id}:\n{a.content[:2000]}"
                for a in analyses
            ])
            
            prompt = f"""Compare the following {analysis_type} analyses from different papers:

{comparison_content}

Provide:
1. Key similarities
2. Key differences
3. Unique insights from each paper
4. Overall comparison summary"""
            
            # Generate comparison
            response = self.llm_service.generate_text(
                prompt=prompt,
                system_message="You are an expert at comparative analysis of scientific papers.",
                max_tokens=2000
            )
            
            if not response:
                return None
            
            # Store comparison
            comparison = AnalysisComparison(
                paper_ids=paper_ids,
                analysis_type=analysis_type,
                comparison_content=response,
                model_used=self.llm_service.model
            )
            
            db.add(comparison)
            db.commit()
            
            return {
                'id': comparison.id,
                'paper_ids': paper_ids,
                'analysis_type': analysis_type,
                'content': response
            }
            
        except Exception as e:
            logger.error(f"Failed to compare papers: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def initialize_default_prompts(self):
        """Initialize default analysis prompts in database"""
        db = next(get_db())
        
        try:
            for key, config in self.DEFAULT_PROMPTS.items():
                # Check if prompt exists
                existing = db.query(AnalysisPrompt).filter(
                    AnalysisPrompt.prompt_key == key
                ).first()
                
                if not existing:
                    prompt = AnalysisPrompt(
                        prompt_key=key,
                        prompt_name=config['name'],
                        system_prompt=config['system'],
                        user_prompt_template=config['template'],
                        icon=config['icon'],
                        color=config['color'],
                        is_fixed=True,
                        is_active=True,
                        display_order=list(self.DEFAULT_PROMPTS.keys()).index(key)
                    )
                    db.add(prompt)
            
            db.commit()
            logger.info("Initialized default analysis prompts")
            
        except Exception as e:
            logger.error(f"Failed to initialize prompts: {e}")
            db.rollback()
        finally:
            db.close()


# Singleton instance
_repository_service = None

def get_repository_service() -> PaperRepositoryService:
    """Get or create repository service singleton"""
    global _repository_service
    if _repository_service is None:
        _repository_service = PaperRepositoryService()
        _repository_service.initialize_default_prompts()
    return _repository_service