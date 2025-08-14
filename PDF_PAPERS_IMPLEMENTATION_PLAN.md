# PDF Research Papers Integration - Implementation Plan

## Overview
Extending SmartTrendTracer to include PDF research papers as a third major content source alongside Twitter/X and Newsletters, creating a comprehensive AI Research Intelligence Platform.

## Architecture Components

### 1. Data Ingestion & Storage
- **Upload Interface**: Drag-and-drop PDF upload area in the UI
- **Bulk Import**: Watch folder for automatic PDF ingestion
- **ArXiv Integration**: API integration to auto-fetch papers by category/keywords
- **URL Import**: Fetch PDFs from URLs (ArXiv, OpenReview, etc.)
- **Database Schema**: New tables for `papers`, `paper_authors`, `paper_sections`, `paper_references`

### 2. PDF Processing Pipeline
- **Text Extraction**: PyPDF2 or pdfplumber for text extraction
- **Metadata Extraction**: 
  - Title, authors, abstract, publication date
  - Conference/journal, DOI, ArXiv ID
  - Citations and references
- **Section Parsing**: Identify Introduction, Methods, Results, Conclusion
- **Figure/Table Captions**: Extract and index figure descriptions
- **Mathematical Formulas**: Preserve LaTeX notation where possible

### 3. Content Analysis
- **Automatic Tagging**: Same AI tagging system as tweets/articles
- **Citation Network**: Track which papers cite each other
- **Key Concepts Extraction**: Identify main contributions, methods, datasets
- **Code Repository Links**: Extract GitHub/GitLab links from papers
- **Dataset References**: Identify mentioned datasets

### 4. Search & Retrieval
- **Full-Text Search**: Include papers in RAG search index
- **Semantic Search**: Vector embeddings for paper abstracts/sections
- **Citation Search**: Find papers by references/citations
- **Author Search**: Track papers by specific researchers

### 5. UI Components Needed
- **Papers Browser**: Similar to FacetedTweetsDashboard but for papers
  - Filter by: Year, Conference, Authors, Tags, Citations
  - Sort by: Date, Citation count, Relevance
- **Paper Viewer**: 
  - PDF viewer with highlighting capability
  - Side panel for notes/snippets
  - Citation preview on hover
- **Research Trends Dashboard**:
  - Most cited papers
  - Rising research topics
  - Author collaboration networks
  - Conference/journal distribution

### 6. Integration with Existing Features
- **Unified Trends**: Compare research paper topics with Twitter/Newsletter discussions
- **Cross-Reference Detection**: Link papers mentioned in tweets/articles
- **Timeline View**: Show when papers are published vs when they trend on social media
- **Impact Tracking**: Monitor social media discussion of specific papers

### 7. Advanced Features
- **Paper Summaries**: LLM-generated summaries with key findings
- **Related Papers**: Recommend similar papers based on content
- **Research Threads**: Group papers by research lineage
- **Breakthrough Detection**: Identify papers with unusual citation velocity
- **Author Profiles**: Aggregate all papers by author with stats

### 8. Data Enrichment
- **Semantic Scholar API**: Get citation counts, author h-index
- **CrossRef API**: Fetch DOI metadata
- **Google Scholar**: Track citations (with careful rate limiting)
- **GitHub Integration**: Link to implementation repositories

### 9. Backend API Endpoints
```python
# Core endpoints
/api/papers/upload              # POST - Upload single PDF
/api/papers/bulk-upload         # POST - Upload multiple PDFs
/api/papers/import-arxiv        # POST - Import from ArXiv
/api/papers/import-url          # POST - Import from URL

# Browse and retrieve
/api/papers                     # GET - List papers with filters
/api/papers/{paper_id}          # GET - Get paper details
/api/papers/{paper_id}/content  # GET - Get full text content
/api/papers/{paper_id}/sections # GET - Get parsed sections

# Analysis
/api/papers/{paper_id}/citations   # GET - Get citations
/api/papers/{paper_id}/references  # GET - Get references
/api/papers/{paper_id}/snippets    # GET/POST - Manage snippets
/api/papers/{paper_id}/tags        # GET/POST/DELETE - Manage tags
/api/papers/{paper_id}/summarize   # POST - Generate AI summary

# Trends and search
/api/papers/trends              # GET - Paper trends analysis
/api/papers/search              # GET - Search papers
/api/papers/authors             # GET - List authors
/api/papers/authors/{author_id} # GET - Author details and papers
```

### 10. Database Schema

