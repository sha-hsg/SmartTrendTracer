"""
GPT-5 Enhanced Tag Reorganization Service
Uses GPT-5's 400K context window and 128K output capability
for comprehensive tag reorganization with full backwards compatibility
"""

import json
import logging
import os
import re
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# Directory for storing GPT-5 responses
RESPONSE_LOG_DIR = Path('data/gpt5_responses')
RESPONSE_LOG_DIR.mkdir(parents=True, exist_ok=True)

class GPT5TagReorganizer:
    """
    GPT-5 powered tag reorganization with comprehensive canonicalization,
    aliasing, and hierarchy management
    """
    
    def __init__(self, model_override: Optional[str] = None):
        self.llm_service = LLMService()
        self.model_override = model_override
        
        # Load configurations
        with open('prompts_config.json', 'r') as f:
            prompts_config = json.load(f)
            # Use tag_reorganization prompt which includes top_level_json placeholder
            self.prompts = prompts_config.get('tag_reorganization', {})
        
        with open('llm.json', 'r') as f:
            llm_config = json.load(f)
            
            # Check if we should use GPT-5 instead of Gemini
            if model_override == 'gpt5':
                # Use the actual GPT-5 config
                self.model_config = {
                    "model": "gpt-5-2025-08-07",
                    "provider": "openai",
                    "temperature": 1,  # GPT-5 requires temperature=1
                    "max_tokens": 100000,
                    "is_reasoning": False
                }
            else:
                # Default to the configured model (Gemini)
                self.model_config = llm_config['models'].get('tag_reorganization_comprehensive')
        
        # Load top-level ontology schema
        self.top_level_json = None
        try:
            # Try current directory first, then parent directory
            import os
            if os.path.exists('top_level.json'):
                path = 'top_level.json'
            elif os.path.exists('../top_level.json'):
                path = '../top_level.json'
            else:
                path = 'top_level.json'  # Fallback
                
            with open(path, 'r') as f:
                self.top_level_json = json.dumps(json.load(f), indent=2)
                logger.info(f"Loaded top_level.json from {path} for entity type schema")
        except Exception as e:
            logger.warning(f"Could not load top_level.json: {e}")
            self.top_level_json = "{}"  # Empty fallback
            
        logger.info(f"Initialized reorganizer with model: {self.model_config.get('model')}")
    
    def reorganize_tags_with_debug(self, tags_data: List[Dict[str, Any]], progress_callback: Optional[Callable] = None) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Wrapper for reorganize_tags that also returns debug info
        """
        # Store debug info
        debug_info = {}
        
        # Call the original method and capture debug info
        result = self._reorganize_tags_internal(tags_data, progress_callback, debug_info)
        
        return result, debug_info
    
    def reorganize_tags(self, tags_data: List[Dict[str, Any]], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Original method for backwards compatibility
        """
        debug_info = {}
        return self._reorganize_tags_internal(tags_data, progress_callback, debug_info)
    
    def _reorganize_tags_internal(self, tags_data: List[Dict[str, Any]], progress_callback: Optional[Callable], debug_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use GPT-5 to reorganize all tags into a comprehensive taxonomy
        
        Args:
            tags_data: List of tag dictionaries with 'id', 'tag', 'display_name', 'count', 
                      'entity_type', and 'current_parents' fields
            debug_info: Dict to store debug information (prompts, etc.)
            
        Returns:
            Complete reorganization result from GPT-5
        """
        try:
            logger.info(f"Starting reorganization of {len(tags_data)} tags using {self.model_config.get('model', 'unknown model')}")
            
            # Enhanced debug logging
            debug_info['input_stats'] = {
                'total_concepts': len(tags_data),
                'organized': sum(1 for t in tags_data if t.get('current_parents')),
                'unorganized': sum(1 for t in tags_data if not t.get('current_parents')),
                'auto_generated': sum(1 for t in tags_data if t.get('auto_generated')),
                'manual': sum(1 for t in tags_data if not t.get('auto_generated'))
            }
            
            logger.info(f"[DEBUG] Input Statistics:")
            logger.info(f"  - Total concepts: {debug_info['input_stats']['total_concepts']}")
            logger.info(f"  - Organized: {debug_info['input_stats']['organized']}")
            logger.info(f"  - Unorganized: {debug_info['input_stats']['unorganized']}")
            logger.info(f"  - Auto-generated: {debug_info['input_stats']['auto_generated']}")
            logger.info(f"  - Manual: {debug_info['input_stats']['manual']}")
            
            # Log the structure we're receiving
            if tags_data and len(tags_data) > 0:
                sample = tags_data[0]
                logger.info(f"Sample tag data structure: {list(sample.keys())}")
                debug_info['sample_input'] = sample
                if 'id' in sample:
                    logger.info(f"Tags include IDs for proper mapping back to database")
            
            # Prepare the tags for GPT-5 in compact format
            # Option 1: Super compact - just essential fields, no indentation
            compact_tags = []
            for tag in tags_data:
                # Only include non-empty fields to save tokens
                compact_tag = {
                    'id': tag['id'],
                    't': tag['tag'],  # Shortened key
                    'd': tag['display_name'],  # Shortened key
                    'c': tag['count'],  # Shortened key
                }
                if tag.get('entity_type'):
                    compact_tag['e'] = tag['entity_type']  # Shortened key
                if tag.get('current_parents'):
                    compact_tag['p'] = tag['current_parents']  # Shortened key
                compact_tags.append(compact_tag)
            
            # Use compact JSON without indentation
            tags_json_compact = json.dumps(compact_tags, separators=(',', ':'))
            
            # Also prepare a readable version for debugging
            tags_json_readable = json.dumps(tags_data, indent=2)
            
            # Use compact version for sending, readable for logging
            tags_json = tags_json_compact
            
            # Check context size
            estimated_tokens = len(tags_json) // 4  # Rough estimate
            logger.info(f"Compact format: {len(tags_json_compact)} chars vs Original: {len(tags_json_readable)} chars (saved {100 - (len(tags_json_compact) * 100 // len(tags_json_readable))}%)")
            logger.info(f"Estimated input tokens: {estimated_tokens} (using {self.model_config.get('model', 'unknown')} with max_tokens={self.model_config.get('max_tokens', 'unset')})")
            
            if estimated_tokens > 500000:  # Models like Claude Opus can handle 700k+ tokens
                logger.warning(f"Input is very large ({estimated_tokens} tokens). Ensure your model can handle this.")
                logger.info("Sending all concepts in single request for complete context...")
            
            # Calculate statistics for prompt
            total_taggings = sum(tag.get('count', 0) for tag in tags_data)
            average_usage = total_taggings / len(tags_data) if tags_data else 0
            
            # Prepare prompts
            system_prompt = self.prompts.get('system', '')
            
            # Use string replacement instead of format() to avoid issues with JSON braces
            user_prompt = self.prompts.get('user_template', '')
            user_prompt = user_prompt.replace('{total_tags}', str(len(tags_data)))
            user_prompt = user_prompt.replace('{tags_json}', tags_json)
            user_prompt = user_prompt.replace('{top_level_json}', self.top_level_json)
            user_prompt = user_prompt.replace('{total_taggings}', str(total_taggings))
            user_prompt = user_prompt.replace('{average_usage}', f"{average_usage:.1f}")
            
            # Store prompts in debug info
            debug_info['system_prompt'] = system_prompt
            debug_info['prompt'] = user_prompt
            debug_info['prompt_size'] = len(user_prompt)
            debug_info['system_prompt_size'] = len(system_prompt)
            debug_info['estimated_tokens'] = estimated_tokens
            
            logger.info(f"Calling {self.model_config.get('model', 'unknown model')} for comprehensive reorganization...")
            logger.info(f"[DEBUG] User prompt size: {len(user_prompt)} characters, System prompt size: {len(system_prompt)} characters")
            
            # Call GPT-5 with the full tag list (with progress updates)
            result_text = self._call_gpt5(system_prompt, user_prompt, progress_callback=progress_callback, tags_count=len(tags_data))
            
            if not result_text:
                logger.error("GPT-5 returned empty response")
                return self._fallback_reorganization(tags_data)
            
            # Parse the JSON response (handle markdown and comments)
            try:
                # First try to extract JSON from markdown code blocks if present
                json_result = self._extract_json_from_markdown(result_text)
                if json_result:
                    result = json_result
                else:
                    # Remove C-style comments that may cause JSON parsing to fail
                    clean_text = re.sub(r'/\*.*?\*/', '', result_text, flags=re.DOTALL)
                    result = json.loads(clean_text)
                
                # Enhanced debug output
                debug_info['output_stats'] = {
                    'concepts_returned': len(result.get('concepts', [])),
                    'aliases_returned': len(result.get('aliases', [])),
                    'merge_proposals': len(result.get('merge_proposals', [])),
                    'response_size': len(result_text)
                }
                
                logger.info(f"[DEBUG] Output Statistics:")
                logger.info(f"  - Concepts returned: {debug_info['output_stats']['concepts_returned']}")
                logger.info(f"  - Aliases returned: {debug_info['output_stats']['aliases_returned']}")
                logger.info(f"  - Merge proposals: {debug_info['output_stats']['merge_proposals']}")
                logger.info(f"  - Response size: {debug_info['output_stats']['response_size']} characters")
                
                # Validate the result
                validation = self._validate_gpt5_result(result, tags_data)
                result['validation'] = validation
                debug_info['validation'] = validation
                
                # Add metadata
                result['metadata'] = {
                    'model': self.model_config.get('model'),
                    'timestamp': datetime.utcnow().isoformat(),
                    'input_tags': len(tags_data),
                    'estimated_tokens': estimated_tokens,
                    'debug_info': debug_info
                }
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT-5 response as JSON: {e}")
                # Try to extract JSON from the response
                result = self._extract_json_from_text(result_text)
                if result:
                    return result
                return self._fallback_reorganization(tags_data)
                
        except Exception as e:
            import traceback
            logger.error(f"Error in GPT-5 reorganization: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._fallback_reorganization(tags_data)
    
    def _call_gpt5(self, system_prompt: str, user_prompt: str, progress_callback: Optional[Callable] = None, tags_count: int = 0) -> Optional[str]:
        """
        Call GPT-5 through the LLM service with retry status updates
        """
        retry_count = 0
        max_retries = 5
        
        while retry_count <= max_retries:
            try:
                if retry_count > 0:
                    retry_msg = f"Retry attempt {retry_count} of {max_retries} for GPT-5 request"
                    logger.info(retry_msg)
                    if progress_callback:
                        progress_callback(retry_msg)
                
                # Use the LLM service's LangChain integration
                from langchain_core.messages import HumanMessage, SystemMessage
                
                # Get the LangChain client configured for GPT-5
                client = self.llm_service._get_client(self.model_config)
                
                if client is None:
                    logger.error("Could not get GPT-5 client")
                    return None
                
                # Prepare messages
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                
                logger.info(f"Sending request to {self.model_config.get('model', 'LLM')}...")
                logger.info(f"Request timeout set to 1 hour for GPT-5")
                if progress_callback:
                    progress_callback(f"Processing {tags_count} concepts with {self.model_config.get('model', 'GPT-5')} (may take 5-15 minutes)...")
                
                # Call GPT-5 with extended timeout
                response = client.invoke(messages)
                
                # Extract content from response
                if hasattr(response, 'content'):
                    result_text = response.content
                else:
                    result_text = str(response)
                
                # Save raw response to file
                self._save_response_to_file(result_text, 'success')
                return result_text
                
            except Exception as e:
                error_msg = f"Error calling GPT-5 (attempt {retry_count + 1}): {e}"
                logger.error(error_msg)
                
                # Check for specific error types
                if '502' in str(e) or '503' in str(e) or 'Bad Gateway' in str(e):
                    if progress_callback:
                        progress_callback(f"OpenAI server error (502/503), retrying...")
                elif 'timeout' in str(e).lower():
                    logger.warning(f"GPT-5 timed out on attempt {retry_count + 1}")
                    if progress_callback:
                        progress_callback(f"GPT-5 timeout after 1 hour. Switching to Gemini 2.5 Pro...")
                    # Don't retry on timeout - go straight to Gemini
                    retry_count = max_retries + 1
                elif 'rate' in str(e).lower():
                    if progress_callback:
                        progress_callback(f"Rate limit hit, waiting before retry...")
                    import time
                    time.sleep(5)  # Wait 5 seconds for rate limit
                
                retry_count += 1
                if retry_count > max_retries:
                    # Save error response for debugging
                    self._save_response_to_file(str(e), 'error')
                    break
                
                # Wait before retry with exponential backoff
                import time
                wait_time = min(2 ** retry_count, 30)  # Max 30 seconds
                if progress_callback:
                    progress_callback(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
        
        # If GPT-5 failed, use Gemini 2.5 Pro with its 2M token context window
        logger.warning("GPT-5 failed after retries, switching to Gemini 2.5 Pro")
        if progress_callback:
            progress_callback("GPT-5 unavailable, using Gemini 2.5 Pro (2M token context)...")
        
        try:
            # Use Gemini 2.5 Pro as fallback
            from langchain_google_genai import ChatGoogleGenerativeAI
            import os
            
            google_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            if not google_api_key:
                logger.error("No Google/Gemini API key available for fallback")
                return None
            
            # Get tags_data from the parent scope for logging
            tags_count = "all"
            for var_name, var_value in locals().items():
                if var_name == 'user_prompt':
                    # Extract concept count from prompt if possible
                    import re
                    match = re.search(r'(\d+)\s+concepts?', var_value[:1000])
                    if match:
                        tags_count = match.group(1)
                    break
            logger.info(f"Using Gemini 2.5 Pro to process {tags_count} concepts")
            gemini_client = ChatGoogleGenerativeAI(
                model="gemini-2.5-pro",
                google_api_key=google_api_key,
                temperature=0.15,
                max_tokens=100000,  # Gemini can handle much larger outputs
                convert_system_message_to_human=True
            )
            
            from langchain_core.messages import HumanMessage, SystemMessage
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            if progress_callback:
                progress_callback(f"Processing ALL concepts with Gemini 2.5 Pro...")
            
            response = gemini_client.invoke(messages)
            
            if hasattr(response, 'content'):
                result_text = response.content
            else:
                result_text = str(response)
            
            logger.info("Gemini 2.5 Pro successfully processed all concepts")
            self._save_response_to_file(result_text, 'gemini_success')
            return result_text
            
        except Exception as gemini_error:
            logger.error(f"Gemini 2.5 Pro also failed: {gemini_error}")
            self._save_response_to_file(str(gemini_error), 'gemini_error')
            if progress_callback:
                progress_callback("Both GPT-5 and Gemini failed, using rule-based fallback")
            return None
    
    def _validate_gpt5_result(self, result: Dict[str, Any], original_tags: List[Dict]) -> Dict[str, Any]:
        """
        Validate that GPT-5's reorganization is complete and correct
        """
        validation = {
            'all_tags_mapped': True,
            'unmapped_tags': [],
            'unmapped_ids': [],
            'duplicate_aliases': [],
            'orphan_concepts': [],
            'statistics': {}
        }
        
        # Get all original tag texts and IDs
        original_tag_texts = set(tag.get('tag', tag.get('slug', '')) for tag in original_tags if tag.get('tag') or tag.get('slug'))
        original_tag_ids = set(tag.get('id') for tag in original_tags if tag.get('id'))
        
        # Get all concepts and aliases from result
        concepts = {c.get('slug', c.get('tag', '')): c for c in result.get('concepts', []) if c.get('slug') or c.get('tag')}
        concept_ids = set(c.get('id') for c in result.get('concepts', []) if c.get('id'))
        aliases = result.get('aliases', [])
        
        # Check if all original tags are mapped
        mapped_tags = set()
        
        # Add concept slugs and display names (handle both 'slug' and 'tag' fields)
        for concept in concepts.values():
            # GPT-5 might return either 'slug' or 'tag' field
            concept_id = concept.get('slug') or concept.get('tag', '')
            if concept_id:
                mapped_tags.add(concept_id)
            if 'display_name' in concept:
                mapped_tags.add(concept['display_name'])
        
        # Add alias texts (handle both 'alias_text' and 'from_tag' fields)
        for alias in aliases:
            alias_text = alias.get('alias_text') or alias.get('from_tag', '')
            if alias_text:
                mapped_tags.add(alias_text)
        
        # Find unmapped tags
        for tag in original_tag_texts:
            if tag not in mapped_tags:
                # Check if the canonicalized version is mapped
                from app.services.comprehensive_tag_reorganizer import ComprehensiveTagReorganizer
                reorganizer = ComprehensiveTagReorganizer()
                canonical = reorganizer.canonicalize_slug(tag)
                
                if canonical not in concepts:
                    validation['all_tags_mapped'] = False
                    validation['unmapped_tags'].append(tag)
        
        # Check for duplicate aliases (handle both 'alias_text' and 'alias_tag' fields)
        alias_texts = [a.get('alias_text') or a.get('alias_tag', '') for a in aliases]
        duplicates = [t for t in alias_texts if alias_texts.count(t) > 1]
        if duplicates:
            validation['duplicate_aliases'] = list(set(duplicates))
        
        # Check for orphan concepts (non-root with no parents)
        root_categories = set(result.get('root_categories', []))
        for concept in concepts.values():
            concept_id = concept.get('slug') or concept.get('tag', '')
            if not concept.get('parents') and concept_id and concept_id not in root_categories:
                validation['orphan_concepts'].append(concept_id)
        
        # Check ID coverage if IDs were provided
        if original_tag_ids:
            for tag_id in original_tag_ids:
                if tag_id not in concept_ids:
                    # Check if it's mapped via an alias
                    alias_mapped = any(a.get('id') == tag_id or a.get('alias_of') == tag_id 
                                      for a in aliases)
                    if not alias_mapped:
                        validation['unmapped_ids'].append(tag_id)
        
        # Statistics
        validation['statistics'] = {
            'total_input_tags': len(original_tags),
            'mapped_tags': len(original_tag_texts) - len(validation['unmapped_tags']),
            'mapped_ids': len(original_tag_ids) - len(validation['unmapped_ids']) if original_tag_ids else 0,
            'concepts_created': len(concepts),
            'aliases_created': len(aliases),
            'root_categories': len(root_categories),
            'orphan_concepts': len(validation['orphan_concepts']),
            'duplicate_aliases': len(validation['duplicate_aliases']),
            'ids_provided': len(original_tag_ids) if original_tag_ids else 0
        }
        
        return validation
    
    def _extract_json_from_markdown(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from markdown code blocks (handles Gemini's response format)
        """
        try:
            # Look for JSON wrapped in markdown code blocks
            # Patterns: ```json ... ```, ``` ... ```, or just {...}
            
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
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting JSON from markdown: {e}")
            return None

    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Enhanced JSON extraction from text response with multiple strategies
        """
        # Save the raw response for debugging
        self._save_response_to_file(text, 'json_extraction_attempt')
        
        try:
            # Strategy 0: Try markdown extraction first (handles Gemini responses)
            markdown_result = self._extract_json_from_markdown(text)
            if markdown_result:
                logger.info("Successfully extracted JSON from markdown code block")
                return markdown_result
            
            # Strategy 1: Strip C-style comments before parsing
            # Remove /* ... */ comments that may be causing JSON parsing to fail
            text_without_comments = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
            
            # Strategy 2: Direct JSON parse (if response is pure JSON)
            try:
                return json.loads(text_without_comments)
            except json.JSONDecodeError:
                pass
            
            # Also try original text without comment removal (fallback)
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
            
            # Strategy 3: Find largest JSON-like structure (use comment-stripped text)
            # Match from first { to last }
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text_without_comments, re.DOTALL)
            if json_match:
                try:
                    # Try to fix common issues
                    json_str = json_match.group(0)
                    # Remove any remaining comments
                    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
                    # Remove trailing commas
                    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
                    # Fix unescaped quotes in strings
                    json_str = re.sub(r'(?<!\\)"([^"]*?)(?<!\\)"([^:,}\]]*?)(?<!\\)"', r'"\1\\"\2"', json_str)
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.warning(f"Found JSON structure but failed to parse: {e}")
            
            # Strategy 4: Try to extract specific expected structure (use comment-stripped text)
            # Look for concepts array
            concepts_match = re.search(r'"concepts"\s*:\s*\[(.*?)\]', text_without_comments, re.DOTALL)
            aliases_match = re.search(r'"aliases"\s*:\s*\[(.*?)\]', text_without_comments, re.DOTALL)
            
            if concepts_match or aliases_match:
                try:
                    reconstructed = {
                        "concepts": json.loads('[' + (concepts_match.group(1) if concepts_match else '') + ']'),
                        "aliases": json.loads('[' + (aliases_match.group(1) if aliases_match else '') + ']')
                    }
                    return reconstructed
                except:
                    pass
            
            # Strategy 5: Clean up common formatting issues and retry (use comment-stripped text)
            cleaned = text_without_comments
            # Remove any text before first {
            first_brace = cleaned.find('{')
            if first_brace > 0:
                cleaned = cleaned[first_brace:]
            # Remove any text after last }
            last_brace = cleaned.rfind('}')
            if last_brace > 0:
                cleaned = cleaned[:last_brace + 1]
            
            # Remove any remaining comments that might have been missed
            cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
            
            try:
                return json.loads(cleaned)
            except:
                pass
            
            logger.error("All JSON extraction strategies failed")
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract JSON from text: {e}")
            return None
    
    def _save_response_to_file(self, content: str, response_type: str = 'response') -> str:
        """
        Save GPT-5 response to a file for debugging
        
        Returns:
            Path to the saved file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"gpt5_{response_type}_{timestamp}.txt"
        filepath = RESPONSE_LOG_DIR / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Type: {response_type}\n")
                f.write(f"Model: {self.model_config.get('model', 'unknown')}\n")
                f.write("-" * 80 + "\n")
                f.write(content)
            
            logger.info(f"Saved GPT-5 {response_type} to: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save response to file: {e}")
            return ""
    
    def _fallback_reorganization(self, tags_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fallback to the rule-based reorganizer if GPT-5 fails
        """
        logger.info("Falling back to rule-based reorganization")
        
        from app.services.comprehensive_tag_reorganizer import ComprehensiveTagReorganizer
        
        reorganizer = ComprehensiveTagReorganizer()
        result = reorganizer.reorganize_tags(tags_data)
        
        # Mark that this was a fallback
        result['metadata'] = {
            'model': 'fallback_rule_based',
            'timestamp': datetime.utcnow().isoformat(),
            'reason': 'GPT-5 unavailable or failed'
        }
        
        return result
    
    def analyze_tags(self, tags_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use GPT-5 to analyze the current tag structure before reorganization
        """
        try:
            logger.info(f"Analyzing {len(tags_data)} tags with GPT-5")
            
            # Use the analysis model configuration
            analysis_config = self.llm_service.llm_config['models'].get('tag_reorganization_analysis')
            
            # Prepare a summary for analysis
            tag_summary = {
                'total_tags': len(tags_data),
                'sample_tags': tags_data[:100],  # First 100 as sample
                'tag_lengths': [len(t['tag']) for t in tags_data],
                'usage_distribution': self._get_usage_distribution(tags_data)
            }
            
            system_prompt = """You are an expert at analyzing tag taxonomies. 
            Analyze the provided tags and identify:
            1. Duplicate concepts with different spellings
            2. Inconsistent naming conventions
            3. Missing hierarchy relationships
            4. Suggested root categories
            5. Quality issues and recommendations"""
            
            user_prompt = f"""Analyze these tags and provide insights:
            
            Total tags: {tag_summary['total_tags']}
            Sample tags: {json.dumps(tag_summary['sample_tags'], indent=2)}
            
            Provide analysis as JSON with structure:
            {{
                "duplicates": [],
                "naming_issues": [],
                "suggested_categories": [],
                "quality_score": 0-100,
                "recommendations": []
            }}"""
            
            # Call GPT-5 for analysis
            result_text = self._call_gpt5(system_prompt, user_prompt)
            
            if result_text:
                try:
                    return json.loads(result_text)
                except:
                    return {'error': 'Failed to parse analysis', 'raw': result_text}
            
            return {'error': 'No analysis generated'}
            
        except Exception as e:
            logger.error(f"Error in tag analysis: {e}")
            return {'error': str(e)}
    
    def _get_usage_distribution(self, tags_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get distribution of tag usage counts
        """
        distribution = {
            'unused': 0,
            'low_1_10': 0,
            'medium_11_50': 0,
            'high_51_100': 0,
            'very_high_100_plus': 0
        }
        
        for tag in tags_data:
            count = tag.get('count', 0)
            if count == 0:
                distribution['unused'] += 1
            elif count <= 10:
                distribution['low_1_10'] += 1
            elif count <= 50:
                distribution['medium_11_50'] += 1
            elif count <= 100:
                distribution['high_51_100'] += 1
            else:
                distribution['very_high_100_plus'] += 1
        
        return distribution