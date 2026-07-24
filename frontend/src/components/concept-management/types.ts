export interface Concept {
  id: string
  slug: string
  name: string
  display_name: string
  description?: string
  parent_id?: string | null
  parents?: string[]
  children?: string[]
  entity_type?: string
  icon?: string
  color?: string
  created_at?: string
  created_by?: string
  auto_generated?: boolean
  verified?: boolean
  quality_score?: number
}

export interface UnorganizedConcept {
  _id: string
  display_name: string
  slug: string
  description?: string
  usage_count: number
  created_at: string
}

export interface OrganizationSuggestion {
  is_alias?: boolean
  alias_of?: string
  parent_concepts?: string[]
  entity_type?: string
  description?: string
  reasoning?: string
}

export interface OntologyStats {
  concepts: {
    total: number
    active: number
    root: number
    with_children: number
  }
  aliases: {
    total: number
    unique_concepts: number
  }
  instances: {
    total: number
    tweets: number
    papers: number
    articles: number
    resolved: number
    orphaned: number
  }
}
