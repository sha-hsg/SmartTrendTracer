export interface TagConcept {
  id: string  // v2 uses string IDs like "c_0001"
  tag: string
  display_name: string
  description: string | null
  child_count: number
  descendant_count: number
  synonyms: string[]
  children?: TagConcept[]
  entity_type?: string  // Added for v2
  icon?: string  // Added for v2
  color?: string  // Added for v2
}

export interface ConceptDetails {
  id: string  // v2 uses string IDs
  _id?: string  // MongoDB _id
  slug?: string  // Concept slug
  tag: string
  display_name: string
  description: string | null
  parent_id: string | null  // v2 uses string IDs - first parent for compatibility
  parent?: {  // Single parent for backward compatibility
    id: string
    tag: string
    display_name: string
  }
  parent_details?: Array<{  // All parents for poly-hierarchy
    id: string
    tag: string
    display_name: string
    icon?: string
    color?: string
  }>
  children?: Array<{
    id: string  // v2 uses string IDs
    tag: string
    display_name: string
    child_count: number
    icon?: string
    color?: string
  }>
  level: number
  child_count: number
  descendant_count: number
  synonyms: string[]
  entity_type?: string
  icon?: string
  color?: string
  path: string
  usage_stats?: {
    tweet_count: number
    article_count: number
    paper_count: number
    total_count: number
  }
  created_at?: string
  created_by?: string
  auto_generated?: boolean
  original_tag_text?: string
}
