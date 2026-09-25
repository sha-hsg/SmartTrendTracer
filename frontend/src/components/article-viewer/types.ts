export interface FullArticle {
  id: number
  title: string
  subtitle: string | null
  author?: {
    id?: number
    name: string
    subdomain: string
    url: string
  }
  url: string | null
  content_markdown: string
  content_html: string
  word_count: number
  reading_time_minutes: number
  published_at: string | null
  summary: string | null
  tags: { id: number; tag: string; type: string }[]
  snippets: {
    id: number
    text: string
    annotation: string | null
    category: string | null
    importance: number
    start_offset?: number
    end_offset?: number
  }[]
}

export interface Author {
  id: number
  name: string
  subdomain?: string
  url?: string
}
