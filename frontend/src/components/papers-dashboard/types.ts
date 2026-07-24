/**
 * Shared types for the Papers Dashboard components.
 */

export interface Paper {
  id: number
  title: string
  abstract?: string
  authors: Array<{ name: string; email?: string; affiliation?: string }> | string
  authors_detailed?: Array<{ name: string; email?: string; affiliation?: string }>
  publication_date?: string
  year?: number
  conference?: string
  journal?: string
  arxiv_id?: string
  doi?: string
  dblp_url?: string
  pdf_path?: string
  page_count: number
  word_count?: number
  tags: string[]
  concepts?: Array<{ concept_id: string; slug: string; display_name: string }>
  created_at: string
  processed: boolean
  processor?: string
  processor_used?: string
  processing_error?: string
  processing_status?: string
  is_flagged?: boolean
  flag_notes?: string
  tei_content?: string
  analyses?: Array<any>
  ai_summary?: string
  key_findings?: string[]
  readability?: {
    flesch_reading_ease?: number
    flesch_kincaid_grade?: number
    difficulty?: string
    academic_level?: string
  }
  user_rating?: number
  paper_type?: 'research' | 'review'
  review_deadline?: string
  review_decision?: 'pending' | 'accept' | 'reject' | 'major_revision' | 'minor_revision'
  review_notes?: string
  review_confidence?: number
}

export interface PapersStats {
  total_papers: number
  total_authors: number
  total_concept_tags?: number
  total_tags?: number
  total_snippets: number
  recent_papers: Array<{ id: number; title: string; created_at: string }>
  top_tags: Array<{ tag: string; count: number }>
}

export interface FacetItem {
  value: string | number
  count: number
  label: string
}

export interface Facets {
  authors: FacetItem[]
  conferences: FacetItem[]
  journals: FacetItem[]
  years: FacetItem[]
  tags: FacetItem[]
  concepts: any[]
  affiliations: FacetItem[]
  processors: FacetItem[]
  special_filters: FacetItem[]
  missing_data?: {
    no_processor: number
    no_year: number
    no_conference: number
    no_affiliation: number
    no_annotations: number
    no_mollick_summary: number
  }
  paper_status?: {
    flagged: number
    unflagged: number
  }
  rating?: {
    '5_stars': number
    '4_stars': number
    '3_stars': number
    '2_stars': number
    '1_star': number
    'unrated': number
    [key: string]: number
  }
}