```sql
-- Core paper table
CREATE TABLE papers (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    content TEXT,  -- Full extracted text
    pdf_path TEXT,  -- Path to stored PDF
    arxiv_id VARCHAR(50),
    doi VARCHAR(100),
    publication_date DATE,
    conference VARCHAR(200),
    journal VARCHAR(200),
    citation_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Authors
CREATE TABLE paper_authors (
    id SERIAL PRIMARY KEY,
    paper_id INTEGER REFERENCES papers(id),
    name TEXT NOT NULL,
    email TEXT,
    affiliation TEXT,
    position INTEGER,  -- Author order
    is_corresponding BOOLEAN DEFAULT FALSE
);

-- Sections
CREATE TABLE paper_sections (
    id SERIAL PRIMARY KEY,
    paper_id INTEGER REFERENCES papers(id),
    section_type VARCHAR(50),  -- intro, methods, results, etc.
    title TEXT,
    content TEXT,
    position INTEGER
);

-- References
CREATE TABLE paper_references (
    id SERIAL PRIMARY KEY,
    paper_id INTEGER REFERENCES papers(id),
    cited_paper_id INTEGER REFERENCES papers(id),  -- If we have it
    raw_citation TEXT,
    title TEXT,
    authors TEXT,
    year INTEGER,
    venue TEXT
);

-- Tags (reuse existing tag system)
CREATE TABLE paper_tags (
    paper_id INTEGER REFERENCES papers(id),
    tag_id INTEGER REFERENCES tags(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (paper_id, tag_id)
);

-- Snippets
CREATE TABLE paper_snippets (
    id SERIAL PRIMARY KEY,
    paper_id INTEGER REFERENCES papers(id),
    content TEXT NOT NULL,
    page_number INTEGER,
    section_id INTEGER REFERENCES paper_sections(id),
    annotation TEXT,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Implementation Phases

### Phase 1: Basic Upload, Text Extraction, Storage ✅ CURRENT
**Goal**: Get PDFs into the system with basic text extraction

1. **Database Setup**
   - Create paper tables
   - Add to existing database migration

2. **Backend - PDF Processing**
   - Install PyPDF2/pdfplumber
   - Create `PaperService` class for PDF handling
   - Extract text, title, basic metadata
   - Store PDF files in `data/papers/` directory

3. **Backend - API Endpoints**
   - `POST /api/papers/upload` - Single file upload
   - `GET /api/papers` - List uploaded papers
   - `GET /api/papers/{id}` - Get paper details

4. **Frontend - Upload UI**
   - Create `PaperUploadModern.tsx` component
   - Drag-and-drop zone with shadcn/ui
   - Upload progress indicator
   - Success/error feedback

### Phase 2: Metadata Extraction & Search Integration
**Goal**: Extract structured metadata and integrate with search

1. **Enhanced Extraction**
   - Extract authors, abstract, sections
   - Parse references
   - Identify publication venue

2. **Search Integration**
   - Add papers to RAG index
   - Update vector store with paper embeddings
   - Extend search API to include papers

3. **Basic Paper Browser**
   - List view of papers
   - Basic filtering (date, author)
   - Search within papers

### Phase 3: Paper Viewer, Tagging, Snippets
**Goal**: Rich interaction with paper content

1. **PDF Viewer Component**
   - Integrate PDF.js for in-browser viewing
   - Text selection and highlighting
   - Page navigation

2. **Tagging System**
   - Extend existing tag system to papers
   - Auto-suggest tags based on content
   - Tag-based filtering

3. **Snippet Management**
   - Create snippets from selected text
   - Categorize snippets
   - Add annotations

### Phase 4: Trends Analysis & Cross-Source Integration
**Goal**: Analyze research trends and connect with other sources

1. **Paper Trends**
   - Track popular papers
   - Identify emerging topics
   - Author activity analysis

2. **Cross-Source Links**
   - Detect papers mentioned in tweets
   - Link newsletter discussions to papers
   - Unified timeline view

3. **Enhanced Analytics**
   - Citation network visualization
   - Topic evolution over time
   - Impact metrics

### Phase 5: Advanced Features
**Goal**: Knowledge graph, recommendations, and AI features

1. **Knowledge Graph**
   - Visual paper relationships
   - Citation networks
   - Author collaborations

2. **AI Features**
   - Auto-summarization
   - Related paper recommendations
   - Key insight extraction

3. **External Integrations**
   - ArXiv auto-import
   - Semantic Scholar API
   - GitHub repo linking

## Success Metrics
- Number of papers uploaded and processed
- Search accuracy for paper content
- Cross-reference detection rate
- User engagement with paper features
- Time saved in research discovery

## Technical Stack
- **Backend**: FastAPI, SQLAlchemy, PyPDF2/pdfplumber
- **Frontend**: React, TypeScript, shadcn/ui, PDF.js
- **Storage**: PostgreSQL/SQLite, File system for PDFs
- **AI/ML**: OpenAI embeddings, FAISS vector store
- **Processing**: Celery for async PDF processing (optional)

## Estimated Timeline
- Phase 1: 2-3 days
- Phase 2: 3-4 days
- Phase 3: 4-5 days
- Phase 4: 1 week
- Phase 5: 1-2 weeks

Total: ~4-5 weeks for full implementation

## Next Steps - Phase 1 Implementation
1. Create database migrations for paper tables
2. Set up PDF processing service with PyPDF2
3. Implement upload API endpoint
4. Build upload UI component
5. Test with sample research papers