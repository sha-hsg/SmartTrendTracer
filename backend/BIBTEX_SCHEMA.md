# BibTeX Schema Design for SmartTrendTracer

## MongoDB BibTeX Storage Structure

### Current Implementation
Papers collection stores BibTeX data in the following fields:

```javascript
{
  _id: ObjectId("..."),
  title: "Paper Title",
  // ... other paper fields ...
  
  // BibTeX Related Fields
  bibtex: "Raw BibTeX string from DBLP or other sources",
  bibtex_parsed: {  // Optional parsed structure for future use
    entry_type: "article|inproceedings|book|misc|...",
    citation_key: "DBLP:journals/tkde/PanLWCWW24",
    fields: {
      author: "Shirui Pan and Linhao Luo and ...",
      title: "Unifying Large Language Models...",
      journal: "IEEE Trans. Knowl. Data Eng.",
      year: "2024",
      volume: "36",
      number: "7",
      pages: "3580--3599",
      doi: "10.1109/TKDE.2024.3352100",
      url: "https://doi.org/10.1109/TKDE.2024.3352100"
    }
  },
  
  // Source tracking
  dblp_key: "journals/tkde/PanLWCWW24",
  dblp_url: "https://dblp.org/rec/journals/tkde/PanLWCWW24",
  dblp_metadata: { /* Full DBLP metadata */ },
  dblp_attached_at: ISODate("2025-09-01T16:28:00.000Z"),
  
  // Future fields for own papers
  bibtex_custom: {  // User's custom BibTeX overrides
    entry_type: "article",
    citation_key: "custom_key_2025",
    fields: { /* Custom field values */ }
  },
  bibtex_history: [  // Track changes over time
    {
      timestamp: ISODate("..."),
      source: "dblp|manual|import",
      bibtex: "...",
      changed_by: "user_id or system"
    }
  ]
}
```

## BibTeX Entry Types Support

### Core Types (Must Support)
- `@article` - Journal articles
- `@inproceedings` - Conference papers
- `@book` - Books
- `@incollection` - Book chapters
- `@phdthesis` - PhD dissertations
- `@mastersthesis` - Master's theses
- `@techreport` - Technical reports
- `@misc` - Miscellaneous (preprints, etc.)

### Extended Types (Future)
- `@proceedings` - Conference proceedings
- `@inbook` - Part of a book
- `@booklet` - Printed work without publisher
- `@manual` - Technical documentation
- `@unpublished` - Unpublished works

## Field Mappings

### Required Fields by Type
```javascript
const REQUIRED_FIELDS = {
  article: ['author', 'title', 'journal', 'year'],
  inproceedings: ['author', 'title', 'booktitle', 'year'],
  book: ['author|editor', 'title', 'publisher', 'year'],
  incollection: ['author', 'title', 'booktitle', 'year'],
  phdthesis: ['author', 'title', 'school', 'year'],
  mastersthesis: ['author', 'title', 'school', 'year'],
  techreport: ['author', 'title', 'institution', 'year'],
  misc: ['author', 'title', 'year']
};
```

### Optional Fields (All Types)
- `abstract` - Paper abstract
- `keywords` - Keywords/tags
- `doi` - Digital Object Identifier
- `url` - Electronic location
- `arxivid` - ArXiv identifier
- `note` - Additional notes
- `month` - Publication month
- `volume` - Journal volume
- `number` - Journal issue number
- `pages` - Page range
- `series` - Book series
- `edition` - Book edition
- `isbn` - Book ISBN
- `issn` - Journal ISSN

## API Endpoints

### Current Endpoints
```
GET  /api/papers/{paper_id}           - Returns paper with bibtex field
POST /api/dblp/attach-metadata/{id}   - Attach DBLP BibTeX to paper
GET  /api/dblp/metadata/{dblp_key}    - Get BibTeX from DBLP
```

