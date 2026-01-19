"""
AI-powered ontology suggestions using LLM Manager
Migrated to use unified LLM Manager with LiteLLM
"""
import json
import os
from typing import List, Dict, Optional, Tuple, Any
from dotenv import load_dotenv
from pydantic import BaseModel

from app.services.llm_manager import get_llm_manager

class OntologySuggestion(BaseModel):
    """Model for ontology suggestions"""
    synonyms: List[Dict[str, str]]  # [{"concept": "llm", "synonym": "language-model"}]
    hierarchies: List[Dict[str, str]]  # [{"child": "gpt-5", "parent": "gpt"}]
    same_as: List[Dict[str, Any]]  # [{"canonical": "llm", "alternatives": ["LLM", "large-language-model"]}]
    reasoning: str

class OntologyAIService:
    """Service for AI-powered ontology management"""

    def __init__(self, user_id: str = "default"):
        """Initialize with LLM Manager"""
        # Load environment variables
        load_dotenv()

        # Initialize LLM Manager
        self.llm_manager = get_llm_manager()
        self.user_id = user_id

        # Task types from litellm_config.yaml
        self.task_type_suggestion = 'ontology_suggestion'
        self.task_type_validation = 'ontology_validation'
        self.task_type_bulk = 'ontology_bulk'

        # Load prompts configuration
        with open('prompts_config.json', 'r') as f:
            self.prompts = json.load(f)

        # Get model attribution for suggestion task
        task_info = self.llm_manager.get_task_info(self.task_type_suggestion)
        self.model_name = task_info['model'] if task_info else 'unknown'
    
    def analyze_tag_relationships(self, db: Session, tag: str) -> OntologySuggestion:
        """
        Analyze a tag and suggest ontology relationships
        """
        # Get context about existing ontology
        existing_concepts = db.query(TagConcept).all()
        concept_names = {c.tag: c.display_name for c in existing_concepts}
        
        # Get sample tweets with this tag
        sample_tweets = db.query(Tag.tweet_id, Tag.tag).filter(
            Tag.tag == tag
        ).limit(5).all()
        
        # Build context
        ontology_context = self._build_ontology_context(existing_concepts)
        
        # Create prompt
        ontology_prompt_config = self.prompts.get('ontology_system', {})
        if not ontology_prompt_config:
            raise ValueError("ontology_system prompt not found in prompts_config.json")
        
        # Extract system and user template from the config
        system_prompt = ontology_prompt_config.get('system', '')
        user_template = ontology_prompt_config.get('user_template', '')
        
        if not system_prompt or not user_template:
            raise ValueError("ontology_system prompt is missing 'system' or 'user_template' keys")
        
        # Format the user prompt with the template
        user_prompt = user_template.format(
            ontology_context=ontology_context,
            tags=f"['{tag}']"  # Format as list for consistency
        )
        
        # Convert to OpenAI message format
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            print(f"Sending messages to LLM for tag: {tag}")
            print(f"System message: {messages[0]['content'][:200]}...")
            print(f"User message: {messages[1]['content'][:200]}...")

            # Call LLM Manager
            response = self.llm_manager.completion_sync(
                task_type=self.task_type_suggestion,
                messages=messages,
                user_id=self.user_id
            )

            print(f"Raw response type: {type(response)}")
            print(f"Raw response: {response}")

            # Extract content from LiteLLM response
            content = response.choices[0].message.content
            print(f"Response content type: {type(content)}")
            print(f"Response content: {content}")
            
            # Clean up the response if needed
            if isinstance(content, str):
                # Remove any markdown code blocks
                original_content = content
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                    print(f"Extracted from ```json block")
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
                    print(f"Extracted from ``` block")
                
                # Strip whitespace
                content = content.strip()
                
                # Try to parse as JSON
                try:
                    result_dict = json.loads(content)
                    print(f"Successfully parsed JSON: {result_dict}")
                    
                    # Create OntologySuggestion from dict
                    return OntologySuggestion(
                        synonyms=result_dict.get('synonyms', []),
                        hierarchies=result_dict.get('hierarchies', []),
                        same_as=result_dict.get('same_as', []),
                        reasoning=result_dict.get('reasoning', 'AI analysis completed')
                    )
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Content was: {content}")
                    print(f"Original content was: {original_content[:500]}...")
                    # Return basic suggestions instead of trying parser
                    return OntologySuggestion(
                        synonyms=[],
                        hierarchies=[],
                        same_as=[],
                        reasoning="Could not parse AI response - using basic analysis"
                    )
            else:
                # If response is not a string, try to extract content
                try:
                    content_str = str(response.content) if hasattr(response, 'content') else str(response)
                    content_str = content_str.strip()
                    result_dict = json.loads(content_str)
                    return OntologySuggestion(
                        synonyms=result_dict.get('synonyms', []),
                        hierarchies=result_dict.get('hierarchies', []),
                        same_as=result_dict.get('same_as', []),
                        reasoning=result_dict.get('reasoning', 'AI analysis completed')
                    )
                except:
                    return OntologySuggestion(
                        synonyms=[],
                        hierarchies=[],
                        same_as=[],
                        reasoning="Could not parse AI response"
                    )
                
        except Exception as e:
            print(f"Error in AI analysis: {str(e)}")
            # Fallback suggestions
            return OntologySuggestion(
                synonyms=[],
                hierarchies=self._suggest_basic_hierarchy(tag, concept_names),
                same_as=self._suggest_basic_sameas(tag),
                reasoning=f"Basic suggestions (AI error: {str(e)[:100]})"
            )
    
    def suggest_bulk_organization(self, db: Session, uncategorized_limit: int = 20) -> Dict:
        """
        Suggest organization for multiple uncategorized tags
        Uses random selection and tracks processed tags to avoid repetition
        """
        import os
        import json
        from datetime import datetime, timedelta
        
        # Track processed tags in a JSON file
        processed_file = 'data/processed_bulk_tags.json'
        processed_tags = set()
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Load previously processed tags (with expiry after 24 hours)
        if os.path.exists(processed_file):
            try:
                with open(processed_file, 'r') as f:
                    processed_data = json.load(f)
                    # Check if data is recent (within 24 hours)
                    if 'timestamp' in processed_data:
                        timestamp = datetime.fromisoformat(processed_data['timestamp'])
                        if datetime.now() - timestamp < timedelta(hours=24):
                            processed_tags = set(processed_data.get('tags', []))
                        else:
                            # Reset if older than 24 hours
                            print("Resetting processed tags (older than 24 hours)")
                            processed_tags = set()
            except Exception as e:
                print(f"Error loading processed tags: {e}")
                processed_tags = set()
        
        # Get uncategorized concepts excluding already processed ones
        query = db.query(TagConcept).filter(
            TagConcept.parent_id.is_(None),
            TagConcept.description == "Auto-imported from existing tags"
        )
        
        # Filter out already processed tags
        if processed_tags:
            query = query.filter(~TagConcept.tag.in_(processed_tags))
            print(f"Excluding {len(processed_tags)} already processed tags")
        
        # Use random ordering to get different batches each time
        uncategorized = query.order_by(func.random()).limit(uncategorized_limit).all()
        
        # If we've processed everything or not enough new tags, reset and start over
        if len(uncategorized) < min(5, uncategorized_limit):
            print(f"Only {len(uncategorized)} unprocessed tags found. Resetting processed tags list.")
            processed_tags = set()
            # Query again without the filter, still with random order
            uncategorized = db.query(TagConcept).filter(
                TagConcept.parent_id.is_(None),
                TagConcept.description == "Auto-imported from existing tags"
            ).order_by(func.random()).limit(uncategorized_limit).all()
        
        # Add current batch to processed tags
        new_processed = processed_tags.copy()
        for concept in uncategorized:
            new_processed.add(concept.tag)
        
        # Save updated processed tags list
        try:
            with open(processed_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'tags': list(new_processed)
                }, f, indent=2)
            print(f"Saved {len(new_processed)} processed tags to tracking file")
        except Exception as e:
            print(f"Error saving processed tags: {e}")
        
        print(f"Selected {len(uncategorized)} uncategorized tags for bulk organization")
        
        if not uncategorized:
            return {"message": "No uncategorized tags found", "suggestions": []}
        
        existing_concepts = db.query(TagConcept).filter(
            TagConcept.description != "Auto-imported from existing tags"
        ).all()
        
        ontology_context = self._build_ontology_context(existing_concepts)

        # Use bulk task type (configured in litellm_config.yaml)
        bulk_prompt_config = self.prompts.get('ontology_bulk_organization', {})
        system_prompt = bulk_prompt_config.get('system', '')
        user_template = bulk_prompt_config.get('user_template', '')
        
        if not system_prompt:
            raise ValueError("ontology_bulk_organization system prompt not found in prompts_config.json")
        
        uncategorized_tags = [{"tag": c.tag, "display_name": c.display_name} for c in uncategorized]
        
        # Use the user_template if available, otherwise use the hardcoded prompt
        if not user_template:
            # User template is required - no fallback allowed
            raise ValueError("ontology_bulk_organization.user_template not configured in prompts_config.json")
        
        user_prompt = user_template.format(
            ontology_context=ontology_context,
            tags=json.dumps(uncategorized_tags, indent=2)
        )

        # Convert to OpenAI message format
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # Call LLM Manager with bulk task type
            response = self.llm_manager.completion_sync(
                task_type=self.task_type_bulk,
                messages=messages,
                user_id=self.user_id
            )

            # Extract content from LiteLLM response
            content = response.choices[0].message.content
            
            # Clean up JSON if in markdown blocks
            if isinstance(content, str):
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
            
            result = json.loads(content)
            return result
        except Exception as e:
            return {
                "message": f"AI suggestion failed: {str(e)}",
                "suggestions": []
            }
    
    def validate_relationship(self, db: Session, relationship_type: str, 
                            source: str, target: str) -> Dict:
        """
        Validate if a proposed relationship makes sense
        """
        validation_prompts = self.prompts.get('ontology_validation', {})
        system_prompt = validation_prompts.get('system', '')
        user_template = validation_prompts.get('user_template', '')
        
        if not system_prompt or not user_template:
            raise ValueError("ontology_validation prompts not found in prompts_config.json")
        
        user_prompt = user_template.format(
            relationship_type=relationship_type,
            source=source,
            target=target
        )

        try:
            # Convert to OpenAI message format
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Call LLM Manager with validation task type
            response = self.llm_manager.completion_sync(
                task_type=self.task_type_validation,
                messages=messages,
                user_id=self.user_id
            )

            content = response.choices[0].message.content
            return json.loads(content)
        except:
            return {
                "valid": True,
                "confidence": 0.5,
                "reasoning": "Could not validate with AI",
                "alternative": None
            }
    
    def _build_ontology_context(self, concepts: List[TagConcept]) -> str:
        """Build a string representation of the ontology structure"""
        # Group by level
        by_level = {}
        for c in concepts:
            if c.level not in by_level:
                by_level[c.level] = []
            by_level[c.level].append(c)
        
        lines = []
        for level in sorted(by_level.keys()):
            if level == 0:
                lines.append("Root concepts:")
            else:
                lines.append(f"Level {level}:")
            
            for concept in by_level[level]:
                indent = "  " * level
                syn_text = f" (synonyms: {', '.join([s.synonym_tag for s in concept.synonyms])})" if concept.synonyms else ""
                lines.append(f"{indent}- {concept.display_name} [{concept.tag}]{syn_text}")
        
        return "\n".join(lines)
    
    def _suggest_basic_hierarchy(self, tag: str, existing: Dict[str, str]) -> List[Dict[str, str]]:
        """Basic hierarchy suggestions without AI"""
        suggestions = []
        tag_lower = tag.lower()
        
        # Common patterns
        if 'gpt' in tag_lower and 'gpt' in existing:
            suggestions.append({"child": tag, "parent": "gpt"})
        elif 'llm' in tag_lower or 'language' in tag_lower:
            if 'llm' in existing:
                suggestions.append({"child": tag, "parent": "llm"})
        elif 'ai' in tag_lower or 'ml' in tag_lower:
            if 'ai-tools' in existing:
                suggestions.append({"child": tag, "parent": "ai-tools"})
        elif any(company in tag_lower for company in ['openai', 'anthropic', 'google', 'microsoft']):
            if 'ai-companies' in existing:
                suggestions.append({"child": tag, "parent": "ai-companies"})
        
        return suggestions
    
    def _suggest_basic_sameas(self, tag: str) -> List[Dict[str, List[str]]]:
        """Basic same-as suggestions without AI"""
        suggestions = []
        
        # Common variations
        variations = []
        
        # Handle underscores and hyphens
        if '_' in tag:
            variations.append(tag.replace('_', '-'))
        if '-' in tag:
            variations.append(tag.replace('-', '_'))
        
        # Handle case variations
        if tag.lower() != tag:
            variations.append(tag.lower())
        if tag.upper() != tag:
            variations.append(tag.upper())
        
        # Common abbreviations
        abbreviations = {
            'artificial-intelligence': ['ai'],
            'machine-learning': ['ml'],
            'deep-learning': ['dl'],
            'natural-language-processing': ['nlp'],
            'computer-vision': ['cv'],
            'large-language-model': ['llm'],
        }
        
        for full, abbrevs in abbreviations.items():
            if tag.lower() == full:
                variations.extend(abbrevs)
            elif tag.lower() in abbrevs:
                variations.append(full)
        
        if variations:
            suggestions.append({
                "canonical": tag,
                "alternatives": list(set(variations))
            })
        
        return suggestions

