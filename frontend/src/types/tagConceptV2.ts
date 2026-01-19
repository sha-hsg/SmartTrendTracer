/**
 * Type definitions for the v2 tag concept structure
 * All IDs are strings (e.g., "c_0001")
 */

export interface TagConceptV2 {
  id: string  // Unique ID like "c_0001"
  slug: string  // Snake_case normalized name
  display_name: string  // Human-readable name
  description?: string | null
  entity_type?: string  // Type: person, organisation, model, etc.
  status?: 'active' | 'deprecated'
  parents?: string[]  // Parent concept IDs for hierarchy
  children?: string[]  // Child concept IDs
  level?: number  // Hierarchy level (0 = root)
  icon?: string  // Visual icon
  color?: string  // Color code
  usage_count?: number  // How many times used
  created_at?: string
  updated_at?: string
}

export interface TagAliasV2 {
  alias_text: string
  concept_id: string  // References TagConceptV2.id
  alias_type: 'synonym' | 'variant' | 'misspelling' | 'abbreviation' | 'deprecated_redirect'
  confidence?: number
  created_at?: string
}

export interface TagWithConceptV2 {
  tag: string  // Original tag text
  tag_type?: string  // How it was created: manual, llm, etc.
  concept_id?: string  // Resolved concept ID
  slug?: string
  display_name?: string
  entity_type?: string
  icon?: string
  color?: string
}

export interface ContentTagsV2 {
  content_type: 'tweet' | 'paper' | 'article'
  content_id: number  // Still numeric for content items
  tags: TagWithConceptV2[]
}

export interface TagFacetV2 {
  concept_id: string
  slug: string
  display_name: string
  count: number
  entity_type?: string
  icon?: string
  color?: string
}

export interface TagHierarchyNodeV2 extends TagConceptV2 {
  children_concepts?: TagHierarchyNodeV2[]
  child_count?: number
  descendant_count?: number
  aliases?: string[]
}

// Entity type configurations
export const ENTITY_TYPE_CONFIG_V2: Record<string, { color: string; icon: string; label: string }> = {
  'person': { color: '#10B981', icon: '👤', label: 'Person' },
  'organisation': { color: '#8B5CF6', icon: '🏢', label: 'Organisation' },
  'location': { color: '#EF4444', icon: '📍', label: 'Location' },
  'event': { color: '#F59E0B', icon: '📅', label: 'Event' },
  'product': { color: '#F97316', icon: '🧩', label: 'Product' },
  'hardware': { color: '#9CA3AF', icon: '🖥️', label: 'Hardware' },
  'model': { color: '#EC4899', icon: '🤖', label: 'Model' },
  'architecture': { color: '#FACC15', icon: '🏗️', label: 'Architecture' },
  'method': { color: '#FB923C', icon: '⚙️', label: 'Method' },
  'dataset': { color: '#84CC16', icon: '📊', label: 'Dataset' },
  'benchmark': { color: '#FBBF24', icon: '📈', label: 'Benchmark' },
  'metric': { color: '#A78BFA', icon: '📏', label: 'Metric' },
  'task': { color: '#14B8A6', icon: '🧪', label: 'Task' },
  'modality': { color: '#0EA5E9', icon: '🎛️', label: 'Modality' },
  'license': { color: '#F472B6', icon: '📝', label: 'License' },
  'research-topic': { color: '#06B6D4', icon: '🔬', label: 'Research Topic' },
  'paper': { color: '#0EA5E9', icon: '📜', label: 'Paper' },
  'tool': { color: '#22C55E', icon: '🔧', label: 'Tool' },
  'concept': { color: '#D946EF', icon: '💭', label: 'Concept' },
  'standard': { color: '#94A3B8', icon: '📘', label: 'Standard' }
}

// Helper functions
export function getEntityTypeConfig(entityType?: string) {
  if (!entityType) return { color: '#6B7280', icon: '🏷️', label: 'Tag' }
  return ENTITY_TYPE_CONFIG_V2[entityType] || { color: '#6B7280', icon: '🏷️', label: entityType }
}

export function formatTagDisplay(tag: TagWithConceptV2 | TagConceptV2): string {
  if ('display_name' in tag && tag.display_name) {
    return tag.display_name
  }
  if ('tag' in tag && tag.tag) {
    return tag.tag
  }
  if ('slug' in tag && tag.slug) {
    return tag.slug.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }
  return 'Unknown'
}