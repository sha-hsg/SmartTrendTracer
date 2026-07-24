export interface Article {
  id: number
  title: string
  author: string
  tags: string[]
  url?: string
  published_date?: string
  summary?: string
  similarity_score?: number
  cluster?: number
}

export interface Cluster {
  articles: Article[]
  size: number
  representative_tags: string[]
  tag_distribution?: Record<string, number>
}

export interface ClusteringResult {
  method: string
  n_clusters: number
  clusters: Record<string, Cluster>
  silhouette_score?: number
  noise_articles?: Article[]
}

export interface TagCooccurrence {
  tag1: string
  tag2: string
  co_occurrence_count: number
  jaccard_similarity: number
}

export interface VisualizationPoint {
  id: number
  title: string
  tags: string[]
  x: number
  y: number
  z?: number
}