class OntologyProposalService:
    """Service for managing ontology proposals"""

    def __init__(self, db: Session, user_id: str = "default"):
        self.db = db
        self.user_id = user_id
        self.ai_service = OntologyAIService(user_id=user_id)
    
    def generate_proposals_for_tag(self, tag: str) -> Dict:
        """Generate comprehensive proposals for a single tag"""
        suggestions = self.ai_service.analyze_tag_relationships(self.db, tag)
        
        # Convert to actionable proposals
        proposals = {
            "tag": tag,
            "proposals": []
        }
        
        # Add synonym proposals (filter out existing ones)
        for syn in suggestions.synonyms:
            synonym_tag = syn['synonym']
            # Check if synonym already exists
            existing_synonym = self.db.query(TagSynonym).filter(
                TagSynonym.synonym_tag == synonym_tag
            ).first()
            # Check if it's already a concept
            existing_concept = self.db.query(TagConcept).filter(
                TagConcept.tag == synonym_tag
            ).first()
            
            if not existing_synonym and not existing_concept:
                proposals["proposals"].append({
                    "type": "add_synonym",
                    "action": f"Add '{syn['synonym']}' as synonym to '{syn['concept']}'",
                    "details": syn
                })
        
        # Add hierarchy proposals  
        for hier in suggestions.hierarchies:
            proposals["proposals"].append({
                "type": "set_hierarchy",
                "action": f"Place '{hier['child']}' under '{hier['parent']}'",
                "details": hier
            })
        
        # Add same-as proposals (filter out existing ones)
        for same in suggestions.same_as:
            for alt in same['alternatives']:
                # Check if synonym already exists
                existing_synonym = self.db.query(TagSynonym).filter(
                    TagSynonym.synonym_tag == alt
                ).first()
                # Check if it's already a concept
                existing_concept = self.db.query(TagConcept).filter(
                    TagConcept.tag == alt
                ).first()
                
                if not existing_synonym and not existing_concept:
                    proposals["proposals"].append({
                        "type": "add_sameas",
                        "action": f"Mark '{alt}' as same as '{same['canonical']}'",
                        "details": {"canonical": same['canonical'], "alternative": alt}
                    })
        
        proposals["reasoning"] = suggestions.reasoning
        
        return proposals
    
    def generate_bulk_proposals(self, limit: int = 20) -> Dict:
        """Generate proposals for organizing uncategorized tags"""
        return self.ai_service.suggest_bulk_organization(self.db, limit)
    
    def apply_proposal(self, proposal: Dict) -> Dict:
        """Apply a single proposal to the ontology"""
        try:
            if proposal['type'] == 'add_synonym':
                from sqlalchemy import or_
                concept = self.db.query(TagConcept).filter(
                    or_(
                        TagConcept.tag == proposal['details']['concept'],
                        TagConcept.display_name == proposal['details']['concept']
                    )
                ).first()
                if concept:
                    # Check if synonym already exists
                    synonym_tag = proposal['details']['synonym']
                    existing_synonym = self.db.query(TagSynonym).filter(
                        TagSynonym.synonym_tag == synonym_tag
                    ).first()
                    
                    if existing_synonym:
                        if existing_synonym.concept_id == concept.id:
                            return {"success": False, "message": f"Synonym '{synonym_tag}' already exists for this concept"}
                        else:
                            existing_concept = self.db.query(TagConcept).filter(
                                TagConcept.id == existing_synonym.concept_id
                            ).first()
                            return {"success": False, "message": f"Synonym '{synonym_tag}' already exists for concept '{existing_concept.display_name}'"}
                    
                    # Check if it's already a concept tag
                    existing_concept = self.db.query(TagConcept).filter(
                        TagConcept.tag == synonym_tag
                    ).first()
                    if existing_concept:
                        return {"success": False, "message": f"'{synonym_tag}' already exists as a concept"}
                    
                    synonym = TagSynonym(
                        concept_id=concept.id,
                        synonym_tag=synonym_tag
                    )
                    self.db.add(synonym)
                    self.db.commit()
                    return {"success": True, "message": "Synonym added"}
                return {"success": False, "message": f"Concept '{proposal['details']['concept']}' not found"}
            
            elif proposal['type'] == 'set_hierarchy':
                # Try to find child by tag or display_name
                from sqlalchemy import or_
                child = self.db.query(TagConcept).filter(
                    or_(
                        TagConcept.tag == proposal['details']['child'],
                        TagConcept.display_name == proposal['details']['child']
                    )
                ).first()
                
                # Try to find parent by tag or display_name
                parent = self.db.query(TagConcept).filter(
                    or_(
                        TagConcept.tag == proposal['details']['parent'],
                        TagConcept.display_name == proposal['details']['parent']
                    )
                ).first()
                
                if child and parent:
                    child.parent_id = parent.id
                    child.update_path(self.db)
                    self.db.commit()
                    return {"success": True, "message": "Hierarchy updated"}
                
                # Provide more detailed error message
                if not child and not parent:
                    return {"success": False, "message": f"Both '{proposal['details']['child']}' and '{proposal['details']['parent']}' not found"}
                elif not child:
                    return {"success": False, "message": f"Child concept '{proposal['details']['child']}' not found"}
                else:
                    return {"success": False, "message": f"Parent concept '{proposal['details']['parent']}' not found"}
            
            elif proposal['type'] == 'add_sameas':
                from sqlalchemy import or_
                concept = self.db.query(TagConcept).filter(
                    or_(
                        TagConcept.tag == proposal['details']['canonical'],
                        TagConcept.display_name == proposal['details']['canonical']
                    )
                ).first()
                if concept:
                    # Check if synonym already exists
                    synonym_tag = proposal['details']['alternative']
                    existing_synonym = self.db.query(TagSynonym).filter(
                        TagSynonym.synonym_tag == synonym_tag
                    ).first()
                    
                    if existing_synonym:
                        if existing_synonym.concept_id == concept.id:
                            return {"success": False, "message": f"Alternative '{synonym_tag}' already exists for this concept"}
                        else:
                            existing_concept = self.db.query(TagConcept).filter(
                                TagConcept.id == existing_synonym.concept_id
                            ).first()
                            return {"success": False, "message": f"Alternative '{synonym_tag}' already exists for concept '{existing_concept.display_name}'"}
                    
                    # Check if it's already a concept tag
                    existing_concept = self.db.query(TagConcept).filter(
                        TagConcept.tag == synonym_tag
                    ).first()
                    if existing_concept:
                        return {"success": False, "message": f"'{synonym_tag}' already exists as a concept"}
                    
                    synonym = TagSynonym(
                        concept_id=concept.id,
                        synonym_tag=synonym_tag
                    )
                    self.db.add(synonym)
                    self.db.commit()
                    return {"success": True, "message": "Same-as relation added"}
                return {"success": False, "message": f"Canonical concept '{proposal['details']['canonical']}' not found"}
            
            return {"success": False, "message": "Unknown proposal type"}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": str(e)}