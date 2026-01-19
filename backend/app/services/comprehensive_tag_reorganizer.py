"""
Comprehensive Tag Reorganization Service
Reorganizes thousands of tags into a clean, backwards-compatible taxonomy
with proper canonicalization, aliasing, and hierarchy management.
"""

import re
import json
import logging
from typing import Dict, List, Set, Optional, Tuple, Any
from collections import defaultdict, Counter
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class AliasType(Enum):
    """Types of aliases for backwards compatibility"""
    SYNONYM = "synonym"              # Different word, same meaning
    VARIANT = "variant"              # Spelling/case variant
    MISSPELLING = "misspelling"      # Common misspelling
    ABBREVIATION = "abbreviation"    # Shortened form
    PLURAL = "plural"                # Plural/singular form
    DEPRECATED = "deprecated"        # Old tag being phased out
    LEGACY = "legacy"                # Historical tag name

class ConceptStatus(Enum):
    """Status of a concept in the taxonomy"""
    ACTIVE = "active"                # Normal use
    SUGGESTED = "suggested"          # Proposed but not confirmed
    DEPRECATED = "deprecated"        # Being phased out
    MERGED = "merged"               # Merged into another concept

@dataclass
class Concept:
    """A canonical concept in the taxonomy"""
    id: str
    slug: str                       # Canonical slug (lower_snake_case)
    display_name: str               # Human-readable name
    description: str = ""
    parents: List[str] = field(default_factory=list)
    children: Set[str] = field(default_factory=set)
    status: ConceptStatus = ConceptStatus.ACTIVE
    usage_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Alias:
    """An alias pointing to a canonical concept"""
    alias_text: str                 # The actual alias text
    canonical_slug: str             # The concept it points to
    alias_type: AliasType
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Relation:
    """Relationships between concepts"""
    source: str
    target: str
    relation_type: str              # broader, narrower, related
    metadata: Dict[str, Any] = field(default_factory=dict)

