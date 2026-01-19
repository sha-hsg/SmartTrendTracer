/**
 * TypeScript interfaces for the concept-only tag system
 */

export interface Concept {
  concept_id: string;     // MongoDB ObjectId
  id: string;            // Human-readable ID (e.g., "c_0001")
  slug: string;          // Snake_case slug (e.g., "machine_learning")
  display_name: string;  // Display name (e.g., "Machine Learning")
  entity_type?: 'topic' | 'person' | 'organisation' | 'location' | 'event' | 'product';
  description?: string;
  parents?: string[];    // Parent concept IDs for hierarchy
  icon?: string;         // Optional icon
  color?: string;        // Optional color for UI
  auto_generated?: boolean;
  created_at?: string;
  created_by?: string;
}

export interface ConceptWithCount extends Concept {
  count: number;
  content_types?: string[];
}

export interface Tweet {
  id: string;
  text: string;
  author_id: string;
  author_username: string;
  author_profile_image_url?: string;  // Profile image from twitter_accounts
  created_at: string;
  metrics: {
    likes: number;
    retweets: number;
    replies: number;
    quotes?: number;
  };
  media: TweetMedia[];
  concepts?: Concept[];      // Full concept objects
  concept_ids?: string[];    // Just concept IDs (when not expanded)
}

export interface TweetMedia {
  media_key: string;
  type: 'photo' | 'video' | 'animated_gif';
  url: string;
  preview_image_url?: string;
  alt_text?: string;
  width?: number;
  height?: number;
}

export interface Paper {
  id: number;
  title: string;
  abstract?: string;
  authors: Author[];
  publication_date?: string;
  conference?: string;
  journal?: string;
  arxiv_id?: string;
  doi?: string;
  concepts?: Concept[];
  concept_ids?: string[];
  created_at: string;
}

export interface Author {
  name: string;
  email?: string;
  affiliation?: string;
}

export interface Article {
  id: number;
  title: string;
  author: string;
  url: string;
  published_date?: string;
  preview?: string;
  content?: string;
  summary?: string;
  concepts?: Concept[];
  concept_ids?: string[];
}

// API Response types
export interface ConceptStatsResponse {
  total_concepts: number;
  top_concepts: ConceptWithCount[];
  statistics: {
    total_assignments: number;
    average_per_concept: number;
  };
}

export interface ConceptSearchResponse {
  concepts: Concept[];
  total: number;
}

// For backward compatibility during migration
export interface LegacyTag {
  tag: string;
  display_name?: string;
  slug?: string;
  type: string;
}