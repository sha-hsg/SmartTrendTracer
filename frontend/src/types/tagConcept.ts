/**
 * Type definitions for the new tag concept structure
 */

// Entity types that tags can represent
export type EntityType = 
  | 'person'
  | 'organisation'
  | 'location'
  | 'event'
  | 'product'
  | 'hardware'
  | 'model'
  | 'architecture'
  | 'method'
  | 'task'
  | 'modality'
  | 'dataset'
  | 'benchmark'
  | 'metric'
  | 'license'
  | 'experimental-setup'
  | 'research-topic'
  | 'paper'
  | 'tool'
  | 'concept'
  | 'standard';

// Alias types for tag variations
export type AliasType = 
  | 'synonym'
  | 'variant'
  | 'misspelling'
  | 'deprecated_redirect'
  | 'abbreviation';

// Relation types between concepts
export type RelationType =
  | 'child_of'
  | 'related'
  | 'produces'
  | 'evaluated_on'
  | 'part_of'
  | 'instance_of'
  | 'same_as'
  | 'replaces';

// Status of a concept
export type ConceptStatus = 'active' | 'deprecated' | 'suggested' | 'draft';

/**
 * Core tag concept structure
 */
export interface TagConcept {
  id: string;                    // Unique ID like "c_0001"
  slug: string;                  // Snake_case normalized name
  display_name: string;          // Human-readable name
  description?: string;          // Optional description
  status: ConceptStatus;         // Current status
  entity_type?: EntityType;      // Semantic classification
  parents: string[];             // Parent concept IDs (poly-hierarchy)
  children: string[];            // Child concept IDs
  level: number;                 // Depth in hierarchy (0 for root)
  icon?: string;                 // Optional emoji icon
  color?: string;                // Optional hex color code
  usage_count: number;           // Total usage across content
  created_at: string;            // ISO timestamp
  updated_at: string;            // ISO timestamp
}

/**
 * Tag alias mapping
 */
export interface TagAlias {
  alias_text: string;            // The alias text
  concept_id: string;            // References TagConcept.id
  alias_type: AliasType;         // Type of alias
  confidence: number;            // Confidence score (0-1)
  created_at: string;            // ISO timestamp
}

/**
 * Relation between concepts
 */
export interface TagRelation {
  source_id: string;             // Source concept ID
  target_id: string;             // Target concept ID
  relation_type: RelationType;  // Type of relationship
  confidence: number;            // Confidence score (0-1)
  metadata?: Record<string, any>; // Optional metadata
  created_at: string;            // ISO timestamp
}

/**
 * Tag instance (actual usage in content)
 */
export interface TagInstance {
  content_type: 'tweet' | 'paper' | 'article';
  content_id: string;            // ID of the content
  concept_id?: string;           // Linked concept ID (optional for legacy)
  original_text: string;         // Original tag text as entered
  display_name: string;          // Display name for UI
  tag_type: string;              // manual, ai, llm, etc.
  metadata?: Record<string, any>; // Optional metadata
  created_at: string;            // ISO timestamp
}

/**
 * Tag with concept information (API response)
 */
export interface TagWithConcept {
  original_text: string;         // Original tag text
  concept_id?: string;           // Concept ID if resolved
  slug: string;                  // Normalized slug
  display_name: string;          // Display name
  entity_type?: EntityType;      // Entity type if available
  icon?: string;                 // Icon if available
  color?: string;                // Color if available
  tag_type: string;              // Tag type (manual, ai, etc.)
}

/**
 * Complete tag hierarchy structure
 */
export interface TagHierarchy {
  root_concepts: TagConceptNode[];
  total_concepts: number;
  total_aliases: number;
}

/**
 * Tag concept with nested children for tree display
 * Not extending TagConcept to avoid children type conflict (string[] vs TagConceptNode[])
 */
export interface TagConceptNode {
  id: string;
  slug: string;
  display_name: string;
  description?: string;
  status: ConceptStatus;
  entity_type?: EntityType;
  parents: string[];
  children: TagConceptNode[];  // Nested children for tree (different from TagConcept.children which is string[])
  level: number;
  icon?: string;
  color?: string;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

/**
 * Tag statistics
 */
export interface TagStatistics {
  total_concepts: number;
  total_aliases: number;
  total_tags: number;
  entity_type_distribution: Record<EntityType, number>;
  top_concepts: Array<{
    id: string;
    slug: string;
    display_name: string;
    usage_count: number;
  }>;
  orphan_tags: number;
  coverage: {
    mapped: number;
    unmapped: number;
    percentage: number;
  };
}

/**
 * Entity type configuration with color and icon
 */
export const ENTITY_TYPE_CONFIG: Record<EntityType, { color: string; icon: string }> = {
  person: { color: '#10B981', icon: '👤' },
  organisation: { color: '#8B5CF6', icon: '🏢' },
  location: { color: '#EF4444', icon: '📍' },
  event: { color: '#F59E0B', icon: '📅' },
  product: { color: '#F97316', icon: '🧩' },
  hardware: { color: '#9CA3AF', icon: '🖥️' },
  model: { color: '#EC4899', icon: '🤖' },
  architecture: { color: '#FACC15', icon: '🏗️' },
  method: { color: '#FB923C', icon: '⚙️' },
  task: { color: '#14B8A6', icon: '🧪' },
  modality: { color: '#0EA5E9', icon: '🎛️' },
  dataset: { color: '#84CC16', icon: '📊' },
  benchmark: { color: '#FBBF24', icon: '📈' },
  metric: { color: '#A78BFA', icon: '📏' },
  license: { color: '#F472B6', icon: '📝' },
  'experimental-setup': { color: '#4ADE80', icon: '🧪' },
  'research-topic': { color: '#06B6D4', icon: '🔬' },
  paper: { color: '#0EA5E9', icon: '📜' },
  tool: { color: '#22C55E', icon: '🔧' },
  concept: { color: '#D946EF', icon: '💭' },
  standard: { color: '#94A3B8', icon: '📘' }
};

/**
 * Root category IDs (for hierarchy navigation)
 */
export const ROOT_CATEGORIES = [
  'c_fundamentals',
  'c_models_and_architectures',
  'c_techniques_and_methods',
  'c_data',
  'c_applications',
  'c_evaluation',
  'c_ecosystem_and_industry',
  'c_responsible_ai'
];

/**
 * Helper function to get entity type config
 */
export function getEntityTypeConfig(entityType?: EntityType): { color: string; icon: string } {
  if (!entityType) {
    return { color: '#6B7280', icon: '🏷️' }; // Default gray tag
  }
  return ENTITY_TYPE_CONFIG[entityType] || { color: '#6B7280', icon: '🏷️' };
}

/**
 * Helper function to format display name
 */
export function formatTagDisplay(tag: TagWithConcept | TagConcept): string {
  if ('display_name' in tag) {
    return tag.display_name;
  }
  if ('original_text' in tag) {
    return tag.original_text;
  }
  return 'Unknown Tag';
}