class ComprehensiveTagReorganizer:
    """
    Complete tag reorganization system with canonicalization,
    aliasing, and hierarchy management
    """
    
    # Root categories for the taxonomy
    ROOT_CATEGORIES = {
        "ai_ml_fundamentals": {
            "display_name": "AI/ML Fundamentals",
            "description": "Core concepts, theories, and foundations of artificial intelligence and machine learning"
        },
        "models_architectures": {
            "display_name": "Models & Architectures",
            "description": "Specific models, neural network architectures, and model families"
        },
        "techniques_methods": {
            "display_name": "Techniques & Methods",
            "description": "Algorithms, training techniques, optimization methods, and approaches"
        },
        "applications_domains": {
            "display_name": "Applications & Domains",
            "description": "Real-world applications and specific domain implementations"
        },
        "data_datasets": {
            "display_name": "Data & Datasets",
            "description": "Datasets, data processing, and data-related topics"
        },
        "evaluation_metrics": {
            "display_name": "Evaluation & Metrics",
            "description": "Performance metrics, benchmarks, and evaluation methods"
        },
        "tools_infrastructure": {
            "display_name": "Tools & Infrastructure",
            "description": "Software tools, frameworks, platforms, and infrastructure"
        },
        "research_development": {
            "display_name": "Research & Development",
            "description": "Research topics, papers, conferences, and development practices"
        },
        "industry_business": {
            "display_name": "Industry & Business",
            "description": "Companies, products, business applications, and industry trends"
        },
        "ethics_society": {
            "display_name": "Ethics & Society",
            "description": "AI ethics, safety, societal impact, and governance"
        }
    }
    
    def __init__(self):
        self.concepts: Dict[str, Concept] = {}
        self.aliases: Dict[str, Alias] = {}
        self.relations: List[Relation] = []
        self.usage_stats: Dict[str, int] = {}
        self.merge_proposals: List[Dict] = []
        
    def canonicalize_slug(self, tag: str) -> str:
        """
        Convert any tag to canonical slug format (lower_snake_case)
        
        Examples:
            "GPT-4" -> "gpt_4"
            "machine-learning" -> "machine_learning"
            "AI Safety" -> "ai_safety"
            "LLMs" -> "llms"
        """
        # Handle None or empty
        if not tag:
            return ""
            
        # Convert to string and strip
        tag = str(tag).strip()
        
        # Replace common separators with underscore
        tag = re.sub(r'[\s\-\.]+', '_', tag)
        
        # Remove special characters except underscore
        tag = re.sub(r'[^a-zA-Z0-9_]', '', tag)
        
        # Convert to lowercase
        tag = tag.lower()
        
        # Remove duplicate underscores
        tag = re.sub(r'_+', '_', tag)
        
        # Strip underscores from ends
        tag = tag.strip('_')
        
        return tag
    
    def generate_display_name(self, slug: str) -> str:
        """
        Generate a human-readable display name from a slug
        
        Examples:
            "gpt_4" -> "GPT-4"
            "machine_learning" -> "Machine Learning"
            "llms" -> "LLMs"
        """
        # Special cases for known acronyms and terms
        special_cases = {
            "gpt": "GPT",
            "llm": "LLM",
            "llms": "LLMs",
            "nlp": "NLP",
            "ml": "ML",
            "ai": "AI",
            "rl": "RL",
            "rlhf": "RLHF",
            "bert": "BERT",
            "lstm": "LSTM",
            "gan": "GAN",
            "gans": "GANs",
            "vae": "VAE",
            "api": "API",
            "apis": "APIs",
            "gpu": "GPU",
            "gpus": "GPUs",
            "cpu": "CPU",
            "tpu": "TPU",
            "rnn": "RNN",
            "cnn": "CNN",
            "sota": "SOTA",
            "agi": "AGI",
            "cv": "CV",
            "ocr": "OCR",
            "asr": "ASR",
            "tts": "TTS",
            "rag": "RAG",
            "dpo": "DPO",
            "ppo": "PPO",
            "sft": "SFT",
            "kl": "KL",
            "moe": "MoE"
        }
        
        # Split by underscore
        parts = slug.split('_')
        
        # Process each part
        display_parts = []
        for part in parts:
            # Check for version numbers (e.g., "4" in "gpt_4")
            if part.isdigit():
                display_parts.append(part)
            # Check special cases
            elif part.lower() in special_cases:
                display_parts.append(special_cases[part.lower()])
            # Check if it's all caps already
            elif part.isupper() and len(part) > 1:
                display_parts.append(part)
            # Otherwise, capitalize normally
            else:
                display_parts.append(part.capitalize())
        
        # Join with appropriate separator
        # Use hyphen for things like "GPT-4", space for others
        if len(display_parts) == 2 and display_parts[1].isdigit():
            return f"{display_parts[0]}-{display_parts[1]}"
        else:
            return " ".join(display_parts)
    
    def detect_alias_type(self, original: str, canonical: str) -> AliasType:
        """
        Detect what type of alias relationship exists
        """
        original_lower = original.lower()
        canonical_lower = canonical.lower()
        
        # Check for misspelling (edit distance)
        if self._is_likely_misspelling(original_lower, canonical_lower):
            return AliasType.MISSPELLING
        
        # Check for abbreviation
        if self._is_abbreviation(original, canonical):
            return AliasType.ABBREVIATION
        
        # Check for plural
        if self._is_plural_form(original_lower, canonical_lower):
            return AliasType.PLURAL
        
        # Check for case/separator variant
        if self.canonicalize_slug(original) == self.canonicalize_slug(canonical):
            return AliasType.VARIANT
        
        # Check if deprecated
        if any(word in original_lower for word in ['old', 'legacy', 'deprecated', 'v1', 'beta']):
            return AliasType.DEPRECATED
        
        # Default to synonym
        return AliasType.SYNONYM
    
    def _is_likely_misspelling(self, s1: str, s2: str) -> bool:
        """Check if two strings are likely misspellings of each other"""
        # Simple edit distance check
        if abs(len(s1) - len(s2)) > 2:
            return False
        
        # Check for common misspellings
        common_misspellings = [
            ('reccomend', 'recommend'),
            ('occured', 'occurred'),
            ('seperate', 'separate'),
            ('definately', 'definitely'),
            ('recieve', 'receive'),
            ('beleive', 'believe'),
            ('wierd', 'weird'),
            ('calender', 'calendar'),
            ('grammer', 'grammar'),
            ('harrass', 'harass'),
            ('untill', 'until'),
            ('wich', 'which'),
            ('occassion', 'occasion'),
            ('aquire', 'acquire'),
            ('arguement', 'argument'),
            ('existance', 'existence'),
            ('experiance', 'experience'),
            ('relavant', 'relevant'),
            ('persistant', 'persistent'),
            ('rythm', 'rhythm')
        ]
        
        for wrong, right in common_misspellings:
            if (wrong in s1 and right in s2) or (wrong in s2 and right in s1):
                return True
        
        return False
    
    def _is_abbreviation(self, short: str, long: str) -> bool:
        """Check if short is an abbreviation of long"""
        short = short.upper()
        long = long.upper()
        
        # Check if short is made of first letters
        if len(short) <= 4 and len(long) > len(short):
            words = re.split(r'[\s\-_]+', long)
            if len(words) == len(short):
                first_letters = ''.join(w[0] for w in words if w)
                if first_letters == short:
                    return True
        
        # Known abbreviations
        known_abbrevs = {
            'ML': 'MACHINE LEARNING',
            'DL': 'DEEP LEARNING',
            'NLP': 'NATURAL LANGUAGE PROCESSING',
            'CV': 'COMPUTER VISION',
            'RL': 'REINFORCEMENT LEARNING',
            'GAN': 'GENERATIVE ADVERSARIAL NETWORK',
            'VAE': 'VARIATIONAL AUTOENCODER',
            'RNN': 'RECURRENT NEURAL NETWORK',
            'CNN': 'CONVOLUTIONAL NEURAL NETWORK',
            'LSTM': 'LONG SHORT TERM MEMORY',
            'BERT': 'BIDIRECTIONAL ENCODER REPRESENTATIONS FROM TRANSFORMERS',
            'GPT': 'GENERATIVE PRE TRAINED TRANSFORMER',
            'LLM': 'LARGE LANGUAGE MODEL',
            'AGI': 'ARTIFICIAL GENERAL INTELLIGENCE',
            'API': 'APPLICATION PROGRAMMING INTERFACE',
            'SDK': 'SOFTWARE DEVELOPMENT KIT',
            'IDE': 'INTEGRATED DEVELOPMENT ENVIRONMENT',
            'GUI': 'GRAPHICAL USER INTERFACE',
            'CLI': 'COMMAND LINE INTERFACE',
            'REST': 'REPRESENTATIONAL STATE TRANSFER',
            'HTTP': 'HYPERTEXT TRANSFER PROTOCOL',
            'JSON': 'JAVASCRIPT OBJECT NOTATION',
            'XML': 'EXTENSIBLE MARKUP LANGUAGE',
            'SQL': 'STRUCTURED QUERY LANGUAGE'
        }
        
        return short in known_abbrevs and known_abbrevs[short] in long
    
    def _is_plural_form(self, s1: str, s2: str) -> bool:
        """Check if one is plural form of the other"""
        # Simple plural rules
        if s1.endswith('s') and s1[:-1] == s2:
            return True
        if s2.endswith('s') and s2[:-1] == s1:
            return True
        
        # 'ies' plural (e.g., 'category' -> 'categories')
        if s1.endswith('ies') and s2 == s1[:-3] + 'y':
            return True
        if s2.endswith('ies') and s1 == s2[:-3] + 'y':
            return True
        
        # 'es' plural (e.g., 'class' -> 'classes')
        if s1.endswith('es') and s1[:-2] == s2:
            return True
        if s2.endswith('es') and s2[:-2] == s1:
            return True
        
        return False
    
    def categorize_tag(self, tag: str, display_name: str = None) -> str:
        """
        Intelligently categorize a tag into one of the root categories
        """
        tag_lower = tag.lower()
        display_lower = (display_name or "").lower()
        
        # Category keywords mapping
        category_keywords = {
            "ai_ml_fundamentals": [
                "machine learning", "deep learning", "artificial intelligence",
                "neural network", "supervised", "unsupervised", "reinforcement learning",
                "classification", "regression", "clustering", "theory", "fundamental",
                "concept", "principle", "foundation", "basic", "introduction"
            ],
            "models_architectures": [
                "model", "architecture", "network", "transformer", "bert", "gpt",
                "resnet", "vgg", "inception", "mobilenet", "efficientnet", "vit",
                "lstm", "gru", "rnn", "cnn", "gan", "vae", "autoencoder",
                "diffusion", "llm", "language model", "vision model"
            ],
            "techniques_methods": [
                "technique", "method", "algorithm", "optimization", "training",
                "fine-tuning", "distillation", "pruning", "quantization",
                "attention", "dropout", "batch norm", "layer norm", "regularization",
                "gradient", "backprop", "learning rate", "scheduler", "augmentation"
            ],
            "applications_domains": [
                "application", "use case", "nlp", "computer vision", "robotics",
                "healthcare", "finance", "education", "gaming", "art", "music",
                "translation", "summarization", "generation", "detection", "recognition",
                "segmentation", "tracking", "prediction", "forecasting", "recommendation"
            ],
            "data_datasets": [
                "data", "dataset", "corpus", "benchmark", "imagenet", "coco",
                "mnist", "cifar", "wikitext", "squad", "glue", "superglue",
                "common crawl", "wikipedia", "preprocessing", "cleaning", "annotation",
                "labeling", "synthetic", "augmentation", "collection"
            ],
            "evaluation_metrics": [
                "metric", "evaluation", "accuracy", "precision", "recall", "f1",
                "bleu", "rouge", "perplexity", "loss", "error", "score",
                "benchmark", "leaderboard", "performance", "sota", "baseline",
                "ablation", "comparison", "analysis", "measurement"
            ],
            "tools_infrastructure": [
                "tool", "framework", "library", "platform", "infrastructure",
                "pytorch", "tensorflow", "jax", "keras", "scikit", "numpy",
                "pandas", "huggingface", "wandb", "mlflow", "docker", "kubernetes",
                "gpu", "tpu", "cuda", "cloud", "aws", "gcp", "azure", "api"
            ],
            "research_development": [
                "research", "paper", "study", "conference", "journal", "arxiv",
                "neurips", "icml", "iclr", "cvpr", "acl", "emnlp", "aaai",
                "publication", "preprint", "review", "survey", "tutorial",
                "experiment", "hypothesis", "methodology", "contribution"
            ],
            "industry_business": [
                "company", "startup", "product", "service", "business", "market",
                "openai", "anthropic", "google", "microsoft", "meta", "amazon",
                "commercial", "enterprise", "saas", "platform", "monetization",
                "pricing", "customer", "user", "adoption", "deployment"
            ],
            "ethics_society": [
                "ethics", "bias", "fairness", "safety", "alignment", "privacy",
                "security", "transparency", "explainability", "interpretability",
                "accountability", "governance", "regulation", "policy", "impact",
                "society", "risk", "harm", "benefit", "trust", "responsible"
            ]
        }
        
        # Score each category
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in tag_lower or keyword in display_lower:
                    # Exact match gets higher score
                    if keyword == tag_lower or keyword == display_lower:
                        score += 3
                    else:
                        score += 1
            category_scores[category] = score
        
        # Get the category with highest score
        best_category = max(category_scores, key=category_scores.get)
        
        # If no good match, use heuristics
        if category_scores[best_category] == 0:
            # Check for model names (often contain numbers or versions)
            if re.search(r'\d', tag) or any(x in tag_lower for x in ['bert', 'gpt', 'net', 'former']):
                return "models_architectures"
            
            # Check for company/product names (often capitalized)
            if tag[0].isupper() and len(tag) > 3:
                return "industry_business"
            
            # Default to fundamentals
            return "ai_ml_fundamentals"
        
        return best_category
    
    def reorganize_tags(self, tags_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main method to reorganize all tags into a clean taxonomy
        
        Args:
            tags_data: List of tag dictionaries with 'tag' and optional 'count' fields
            
        Returns:
            Complete reorganization result with concepts, aliases, and reports
        """
        logger.info(f"Starting reorganization of {len(tags_data)} tags")
        
        # Step 1: Initialize root categories
        self._initialize_root_categories()
        
        # Step 2: Process each tag
        tag_to_concept = {}  # Map original tag to canonical concept
        
        for tag_info in tags_data:
            original_tag = tag_info.get('tag', '')
            usage_count = tag_info.get('count', 0)
            
            if not original_tag:
                continue
            
            # Canonicalize the tag
            canonical_slug = self.canonicalize_slug(original_tag)
            
            # Skip empty slugs
            if not canonical_slug:
                continue
            
            # Check if we've seen this canonical form
            if canonical_slug in self.concepts:
                # Add as alias if different from canonical
                if original_tag != canonical_slug:
                    self._add_alias(original_tag, canonical_slug)
                # Update usage count
                self.concepts[canonical_slug].usage_count += usage_count
            else:
                # Create new concept
                display_name = self.generate_display_name(canonical_slug)
                concept = Concept(
                    id=canonical_slug,
                    slug=canonical_slug,
                    display_name=display_name,
                    usage_count=usage_count
                )
                
                # Categorize it
                category = self.categorize_tag(canonical_slug, display_name)
                concept.parents = [category]
                
                # Add to concepts
                self.concepts[canonical_slug] = concept
                
                # Add the category as parent's child
                if category in self.concepts:
                    self.concepts[category].children.add(canonical_slug)
                
                # Add alias for original if different
                if original_tag != canonical_slug:
                    self._add_alias(original_tag, canonical_slug)
            
            tag_to_concept[original_tag] = canonical_slug
        
        # Step 3: Detect and merge duplicates
        self._detect_and_merge_duplicates()
        
        # Step 4: Clean up hierarchy
        self._cleanup_hierarchy()
        
        # Step 5: Validate completeness
        validation_report = self._validate_reorganization(tags_data)
        
        # Step 6: Generate reports
        result = {
            "summary": {
                "total_original_tags": len(tags_data),
                "total_concepts": len(self.concepts),
                "total_aliases": len(self.aliases),
                "root_categories": len([c for c in self.concepts.values() if not c.parents]),
                "validation_passed": validation_report["all_tags_mapped"]
            },
            "concepts": [self._concept_to_dict(c) for c in self.concepts.values()],
            "aliases": [self._alias_to_dict(a) for a in self.aliases.values()],
            "relations": [self._relation_to_dict(r) for r in self.relations],
            "mapping_report": tag_to_concept,
            "validation_report": validation_report,
            "merge_proposals": self.merge_proposals,
            "hierarchy": self._generate_hierarchy_report()
        }
        
        logger.info(f"Reorganization complete: {len(self.concepts)} concepts, {len(self.aliases)} aliases")
        
        return result
    
    def _initialize_root_categories(self):
        """Initialize the root category concepts"""
        for slug, info in self.ROOT_CATEGORIES.items():
            concept = Concept(
                id=slug,
                slug=slug,
                display_name=info["display_name"],
                description=info["description"],
                parents=[],  # Root nodes have no parents
                status=ConceptStatus.ACTIVE
            )
            self.concepts[slug] = concept
    
    def _add_alias(self, alias_text: str, canonical_slug: str):
        """Add an alias mapping"""
        if alias_text in self.aliases:
            # Already exists, check if it points to the same concept
            if self.aliases[alias_text].canonical_slug != canonical_slug:
                logger.warning(f"Alias conflict: '{alias_text}' maps to both '{self.aliases[alias_text].canonical_slug}' and '{canonical_slug}'")
            return
        
        alias_type = self.detect_alias_type(alias_text, canonical_slug)
        
        self.aliases[alias_text] = Alias(
            alias_text=alias_text,
            canonical_slug=canonical_slug,
            alias_type=alias_type
        )
    
    def _detect_and_merge_duplicates(self):
        """Detect duplicate concepts and merge them"""
        # Group concepts by similar names
        name_groups = defaultdict(list)
        
        for concept in self.concepts.values():
            # Skip root categories
            if not concept.parents:
                continue
            
            # Create a normalized key for grouping
            key = re.sub(r'[^a-z0-9]', '', concept.slug.lower())
            name_groups[key].append(concept)
        
        # Process groups with multiple items
        for key, group in name_groups.items():
            if len(group) > 1:
                # Sort by usage count to keep the most used one
                group.sort(key=lambda x: x.usage_count, reverse=True)
                
                # Keep the first (most used) as canonical
                canonical = group[0]
                
                # Merge others into it
                for duplicate in group[1:]:
                    self._merge_concepts(duplicate, canonical)
    
    def _merge_concepts(self, source: Concept, target: Concept):
        """Merge source concept into target"""
        # Create alias from source to target
        self._add_alias(source.slug, target.slug)
        if source.display_name != target.display_name:
            self._add_alias(source.display_name, target.slug)
        
        # Combine usage counts
        target.usage_count += source.usage_count
        
        # Move children
        for child in source.children:
            target.children.add(child)
            if child in self.concepts:
                # Update child's parent
                child_concept = self.concepts[child]
                child_concept.parents = [p if p != source.slug else target.slug for p in child_concept.parents]
        
        # Update parent's children
        for parent_slug in source.parents:
            if parent_slug in self.concepts:
                parent = self.concepts[parent_slug]
                parent.children.discard(source.slug)
                parent.children.add(target.slug)
        
        # Mark as merged
        source.status = ConceptStatus.MERGED
        source.metadata["merged_into"] = target.slug
        
        # Record merge proposal
        self.merge_proposals.append({
            "source": source.slug,
            "target": target.slug,
            "reason": "Duplicate concept detected",
            "source_usage": source.usage_count,
            "target_usage": target.usage_count
        })
        
        # Remove from active concepts
        del self.concepts[source.slug]
    
    def _cleanup_hierarchy(self):
        """Clean up the hierarchy by removing redundant relationships"""
        for concept in self.concepts.values():
            # Remove duplicate children
            concept.children = set(concept.children)
            
            # Remove self-references
            concept.children.discard(concept.slug)
            if concept.slug in concept.parents:
                concept.parents.remove(concept.slug)
            
            # Ensure all children exist
            valid_children = set()
            for child in concept.children:
                if child in self.concepts:
                    valid_children.add(child)
                else:
                    # Try to find it as an alias
                    if child in self.aliases:
                        canonical = self.aliases[child].canonical_slug
                        if canonical in self.concepts:
                            valid_children.add(canonical)
            concept.children = valid_children
    
    def _validate_reorganization(self, original_tags: List[Dict]) -> Dict[str, Any]:
        """Validate that all original tags can be resolved"""
        validation_report = {
            "all_tags_mapped": True,
            "unmapped_tags": [],
            "alias_conflicts": [],
            "orphan_concepts": [],
            "circular_dependencies": [],
            "statistics": {}
        }
        
        # Check all original tags
        for tag_info in original_tags:
            tag = tag_info.get('tag', '')
            if not tag:
                continue
            
            # Check if it maps to a concept
            canonical_slug = self.canonicalize_slug(tag)
            
            # Check direct concept
            if canonical_slug in self.concepts:
                continue
            
            # Check aliases
            if tag in self.aliases:
                continue
            
            # Not mapped
            validation_report["all_tags_mapped"] = False
            validation_report["unmapped_tags"].append(tag)
        
        # Check for orphan concepts (non-root with no parents)
        for concept in self.concepts.values():
            if not concept.parents and concept.slug not in self.ROOT_CATEGORIES:
                validation_report["orphan_concepts"].append(concept.slug)
        
        # Check for circular dependencies
        for concept in self.concepts.values():
            if self._has_circular_dependency(concept.slug, set()):
                validation_report["circular_dependencies"].append(concept.slug)
        
        # Statistics
        validation_report["statistics"] = {
            "total_tags": len(original_tags),
            "mapped_tags": len(original_tags) - len(validation_report["unmapped_tags"]),
            "concepts": len(self.concepts),
            "aliases": len(self.aliases),
            "orphans": len(validation_report["orphan_concepts"]),
            "circular": len(validation_report["circular_dependencies"])
        }
        
        return validation_report
    
    def _has_circular_dependency(self, slug: str, visited: Set[str]) -> bool:
        """Check if a concept has circular parent dependencies"""
        if slug in visited:
            return True
        
        if slug not in self.concepts:
            return False
        
        visited.add(slug)
        concept = self.concepts[slug]
        
        for parent in concept.parents:
            if self._has_circular_dependency(parent, visited.copy()):
                return True
        
        return False
    
    def _generate_hierarchy_report(self) -> Dict[str, Any]:
        """Generate a hierarchical view of the taxonomy"""
        hierarchy = {}
        
        # Start with root categories
        for slug in self.ROOT_CATEGORIES:
            if slug in self.concepts:
                hierarchy[slug] = self._build_hierarchy_node(self.concepts[slug])
        
        return hierarchy
    
    def _build_hierarchy_node(self, concept: Concept, depth: int = 0, max_depth: int = 5) -> Dict[str, Any]:
        """Build a hierarchy node recursively"""
        if depth > max_depth:
            return None
        
        node = {
            "slug": concept.slug,
            "display_name": concept.display_name,
            "usage_count": concept.usage_count,
            "children": {}
        }
        
        # Add children
        for child_slug in sorted(concept.children):
            if child_slug in self.concepts:
                child_node = self._build_hierarchy_node(self.concepts[child_slug], depth + 1, max_depth)
                if child_node:
                    node["children"][child_slug] = child_node
        
        return node
    
    def _concept_to_dict(self, concept: Concept) -> Dict[str, Any]:
        """Convert concept to dictionary for JSON serialization"""
        return {
            "id": concept.id,
            "slug": concept.slug,
            "display_name": concept.display_name,
            "description": concept.description,
            "parents": concept.parents,
            "children": list(concept.children),
            "status": concept.status.value,
            "usage_count": concept.usage_count,
            "metadata": concept.metadata
        }
    
    def _alias_to_dict(self, alias: Alias) -> Dict[str, Any]:
        """Convert alias to dictionary for JSON serialization"""
        return {
            "alias_text": alias.alias_text,
            "canonical_slug": alias.canonical_slug,
            "alias_type": alias.alias_type.value,
            "confidence": alias.confidence,
            "metadata": alias.metadata
        }
    
    def _relation_to_dict(self, relation: Relation) -> Dict[str, Any]:
        """Convert relation to dictionary for JSON serialization"""
        return {
            "source": relation.source,
            "target": relation.target,
            "relation_type": relation.relation_type,
            "metadata": relation.metadata
        }
    
    def export_to_database_format(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export the reorganization result to a format suitable for database import
        """
        return {
            "concepts": result["concepts"],
            "aliases": result["aliases"],
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0",
            "backwards_compatible": True
        }