### Future Endpoints (for own paper management)
```
POST   /api/papers/{id}/bibtex        - Create/update custom BibTeX
PUT    /api/papers/{id}/bibtex        - Update BibTeX entry
DELETE /api/papers/{id}/bibtex        - Remove custom BibTeX
GET    /api/papers/bibtex/export      - Export multiple BibTeX entries
POST   /api/papers/bibtex/import      - Import BibTeX file
GET    /api/papers/bibtex/validate    - Validate BibTeX format
POST   /api/papers/bibtex/generate    - Generate BibTeX from metadata
```

## BibTeX Operations

### 1. Parsing BibTeX
```python
def parse_bibtex(bibtex_string: str) -> dict:
    """Parse BibTeX string into structured format"""
    # Extract entry type and key
    # Parse fields with proper handling of:
    # - Multi-line values
    # - Nested braces
    # - Special characters
    # - LaTeX commands
```

### 2. Generating BibTeX
```python
def generate_bibtex(paper: dict) -> str:
    """Generate BibTeX from paper metadata"""
    # Determine entry type
    # Format required fields
    # Add optional fields
    # Handle special characters
    # Ensure valid LaTeX
```

### 3. Merging BibTeX
```python
def merge_bibtex(dblp: str, custom: dict) -> str:
    """Merge DBLP BibTeX with custom overrides"""
    # Parse DBLP BibTeX
    # Apply custom field overrides
    # Preserve DBLP fields not overridden
    # Generate merged BibTeX
```

## Export Formats

### Individual Export
- Plain BibTeX (.bib)
- BibLaTeX format
- RIS format (future)
- EndNote format (future)

### Bulk Export
```python
def export_bibtex_collection(paper_ids: List[str]) -> str:
    """Export multiple papers as BibTeX collection"""
    # Query papers by IDs
    # Collect BibTeX entries
    # Ensure unique citation keys
    # Sort by author/year
    # Return concatenated BibTeX
```

## Frontend Integration

### BibTeXViewer Component Features
- ✅ Formatted view with field breakdown
- ✅ Raw BibTeX code view
- ✅ Copy to clipboard
- ✅ Download as .bib file
- ✅ DBLP source indication
- ✅ Entry type badges
- ✅ Generated BibTeX fallback

### Future UI Enhancements
- [ ] BibTeX editor with syntax highlighting
- [ ] Field validation and auto-completion
- [ ] Citation key generator
- [ ] Preview in different citation styles (APA, MLA, Chicago)
- [ ] Batch export interface
- [ ] Import from .bib files
- [ ] Duplicate detection
- [ ] Citation graph visualization

## Data Quality

### Validation Rules
1. Citation keys must be unique across database
2. Required fields must be non-empty
3. Year must be valid (1900-current+1)
4. DOI format validation if present
5. URL validation if present
6. Author names properly formatted

### Sanitization
- Remove/escape LaTeX special characters in user input
- Preserve LaTeX commands in DBLP imports
- Handle Unicode properly
- Normalize whitespace
- Fix common formatting issues

## Migration Notes

### From Current State
1. All papers with DBLP metadata have `bibtex` field populated
2. Frontend BibTeXViewer component handles display
3. API returns bibtex in paper response

### Next Steps
1. Add `bibtex_parsed` field for structured storage
2. Implement custom BibTeX override system
3. Add bulk export functionality
4. Create BibTeX editor component
5. Implement citation style formatting

## Best Practices

### Storage
- Always store raw BibTeX string for compatibility
- Parse to structured format for searching/filtering
- Track source (DBLP, manual, generated)
- Maintain edit history for important papers

### API Design
- Return both raw and parsed formats
- Support partial updates
- Validate before storing
- Handle character encoding properly

### UI/UX
- Show source of BibTeX data
- Indicate if generated vs. official
- Provide multiple export options
- Enable easy editing for own papers
- Support batch operations

## Future Extensions

### Citation Management
- Track which papers cite each other
- Generate bibliography for own papers
- Suggest related papers
- Check for citation updates

### Integration
- Zotero connector
- Mendeley sync
- Overleaf integration
- Google Scholar tracking
- CrossRef API integration

### Analytics
- Citation impact metrics
- Co-author networks
- Publication timeline
- Venue analysis