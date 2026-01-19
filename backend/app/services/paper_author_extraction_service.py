"""
Service for extracting author information from research papers using LLM
"""
import json
import re
import logging
from typing import Dict, List, Optional, Any
from app.services.llm_manager import get_llm_manager
from pathlib import Path

logger = logging.getLogger(__name__)

class PaperAuthorExtractionService:
    """Service to extract author and affiliation information from papers"""

    def __init__(self, user_id: str = "default"):
        self.llm_manager = get_llm_manager()
        self.user_id = user_id
        self.task_type = 'paper_author_extraction'
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict:
        """Load prompts from configuration"""
        prompts_path = Path(__file__).parent.parent.parent / 'prompts_config.json'
        if prompts_path.exists():
            with open(prompts_path, 'r') as f:
                all_prompts = json.load(f)
                return all_prompts.get('paper_author_extraction', {})
        return {}
        
    def extract_header_section(self, content: str, max_chars: int = 3000) -> str:
        """
        Extract the header section of a paper (between title and abstract/introduction)
        
        Args:
            content: Full paper markdown content
            max_chars: Maximum characters to consider as header
            
        Returns:
            The extracted header text
        """
        if not content:
            return ""
            
        # Look for common abstract markers
        abstract_patterns = [
            r'\n#+\s*abstract\s*\n',
            r'\nabstract\s*:?\s*\n',
            r'\n\*\*abstract\*\*',
            r'\n#+\s*introduction\s*\n',
            r'\n1\.\s*introduction',
            r'\n## 1\s+',
            r'\nsummary\s*:?\s*\n'
        ]
        
        # Find the earliest occurrence of any abstract/intro marker
        earliest_pos = len(content)
        for pattern in abstract_patterns:
            match = re.search(pattern, content.lower())
            if match and match.start() < earliest_pos:
                earliest_pos = match.start()
        
        # Extract header section (limit to reasonable size)
        header_text = content[:min(earliest_pos, max_chars)]
        
        # Clean up the header text
        # Remove markdown artifacts but preserve structure
        header_text = re.sub(r'<[^>]+>', '', header_text)  # Remove HTML tags
        header_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', header_text)  # Remove markdown links
        header_text = re.sub(r'#+\s*$', '', header_text, flags=re.MULTILINE)  # Remove empty headers
        
        return header_text.strip()
    
    def parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse the LLM response to extract author information
        
        Args:
            response: LLM response string
            
        Returns:
            Parsed author data or None if parsing fails
        """
        try:
            # Try to extract JSON from the response
            if '```json' in response:
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            elif '```' in response:
                json_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            
            # Parse the JSON
            data = json.loads(response)
            
            # Validate the structure
            if 'authors' not in data:
                logger.warning("No 'authors' field in LLM response")
                return None
                
            # Ensure all authors have required fields
            for author in data.get('authors', []):
                if 'name' not in author:
                    continue
                # Set defaults for optional fields
                author.setdefault('affiliation', '')
                author.setdefault('department', '')
                author.setdefault('email', '')
                author.setdefault('corresponding', False)
                
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response was: {response[:500]}")
            return None
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return None
    
    def extract_authors(self, paper_content: str, paper_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract author information from a paper using LLM
        
        Args:
            paper_content: Full paper markdown content
            paper_title: Optional paper title to help identify header boundary
            
        Returns:
            Dictionary with extracted author information
        """
        try:
            # Extract the header section
            header_text = self.extract_header_section(paper_content)
            
            if not header_text:
                logger.warning("No header text extracted from paper")
                return {
                    "success": False,
                    "error": "Could not extract header section",
                    "authors": [],
                    "institutions": []
                }
            
            # If we have a title, try to remove it from header to focus on author info
            if paper_title and paper_title in header_text:
                title_end = header_text.find(paper_title) + len(paper_title)
                header_text = header_text[title_end:].strip()
            
            logger.info(f"Extracting authors from header ({len(header_text)} chars)")

            # Call LLM for extraction using LLMManager
            system_prompt = self.prompts.get('system', '')
            user_template = self.prompts.get('user_template', '')
            user_prompt = user_template.format(header_text=header_text)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            try:
                response = self.llm_manager.completion_sync(
                    task_type=self.task_type,
                    messages=messages,
                    user_id=self.user_id
                )
                result = response.choices[0].message.content
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                result = None

            if not result:
                return {
                    "success": False,
                    "error": "LLM extraction failed",
                    "authors": [],
                    "institutions": []
                }
            
            # Parse the LLM response
            author_data = self.parse_llm_response(result)
            
            if not author_data:
                return {
                    "success": False,
                    "error": "Failed to parse LLM response",
                    "authors": [],
                    "institutions": [],
                    "raw_response": result[:500]  # Include partial response for debugging
                }
            
            # Add success flag
            author_data["success"] = True
            
            # Ensure we have the institutions list
            if 'institutions' not in author_data:
                # Extract unique institutions from authors
                institutions = set()
                for author in author_data.get('authors', []):
                    if author.get('affiliation'):
                        institutions.add(author['affiliation'])
                author_data['institutions'] = list(institutions)
            
            logger.info(f"Successfully extracted {len(author_data.get('authors', []))} authors")
            
            return author_data
            
        except Exception as e:
            logger.error(f"Error in author extraction: {e}")
            return {
                "success": False,
                "error": str(e),
                "authors": [],
                "institutions": []
            }
    
    def format_authors_for_display(self, authors: List[Dict[str, Any]]) -> str:
        """
        Format author information for display
        
        Args:
            authors: List of author dictionaries
            
        Returns:
            Formatted string for display
        """
        if not authors:
            return "No authors"
        
        formatted = []
        for author in authors:
            name = author.get('name', 'Unknown')
            affiliation = author.get('affiliation', '')
            dept = author.get('department', '')
            
            if dept and affiliation:
                formatted.append(f"{name} ({dept}, {affiliation})")
            elif affiliation:
                formatted.append(f"{name} ({affiliation})")
            else:
                formatted.append(name)
        
        return ", ".join(formatted)