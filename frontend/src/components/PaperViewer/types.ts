/**
 * Shared types for the PaperViewer component family.
 */

export interface PaperSection {
  id: number;
  section_type: string;
  title: string;
  content: string;
  position: number;
}

export interface PaperSnippet {
  id: number;
  content: string;
  annotation?: string;
  category?: string;
  created_at: string;
  page_number?: number;
}

export interface PaperAuthor {
  name: string;
  email?: string;
  affiliation?: string;
  affiliation_index?: number;
}

export interface Paper {
  id: number;
  title: string;
  abstract?: string;
  content?: string;
  markdown_content?: string;
  authors: PaperAuthor[] | string;
  authors_detailed?: Array<{
    name: string;
    affiliation?: string;
    email?: string;
  }>;
  authors_list?: Array<{
    name: string;
    affiliation?: string;
    email?: string;
    position?: number;
  }>;
  affiliations?: Array<string | { name: string }>;
  publication_date?: string;
  conference?: string;
  journal?: string;
  arxiv_id?: string;
  doi?: string;
  openreview_id?: string;
  openreview_url?: string;
  bibtex?: string;
  import_source?: string;
  import_url?: string;
  page_count: number;
  tags?: string[];
  created_at: string;
  processed: boolean;
  processor_used?: string;
  processing_status?: string;
  processing_error?: string;
  pdf_path?: string;
  sections?: PaperSection[];
  snippets?: PaperSnippet[];
  flagged?: boolean;
  rating?: number | null;
  notes?: string;
  metadata?: {
    supplementary?: Array<{
      type: string;
      url: string;
    }>;
    grobid_processed?: boolean;
    grobid_processed_at?: string;
    [key: string]: any;
  };
  dblp_key?: string;
  dblp_url?: string;
}

export interface DocumentChunk {
  id: string;
  content: string;
  startIndex: number;
  endIndex: number;
  headings: Array<{ id: string; text: string; level: number }>;
}

export interface TOCItem {
  id: string;
  text: string;
  level: number;
  position: number;
}
