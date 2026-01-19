"""
Concept Organization Service
Organizes unorganized concepts into the hierarchy or identifies them as aliases.
Uses configuration from llm.json and prompts_config.json
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from pathlib import Path

from app.services.llm_manager import get_llm_manager

logger = logging.getLogger(__name__)


class ConceptOrganizationService:
    """Service for organizing new concepts into the hierarchy"""

    def __init__(self, user_id: str = "default"):
        """Initialize the concept organization service"""
        from app.database.mongodb import get_client, get_database

        self.client = get_client()
        self.db = get_database()
        self.llm_manager = get_llm_manager()
        self.user_id = user_id
        self.task_type = 'concept_organization'

        # Load prompts configuration
        prompts_path = Path(__file__).parent.parent.parent / 'prompts_config.json'
        with open(prompts_path, "r") as f:
            self.prompts_config = json.load(f)
    
    def get_unorganized_concepts(self, limit: int = 50) -> List[Dict]:
        """Get concepts that need organization"""
        # Find concepts that are:
        # 1. Explicitly marked as not organized
        # 2. Marked as needs review
        # 3. Have no parents (orphaned) - regardless of who created them
        # But exclude root categories that have children
        
        # First, get all concepts with no parents
        orphaned = list(self.db.tag_concepts_v2.find(
            {"parents": {"$size": 0}},
            {"_id": 1}
        ))
        
        # Filter out root categories (those with children)
        orphaned_ids = []
        for concept in orphaned:
            children_count = self.db.tag_concepts_v2.count_documents(
                {"parents": concept["_id"]}
            )
            if children_count == 0:
                # This is truly orphaned, not a root category
                orphaned_ids.append(concept["_id"])
        
        # Now get the unorganized concepts
        concepts = list(self.db.tag_concepts_v2.find(
            {"$or": [
                {"is_organized": False},
                {"needs_review": True},
                {"_id": {"$in": orphaned_ids}}  # Include all orphaned concepts
            ]},
            {"_id": 1, "display_name": 1, "slug": 1, "description": 1, "created_at": 1}
        ).limit(limit))
        
        # Convert ObjectId to string for JSON serialization
        for concept in concepts:
            concept["_id"] = str(concept["_id"])
            if "created_at" in concept and hasattr(concept["created_at"], "isoformat"):
                concept["created_at"] = concept["created_at"].isoformat()
        
        return concepts
    
    def get_hierarchy_structure(self) -> str:
        """Get a text representation of the current hierarchy"""
        # Get root concepts
        roots = list(self.db.tag_concepts_v2.find(
            {"parents": [], "is_organized": {"$ne": False}},
            {"_id": 1, "display_name": 1}
        ))
        
        hierarchy_text = []
        for root in roots:
            hierarchy_text.append(f"{root['display_name']} (ID: {root['_id']})")
            # Get children recursively (simplified for brevity)
            children = list(self.db.tag_concepts_v2.find(
                {"parents": root["_id"]},
                {"_id": 1, "display_name": 1}
            ).limit(10))
            for child in children:
                hierarchy_text.append(f"  └─ {child['display_name']} (ID: {child['_id']})")
        
        return "\n".join(hierarchy_text[:100])  # Limit to avoid token overflow
    
    def get_existing_concepts_list(self) -> str:
        """Get a list of existing concepts for alias checking"""
        concepts = list(self.db.tag_concepts_v2.find(
            {"is_organized": {"$ne": False}},
            {"_id": 1, "display_name": 1, "slug": 1}
        ))
        
        concept_list = []
        for c in concepts[:200]:  # Limit to avoid token overflow
            concept_list.append(f"{c['display_name']} (ID: {c['_id']}, slug: {c['slug']})")
        
        return "\n".join(concept_list)
    
    def get_usage_examples(self, concept_id: str) -> str:
        """Get usage examples for a concept"""
        # Convert to ObjectId if needed for tag_instances (they store string IDs)
        # tag_instances uses string concept_id, not ObjectId
        instances = list(self.db.tag_instances.find(
            {"concept_id": str(concept_id) if not isinstance(concept_id, str) else concept_id},
            {"content_type": 1, "content_id": 1}
        ).limit(5))
        
        examples = []
        for inst in instances:
            if inst["content_type"] == "tweet":
                tweet = self.db.tweets.find_one(
                    {"_id": inst["content_id"]},
                    {"text": 1}
                )
                if tweet:
                    examples.append(f"Tweet: {tweet['text'][:100]}...")
            elif inst["content_type"] == "paper":
                paper = self.db.papers.find_one(
                    {"_id": inst["content_id"]},
                    {"title": 1}
                )
                if paper:
                    examples.append(f"Paper: {paper['title']}")
        
        return "\n".join(examples) if examples else "No usage examples found"
    
    async def organize_concept(self, concept_id: str) -> Dict:
        """
        Organize a single concept using LLM
        Returns organization result including whether it's an alias or where to place it
        """
        # Convert string to ObjectId if needed
        try:
            if isinstance(concept_id, str):
                concept_obj_id = ObjectId(concept_id)
            else:
                concept_obj_id = concept_id
        except Exception as e:
            logger.error(f"Invalid concept_id format: {concept_id}")
            return {"success": False, "error": f"Invalid concept ID format: {str(e)}"}
        
        # Get the concept
        concept = self.db.tag_concepts_v2.find_one({"_id": concept_obj_id})
        if not concept:
            return {"error": "Concept not found"}
        
        # Prepare context
        hierarchy_structure = self.get_hierarchy_structure()
        existing_concepts = self.get_existing_concepts_list()
        usage_examples = self.get_usage_examples(concept_id)
        
        # Get prompt configuration
        prompt_config = self.prompts_config.get("concept_organization", {})
        
        # Format the prompt (escape braces in data to avoid format conflicts)
        safe_hierarchy = hierarchy_structure.replace('{', '{{').replace('}', '}}')
        safe_concepts = existing_concepts.replace('{', '{{').replace('}', '}}')
        safe_examples = usage_examples.replace('{', '{{').replace('}', '}}')
        
        user_prompt = prompt_config["user_template"].format(
            concept_name=concept["display_name"],
            description=concept.get("description", "No description available"),
            usage_examples=safe_examples,
            hierarchy_structure=safe_hierarchy,
            existing_concepts=safe_concepts
        )
        
        # Call LLM using LLMManager
        try:
            # Prepare messages in OpenAI format
            messages = [
                {"role": "system", "content": prompt_config['system']},
                {"role": "user", "content": user_prompt}
            ]

            # Call LLM Manager async
            response = await self.llm_manager.completion(
                task_type=self.task_type,
                messages=messages,
                user_id=self.user_id
            )

            result = response.choices[0].message.content
            logger.info(f"LLM response for concept {concept_id}: {result}")
            
            # Extract JSON from response using robust extraction
            organization = self._extract_json_from_response(result)
            
            if not organization:
                raise ValueError("Could not extract valid JSON from LLM response")
            
            return {
                "concept_id": str(concept_obj_id),
                "concept_name": concept["display_name"],
                "organization": organization,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error organizing concept {concept_id}: {e}")
            return {
                "concept_id": str(concept_obj_id),
                "concept_name": concept["display_name"],
                "error": str(e),
                "success": False
            }
    
    async def apply_organization(self, concept_id: str, organization: Dict) -> bool:
        """Apply the organization decision to the database"""
        try:
            # Convert string to ObjectId if needed
            if isinstance(concept_id, str):
                concept_obj_id = ObjectId(concept_id)
            else:
                concept_obj_id = concept_id
            
            if organization.get("is_alias"):
                # This is an alias - add to aliases collection
                alias_of = organization["alias_of"]
                if alias_of:
                    self.db.tag_aliases_v2.insert_one({
                        "alias": self.db.tag_concepts_v2.find_one({"_id": concept_obj_id})["display_name"],
                        "concept_id": alias_of,
                        "created_at": datetime.now(),
                        "created_by": "concept_organizer"
                    })
                    
                    # Update all instances to point to the main concept
                    self.db.tag_instances.update_many(
                        {"concept_id": str(concept_obj_id)},
                        {"$set": {"concept_id": alias_of}}
                    )
                    
                    # Remove the duplicate concept
                    self.db.tag_concepts_v2.delete_one({"_id": concept_obj_id})
                    
                    logger.info(f"Concept {concept_id} identified as alias of {alias_of}")
                    return True
            
            else:
                # Update the concept with parent relationships
                update_doc = {
                    "parents": organization.get("parent_concepts", []),
                    "entity_type": organization.get("entity_type", "other"),
                    "is_organized": True,
                    "needs_review": False,
                    "organization_updated_at": datetime.now(),
                    "organized_by": "concept_organizer"
                }
                
                if organization.get("description"):
                    update_doc["description"] = organization["description"]
                
                self.db.tag_concepts_v2.update_one(
                    {"_id": concept_obj_id},
                    {"$set": update_doc}
                )
                
                logger.info(f"Concept {concept_id} organized with parents: {organization.get('parent_concepts')}")
                return True
                
        except Exception as e:
            logger.error(f"Error applying organization for {concept_id}: {e}")
            return False
    
    async def organize_batch(self, limit: int = 10, auto_apply: bool = False) -> List[Dict]:
        """
        Organize a batch of unorganized concepts
        
        Args:
            limit: Number of concepts to organize
            auto_apply: If True, automatically apply the organization
        
        Returns:
            List of organization results
        """
        unorganized = self.get_unorganized_concepts(limit)
        results = []
        
        for concept in unorganized:
            logger.info(f"Organizing concept: {concept['display_name']}")
            result = await self.organize_concept(concept["_id"])
            
            if result.get("success") and auto_apply:
                applied = await self.apply_organization(
                    concept["_id"],
                    result["organization"]
                )
                result["applied"] = applied
            
            results.append(result)
        
        return results
    
    def _extract_json_from_response(self, text: str) -> Optional[Dict]:
        """
        Extract JSON from LLM response, handling markdown code blocks and mixed content
        """
        import re
        import json
        
        try:
            # Strategy 1: Look for ```json specifically
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text, re.IGNORECASE | re.MULTILINE)
            if json_match:
                json_content = json_match.group(1).strip()
                try:
                    return json.loads(json_content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Found ```json block but failed to parse: {e}")
            
            # Strategy 2: Look for any ``` code block that might contain JSON
            code_matches = re.findall(r'```(?:\w+)?\s*([\s\S]*?)\s*```', text, re.MULTILINE)
            for code_content in code_matches:
                code_content = code_content.strip()
                # Check if it looks like JSON (starts with { or [)
                if code_content.startswith(('{', '[')):
                    try:
                        return json.loads(code_content)
                    except json.JSONDecodeError:
                        continue
            
            # Strategy 3: Look for JSON object in the text (fallback)
            # Find the largest JSON-like structure
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    # Clean up common issues
                    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)  # Remove trailing commas
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # Strategy 4: Direct JSON parse (if response is pure JSON)
            try:
                return json.loads(text.strip())
            except json.JSONDecodeError:
                pass
            
            logger.error(f"All JSON extraction strategies failed for response: {text[:200]}...")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting JSON from response: {e}")
            return None


# Utility function for testing
async def test_organization():
    """Test the concept organization service"""
    service = ConceptOrganizationService()
    
    # Get unorganized concepts
    unorganized = service.get_unorganized_concepts(5)
    print(f"Found {len(unorganized)} unorganized concepts")
    
    if unorganized:
        # Test organizing the first one
        concept = unorganized[0]
        print(f"\nTesting organization for: {concept['display_name']}")
        
        result = await service.organize_concept(concept["_id"])
        print(f"Result: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            print(f"\nOrganization suggestion:")
            org = result["organization"]
            if org.get("is_alias"):
                print(f"  - This is an alias of: {org['alias_of']}")
            else:
                print(f"  - Parent concepts: {org.get('parent_concepts')}")
                print(f"  - Entity type: {org.get('entity_type')}")
                print(f"  - Description: {org.get('description')}")
            print(f"  - Reasoning: {org.get('reasoning')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_organization())
