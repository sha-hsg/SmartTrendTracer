# SmartTrendTracer - Claude Assistant Documentation

## Project Overview
SmartTrendTracer is a comprehensive AI content monitoring system that tracks both Twitter/X accounts and Substack newsletters to identify emerging trends, hot topics, and declining discussions in the AI space.

## Core Components

### 1. Twitter/X Monitoring
Tracks 7 specific AI-related accounts for real-time trends.

### 2. Substack Newsletter Collection
Collects and analyzes newsletters from both direct Gmail subscriptions and forwarded emails.

## Key Twitter Accounts Monitored
1. @OpenAI (ID: 4398626122)
2. @emollick (ID: 39125788)
3. @stanfordnlp (ID: 118263124)
4. @AnthropicAI (ID: 1353836358901501952)
5. @GoogleDeepMind (ID: 4783690002)
6. @huggingface (ID: 778764142412984320)
7. @sama (ID: 1605)

## Substack Newsletter Authors

### Direct Gmail Subscriptions
- **Ethan Mollick** (One Useful Thing) - AI strategy and implications
- **David Szabo-Stuban** (LumberjackAI) - Technical AI insights

### Forwarded Newsletters (from university email)
- **Gary Marcus** - Critical AI analysis
- **Nathan Lambert** - AI research and development
- **Sebastian Raschka** - Machine learning fundamentals

## Recent Enhancements (January 13, 2025)

### Phase 4: Trends Analysis & Cross-Source Integration - COMPLETE

#### Unified Timeline View
- **Component**: `UnifiedTimelineView.tsx`
- **Features**:
  - Chronological timeline of papers, tweets, and articles
  - Time window selection (7-90 days)
  - Type filtering (all/papers/tweets/articles)
  - Color-coded items by source type
  - Real-time statistics display

#### Research Analytics Dashboard
- **Component**: `ResearchAnalyticsDashboard.tsx`
- **Features**:
  - Popular papers with engagement metrics
  - Emerging topics with growth visualization
  - Active researchers and their focus areas
  - Impact analysis for individual papers
  - Cross-source mention detection

#### Backend Trend Services
- **Paper Trends Service**: `paper_trends_service.py`
  - Popular papers ranking
  - Emerging topic detection
  - Author activity analysis
  - Cross-source mention finding
  - Topic evolution tracking
  - Citation network analysis

#### API Endpoints
- `GET /api/papers/trends/popular` - Most popular papers
- `GET /api/papers/trends/emerging-topics` - Rising research topics
- `GET /api/papers/trends/active-authors` - Most active researchers
- `GET /api/papers/trends/cross-mentions/{paper_id}` - Find paper mentions in social media
- `GET /api/papers/trends/topic-evolution` - Track topic changes over time
- `GET /api/papers/trends/citation-network/{paper_id}` - Build citation networks
- `GET /api/papers/trends/unified-timeline` - Combined timeline across all sources
- `GET /api/papers/trends/research-impact/{paper_id}` - Comprehensive impact metrics

### Phase 5: Advanced Features - COMPLETE

#### Knowledge Graph Visualization
- **Component**: `PaperKnowledgeGraph.tsx`
- **Library**: react-force-graph-2d
- **Features**:
  - Interactive force-directed graph
  - Color-coded nodes (papers, authors, citations)
  - Zoom, pan, and center controls
  - Node click interactions
  - Real-time statistics
  - Visual legend for node types

#### AI-Powered Paper Analytics
- **Component**: `PaperAdvancedDashboard.tsx`
- **Features**:
  - Paper recommendations based on similarity
  - AI-generated summaries with key insights
  - GitHub repository link extraction
  - ArXiv paper import functionality
  - External resource links (Semantic Scholar, Google Scholar)

#### Advanced Backend Services
- **Service**: `paper_advanced_service.py`
  - Paper recommendation system (Jaccard similarity)
  - AI summarization with GPT-4
  - Knowledge graph builder
  - ArXiv API integration
  - GitHub link extraction
  - Author collaboration network
  - Semantic Scholar integration (placeholder)

#### Advanced API Endpoints
- `GET /api/papers/advanced/recommendations/{paper_id}` - Get similar papers
- `POST /api/papers/advanced/summarize` - Generate AI summary
- `GET /api/papers/advanced/knowledge-graph` - Build knowledge graph
- `POST /api/papers/advanced/import-arxiv` - Import from ArXiv
- `GET /api/papers/advanced/github-links/{paper_id}` - Extract GitHub links
- `GET /api/papers/advanced/author-network` - Get collaboration network

### Critical Tag System Fix - COMPLETE (January 13, 2025)

#### Problem Identified
The tag system had fundamental architectural issues preventing cross-compatibility between flat tags and the hierarchical ontology:
- Tags stored as strings instead of concept references
- Inconsistent capitalization across content types
- Broken hierarchy filtering
- No proper synonym resolution
- Tag filtering failed for papers and articles

#### Solution Implemented

##### UnifiedTagService
- **Location**: `app/services/unified_tag_service.py`
- **Features**:
  - Handles all tag variations (original, slugified, capitalized)
  - Proper hierarchy resolution with parent/child relationships
  - Case-insensitive matching while preserving display names
  - Cross-content-type compatibility
  - Synonym and descendant tag inclusion
  - Smart tag normalization with proper noun preservation

##### API Integration
- **Updated APIs**:
  - `/api/tweets` - Now uses UnifiedTagService for filtering
  - `/api/papers` - Integrated UnifiedTagService with hierarchy support
  - `/api/substack/articles` - Added UnifiedTagService filtering
- **New Parameter**: `use_ontology=true/false` for hierarchy control
- **Tag Normalization**: Applied when adding new tags to maintain consistency

##### Tag Consistency Tools
- **Script**: `check_tag_consistency.py`
- **Commands**:
  ```bash
  # Analyze tag inconsistencies
  python check_tag_consistency.py --analyze
  
  # Fix tag consistency issues
  python check_tag_consistency.py --fix
  
  # Test tag filtering
  python check_tag_consistency.py --test "machine-learning"
  ```

#### Tag System Analysis
- **Report**: `TAG_SYSTEM_ANALYSIS.md`
- Documents all issues found and recommended long-term fixes
- Provides migration strategy for proper foreign key relationships
- Includes testing checklist for tag functionality

## Recent Enhancements (August 12, 2025)

### 1. RAG Search System - Complete Implementation
Fully functional AI-powered search with modern UI:

#### Features:
- **Working RAG Endpoints**: Fixed 404 errors, all endpoints now operational
- **Modern UI with shadcn/ui**: Complete redesign using Tailwind CSS and shadcn components
- **Index Management**: Real-time index status display with document count
- **Rebuild Capability**: One-click index rebuild button with progress tracking
- **Auto-refresh**: Automatic status updates during index building
- **1,740 Documents Indexed**: Full corpus of tweets and articles searchable

#### Technical Implementation:
- Backend: `app/api/rag_simple.py` - Simplified, working RAG endpoints
- Frontend: `RAGSearchModern.tsx` - Modern interface with shadcn/ui components
- Endpoints:
  - `GET /api/rag/stats` - Index statistics
  - `GET /api/rag/sample-questions` - Sample queries
  - `POST /api/rag/ask` - AI-powered question answering
  - `POST /api/rag/rebuild` - Rebuild search index

#### Manual Index Rebuild:
```bash
cd backend
python rebuild_rag_index.py
```

### 2. Tag Ontology Manager - Modern UI & Extended Details
Complete modernization with shadcn/ui and enhanced concept information:

#### UI Modernization:
- **shadcn/ui Components**: Cards, Buttons, Inputs, Badges, Tabs, Dialogs
- **Responsive Layout**: 3-column grid (tree, details, actions)
- **Tabbed Interface**: Organized Details, Synonyms, and Create New tabs
- **Visual Hierarchy**: Color-coded badges, icons for clarity
- **Smooth Interactions**: Hover effects, loading states, auto-dismiss alerts

#### Extended Concept Details:
- **Parent Concept**: Shows parent with clickable navigation
- **Child Concepts List**: Scrollable list of all direct children
- **Usage Statistics**:
  - Tweet count with Twitter icon
  - Article count with document icon
  - Total usage across system
- **Hierarchy Navigation**: Click to navigate between parent/child concepts

#### Backend Enhancements:
- Enhanced `/api/ontology/concept/{id}` endpoint
- Returns parent info, children list, and usage statistics
- Counts include all synonyms and mapped tags

### 3. UI Component Migration to shadcn/ui
Systematic migration to shadcn/ui component library:

#### Components Added:
- `button.tsx`, `card.tsx`, `input.tsx`, `badge.tsx`
- `dialog.tsx`, `separator.tsx`, `scroll-area.tsx`
- `alert.tsx`, `tooltip.tsx`, `tabs.tsx`, `textarea.tsx`
- `label.tsx` - Form labels with proper accessibility

#### Benefits:
- Consistent design system across application
- Full TypeScript support
- Accessibility via Radix UI primitives
- Customizable with Tailwind CSS variables
- Professional, modern appearance

## Recent Enhancements (January 11, 2025)

### 1. Tag Hierarchy Toggle in Faceted Browser
Added a "Hierarchy View" toggle to switch between raw tags and organized hierarchy:

#### Features:
- **Toggle Button**: Switch between 🏷️ All Tags (757 raw tags) and 📊 Hierarchy (116 organized concepts)
- **Hierarchical Display**: Shows 8 root categories with indented children
- **Smart Filtering**: Parent categories include all child tags and synonyms when selected
- **Visual Enhancements**: Color-coded toggle, proper indentation, hover effects
- **Aggregate Counts**: Parent concepts show total tweets from all children

#### Implementation:
- Backend endpoint: `/api/v2/tweets/tweets/hierarchy-facets`
- Frontend component: `FacetedTweetsDashboard.tsx` with dynamic view switching
- Tag expansion: Parent tags automatically include all descendants in search

### 2. RAG Search Fixed
Fixed AI-powered search functionality with proper LLM configuration:

#### Issues Resolved:
- Fixed `LLMService.config` attribute error (should be `llm_config`)
- Resolved Claude model compatibility with OpenAI client
- Implemented proper fallback to GPT-4o-mini for RAG queries

#### Current Configuration:
- **Search/Embeddings**: Gemini text-embedding-004 for semantic search
- **Answer Generation**: GPT-4o-mini for generating responses
- **Hybrid Approach**: Gemini finds relevant content, GPT-4o-mini generates answers

### 3. UI Component Library Migration to shadcn/ui
Complete migration to shadcn/ui component library for consistent, modern UI:

#### Installation and Configuration:
- **shadcn CLI**: Initialized with New York style and Neutral color scheme
- **TypeScript Path Aliases**: Added `@/*` alias for clean imports
- **Tailwind Integration**: Fixed content paths and CSS variable system
- **Vite Configuration**: Updated with path resolution for aliases

#### Components Installed:
- **Core Components**: button, input, dialog, badge, card
- **Layout Components**: separator, scroll-area
- **Feedback Components**: alert, tooltip
- **Utility Functions**: cn() helper for className merging

#### Benefits:
- **Accessibility**: Built on Radix UI primitives with ARIA support
- **Customization**: Components copied locally for full control
- **Type Safety**: Full TypeScript support with proper types
- **Consistent Styling**: CSS variables for theming
- **Modern Design**: Clean, professional appearance

#### Usage:
```tsx
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
```

## Recent Enhancements (January 10, 2025)

### 1. Text Selection and Context Menu for Content Tagging
Added comprehensive text selection and context menu functionality:

#### Twitter View:
- **Text Selection**: Select any text within tweets for tagging
- **Context Menu**: Right-click on selected text to open context menu
- **Tag Creation**: Create tags from selected text with preserved capitalization
- **Smart Positioning**: Context menu intelligently positions to avoid screen edges
- **Portal Rendering**: Context menu rendered at document root to avoid z-index issues

#### Article View:
- **Persistent Selection**: Text remains selected until action is taken
- **Multiple Actions**: Context menu offers Highlighting, Create Snippet, and Tag Creation
- **Tag Creation Form**: Edit selected text before creating tag
- **Capitalization Preserved**: Tags maintain original capitalization for proper nouns

### 2. Enhanced UI Components

#### Twitter Cards:
- **X Button**: Circular blue gradient button with X logo to open original tweet
- **Hover Effects**: Smooth scale and shadow animations on hover
- **Compact Design**: Replaced double-click with dedicated button for better UX
- **Text Selection Support**: Tweet text is selectable for context menu actions

#### Tag Suggestions:
- **Custom Tag Capitalization**: Custom tags preserve user-entered capitalization
- **Tag Type Differentiation**: System distinguishes between AI-suggested and custom tags
- **Proper Backend Handling**: Manual tags bypass normalization to preserve capitalization

### 3. Entity Extraction and Automatic Annotation
- **Bulk Annotation**: "Automatic Annotation" button for AI-powered entity extraction
- **Capitalization Preserved**: AI-proposed entity tags maintain natural capitalization
- **Loading Indicators**: Visual feedback during LLM processing
- **Duplicate Handling**: Gracefully handles existing tags without errors

### 4. Error Handling Improvements

#### Twitter Media URLs:
- **Graceful Degradation**: Broken images show placeholder instead of error
- **Auto-Hide**: Media section hides if all images are broken
- **Fallback UI**: "🖼️ Image unavailable" for photos, "🎬 GIF unavailable" for GIFs
- **Smart Caching**: Tracks broken images to prevent repeated load attempts

#### Context Menu Positioning:
- **Boundary Detection**: Prevents menu from appearing off-screen
- **Above Cursor**: Positions above when near bottom edge
- **Z-Index Management**: Ensures menu appears above all UI elements
- **Event Propagation**: Proper event stopping to prevent "running away" behavior

## Recent Enhancements (August 10, 2025)

### 1. Substack Integration
Complete Gmail-based newsletter collection system with:
- **Automatic email parsing** from Gmail API
- **HTML to Markdown conversion** preserving article structure
- **Image preservation** (filters tracking pixels, keeps content images)
- **Forwarded email handling** for university-forwarded newsletters
- **Article viewer** with markdown rendering and highlighting
- **Snippet annotation** system for capturing key insights
- **AI summarization** using GPT-4 for article summaries

### 2. Twitter Timezone Fix
Fixed critical timezone issues affecting tweet collection:
- **Problem**: Naive datetime objects caused incorrect sorting and duplicate detection
- **Solution**: All 3,269+ timestamp fields now use UTC timezone format
- **Impact**: Fixed @sama tweet collection issues and improved reliability

### 3. UI Improvements
- **Markdown rendering** in article tiles and summaries
- **Scrollable summaries** with proper styling
- **Clean previews** for all forwarded articles (removed HTML artifacts)
- **Database caching** for generated summaries

### 4. Automatic Footer Removal
- **Removes copyright notices** and author attribution from article endings
- **Strips promotional content** like "Start writing" and "Get the app" buttons
- **Cleans address information** from newsletter footers
- **Integrated into Gmail collector** for automatic cleaning during collection
- **Handles manually cleaned articles** gracefully (won't break on already-cleaned content)

## Recent Enhancements (August 8, 2025)

### 1. Enhanced Tag Suggestion System with Semantic Similarity
The system now provides intelligent tag suggestions using both existing tags and AI-generated new tags.

#### Features:
- **Dual Suggestions**: 
  - 🔍 **Existing Tags** (Green in UI): Semantically similar tags from vector store
  - ✨ **New Tags** (Purple in UI): AI-generated tags for new concepts
- **Vector Store**: FAISS-based index with OpenAI embeddings for 600+ existing tags
- **Semantic Search**: Finds existing tags with 50%+ similarity to tweet content
- **Usage Statistics**: Shows how many times each existing tag has been used
- **Smart Ranking**: Popular tags (high usage count) are boosted in results

#### Technical Implementation:
```python
# Vector store for semantic similarity
backend/app/services/vector_store_openai.py  # OpenAI embeddings + FAISS
backend/build_vector_store.py                 # Build/rebuild vector store

# Enhanced LLM service with fallback chain
backend/app/services/llm_service.py          # GPT-4o-mini → spaCy → Keywords
backend/app/services/spacy_tagger.py         # NLP-based fallback

# API endpoint
POST /api/tags/suggest/{tweet_id}            # Returns existing + new suggestions
```

### 2. Server-Side Tag Filtering Fix
Fixed issue where tags with special characters weren't filtering correctly.

#### Problem:
- Frontend was only loading first 100 tweets
- Client-side filtering missed tweets outside that range
- Tags like "Research & Development" and "80GB GPU" appeared to have no tweets

#### Solution:
- Implemented server-side filtering in `/api/tweets?tag={tag_name}`
- Properly handles URL encoding for special characters
- Works with entire database, not just first 100 tweets

### 3. Intelligent Fallback System
Three-tier fallback for tag generation with debug logging:

1. **Primary**: OpenAI GPT-4o-mini API
2. **Secondary**: spaCy NLP (if installed) - for truncated retweets
3. **Tertiary**: Simple keyword extraction

Debug logs explain why fallback is used:
```
DEBUG: Using fallback - Truncated retweet detected (ellipsis: True, length: 121)
DEBUG: Reason - Retweets with ellipsis cannot be properly analyzed by LLM
DEBUG: spaCy fallback successful, extracted 5 tags
```

## Collecting New Tweets (Python)

### Daily Collection Commands

#### 1. **Main Collection (Recommended)**
```bash
cd backend
python collect_tweets.py
```
- Collects up to 50 recent tweets per account
- If no new tweets, automatically collects 7 days of history
- Shows statistics after collection

#### 2. **Smart Collection with Rate Limiting**
```bash
python smart_collect.py
```
- Includes automatic delays between API calls
- Shows progress with countdown timers
- Handles rate limits gracefully

#### 3. **Force Collection (Reset and Collect)**
```bash
python force_collect.py
```
- Resets collection state
- Forces collection even if recently run

#### 4. **Scheduled Collection**
```bash
python scheduled_collector.py
```
- Runs collection on a schedule
- Good for automated/cron setups

#### 5. **Monitor Collection Progress**
```bash
python monitor_collection.py
```
- Shows real-time collection statistics
- Updates every 5 seconds

### Check Collection Status

```bash
# Check last collection time
python check_collection_state.py

# View database statistics
sqlite3 ../data/tweets.db "SELECT COUNT(*) FROM tweets;"
sqlite3 ../data/tweets.db "SELECT author_username, COUNT(*) FROM tweets GROUP BY author_username;"

# Check most recent tweet
sqlite3 ../data/tweets.db "SELECT MAX(created_at) FROM tweets;"
```

### If Rate Limited

If you encounter rate limit errors (429):
```bash
# Wait and collect with automatic retry
python wait_and_collect.py

# Or use smart collect with built-in delays
python smart_collect.py
```

### Best Practice - Daily Workflow

```bash
# 1. Collect new tweets
cd backend
python collect_tweets.py

# 2. Process and tag them
python app/main.py  # Start the API server
# Then use the web interface to review and tag

# 3. Generate trend analysis
python app/analyzers/enhanced_trend_analyzer.py
```

## API Endpoints

### Tag Suggestions
```http
POST /api/tags/suggest/{tweet_id}
```
Response:
```json
{
  "tweet_id": "123",
  "existing_suggestions": [
    {
      "tag": "artificial-intelligence",
      "score": 0.723,
      "usage_count": 45,
      "type": "existing"
    }
  ],
  "new_suggestions": [
    {
      "tag": "gpt-5-capabilities",
      "type": "new",
      "model": "gpt-4o-mini"
    }
  ],
  "already_tagged": ["ai", "openai"],
  "model_used": "gpt-4o-mini",
  "total_suggestions": 8
}
```

### Tweet Filtering
```http
GET /api/tweets?tag={tag_name}&limit=100
```
- Properly encode tag names: `Research & Development` → `Research%20%26%20Development`
- Server-side filtering for performance
- Returns only tweets with specified tag

## Configuration Files

### llm.json
```json
{
  "models": {
    "tag_suggestion": {
      "model": "gpt-4o-mini",
      "temperature": 0.3,
      "max_tokens": 500
    },
    "summarization": {
      "model": "gpt-4o-mini",  // Changed from o1-mini
      "temperature": 0.3
    }
  }
}
```

### Environment Variables
```bash
OPENAI_API_KEY=your_key_here  # Required for embeddings and tag generation
```

## Database Schema Updates

### Tags Table
- Stores all tags with relationships to tweets
- Used for both filtering and vector store building
- Supports special characters (spaces, &, hyphens, etc.)

### Vector Store
- Location: `data/vector_store/`
- Files:
  - `faiss_index.bin` - FAISS index for similarity search
  - `metadata.pkl` - Tag metadata (counts, contexts)
  - `embeddings_cache.pkl` - Cached OpenAI embeddings

## Frontend Updates

### TagSuggestionModal Component
- Displays existing and new suggestions separately
- Color coding:
  - Green tags = existing (with usage stats)
  - Purple tags = new AI-generated
- Hover tooltips show similarity scores and usage counts

### Dashboard Component
- Server-side filtering via API
- Proper URL encoding for special characters
- Removed client-side filtering for better performance

## Testing Scripts

```bash
# Test tag suggestions
python backend/test_enhanced_tags.py

# Test vector store
python backend/test_vector_search.py

# Test tag filtering
python backend/test_tag_filtering.py

# Build/rebuild vector store
python backend/build_vector_store.py
```

## Common Issues & Solutions

### Tags Not Filtering
**Issue**: Tags with special characters show "No tweets found"
**Solution**: Implemented server-side filtering with proper URL encoding

### Empty Summarization
**Issue**: Summarization returns empty despite 200 OK
**Solution**: Switched from o1-mini to gpt-4o-mini (o1-mini is reasoning model, not suitable for summarization)

### Fallback Not Working
**Issue**: spaCy fallback fails
**Solution**: Install spaCy in virtual environment:
```bash
source venv/bin/activate
pip install spacy
python -m spacy download en_core_web_sm
```

### Rate Limiting
**Issue**: OpenAI API rate limits
**Solution**: 
- Embeddings are cached in `embeddings_cache.pkl`
- Batch processing for vector store building
- Fallback to local NLP when API fails

## Performance Optimizations

1. **Vector Store Caching**: Embeddings cached to reduce API calls
2. **Server-Side Filtering**: More efficient than client-side
3. **Batch Processing**: Vector store builds in batches of 20
4. **FAISS Index**: Fast similarity search even with 600+ tags

## Future Enhancements

1. **Tag Synonyms**: Group similar tags (e.g., "AI" and "artificial-intelligence")
2. **Tag Hierarchies**: Parent-child relationships for tags
3. **Auto-Tagging**: Automatically tag new tweets on collection
4. **Tag Trends**: Track tag usage over time
5. **Custom Embeddings**: Fine-tune embeddings for AI/ML domain

## Usage Guide - New Features (January 2025)

### Creating Tags from Selected Text

#### In Twitter View:
1. **Select text** in any tweet by clicking and dragging
2. **Right-click** on the selected text
3. Choose **"🏷️ Tag Creation"** from context menu
4. **Edit the tag** if needed (preserves capitalization)
5. Click **"Create Tag"** to add to tweet

#### In Article View:
1. **Select text** in the article content
2. **Right-click** for context menu with multiple options:
   - **🎨 Highlighting**: Color-code important text
   - **📝 Create Snippet**: Save with annotation
   - **🏷️ Create Tag**: Create tag from selection
3. **Edit and apply** as needed

### Tag Capitalization Rules
- **Manual tags**: Preserve exact capitalization as entered
- **Custom tags**: Maintain user's capitalization choice
- **AI-suggested tags**: Keep AI's proposed capitalization
- **Normalized tags**: Only for system-generated tags

### Opening Original Tweets
- Click the **blue X button** in tweet header
- Hover for "Open original tweet in X/Twitter" tooltip
- Opens tweet in new browser tab

## Workflow for Tag Management

1. **View Tweet** → Click "Suggest Tags"
2. **Review Suggestions**:
   - Green tags: Already used elsewhere, semantically similar
   - Purple tags: New AI-generated suggestions
3. **Select Tags** → Apply to tweet
4. **Filter by Tag** → Click tag in Tag Cloud
5. **Server Filters** → Shows all tweets with that tag

## Dependencies

### Backend
```
fastapi
sqlalchemy
openai
faiss-cpu
spacy
sentence-transformers  # Optional, for local embeddings
```

### Frontend
```
react
axios
typescript
```

## Debug Mode

To enable debug logging:
```python
# In backend/app/services/llm_service.py
# Debug messages already implemented, showing:
# - Why fallback is triggered
# - Which model is used
# - Token length issues
# - API failures
```

## Substack Collection Commands

### Collect Newsletters from Gmail
```bash
cd backend

# Collect all Substack newsletters (direct + forwarded)
python -m app.collectors.gmail_substack_collector

# Collect only forwarded newsletters
python -m app.collectors.gmail_substack_collector --forwarded

# Collect with specific date range
python -m app.collectors.gmail_substack_collector --max 100
```

### Manage Substack Articles
```bash
# View Substack dashboard
cd frontend
npm start
# Navigate to: http://localhost:3000/substack

# Generate summaries for articles
python summarize_articles.py

# Fix previews for forwarded articles
python fix_previews.py

# Clean footers from existing articles
python clean_substack_footers.py --clean

# Test footer removal
python clean_substack_footers.py --test
```

### Configuration Files

#### forwarded_authors.json
```json
{
  "forwarded_authors": [
    {"name": "Nathan Lambert", "email": "robotic@substack.com"},
    {"name": "Gary Marcus", "email": "garymarcus@substack.com"},
    {"name": "Sebastian Raschka", "email": "sebastianraschka@substack.com"}
  ]
}
```

## Twitter Collection Commands

### Standalone Tweet Collector Service
```bash
cd backend

# Start the tweet collector service (runs every 15 minutes)
python tweet_collector_service.py

# Check collector logs
tail -f tweet_collector.log
```

### Manual Collection
```bash
# Collect recent tweets
python collect_tweets.py

# Smart collection with rate limiting
python smart_collect.py

# Force collection (reset state)
python force_collect.py
```

## Database Maintenance

### Fix Timezone Issues
```bash
# Fix Twitter timestamps
python -c "from app.models import get_db; from sqlalchemy import text; db = next(get_db()); db.execute(text('UPDATE tweets SET created_at = created_at || \"+00:00\" WHERE created_at NOT LIKE \"%+%\"')); db.commit()"

# Check timestamp formats
sqlite3 data/tweets.db "SELECT COUNT(*) FROM tweets WHERE created_at LIKE '%+00:00';"
```

### Check Database Status
```bash
# Twitter stats
sqlite3 data/tweets.db "SELECT author_username, COUNT(*) FROM tweets GROUP BY author_username;"

# Substack stats
sqlite3 data/tweets.db "SELECT a.name, COUNT(s.id) FROM substack_authors a LEFT JOIN substack_articles s ON a.id = s.author_id GROUP BY a.name;"
```

## Known Issues & Solutions

### Issue: Twitter media URLs return 404 errors
**Cause**: Twitter media URLs expire after a period of time
**Symptom**: Images/videos in tweets show as broken or 404 errors
**Solution**: 
- Frontend gracefully handles broken images with placeholder text
- Media section auto-hides if all images are broken
- To refresh media URLs, re-collect recent tweets:
  ```bash
  cd backend
  python collect_tweets.py
  ```
**Note**: This is a limitation of Twitter's API - media URLs are temporary and expire

### Issue: @sama tweets showing "already in database"
**Cause**: Timezone mismatch in datetime objects
**Solution**: Run timezone fix script (see Database Maintenance)

### Issue: Forwarded Substack articles have HTML in previews
**Cause**: HTML artifacts in markdown content
**Solution**: Run `python fix_previews.py`

### Issue: Gary Marcus articles attributed to Ethan Mollick
**Cause**: Email parsing confusion with forwarded content
**Solution**: Check author attribution and manually correct if needed

### Issue: Rate limiting on Twitter API
**Cause**: Too many requests in 15-minute window
**Solution**: Use `tweet_collector_service.py` which includes proper rate limiting

## API Endpoints (Extended)

### Substack Endpoints
```http
GET /api/substack/articles
GET /api/substack/articles/{article_id}
POST /api/substack/articles/{article_id}/summarize
POST /api/substack/articles/{article_id}/snippets
GET /api/substack/authors
```

### Twitter Endpoints
```http
GET /api/tweets
GET /api/tweets/{tweet_id}
POST /api/tags/suggest/{tweet_id}
GET /api/trends
```

## System Completeness Status

### ✅ Phase 1-3: Basic PDF Papers (COMPLETE)
- PDF upload and processing
- Text extraction and metadata parsing
- Paper browsing and viewing
- PDF viewer with react-pdf
- Tagging and snippet management
- RAG search integration

### ✅ Phase 4: Trends & Analytics (COMPLETE)
- Unified timeline across all sources
- Research analytics dashboard
- Cross-source mention detection
- Citation network analysis
- Topic evolution tracking
- Impact metrics calculation

### ✅ Phase 5: Advanced Features (COMPLETE)
- Knowledge graph visualization
- AI-powered paper summaries
- Paper recommendation system
- ArXiv import functionality
- GitHub repository extraction
- Author collaboration networks

### 🔧 Critical Fixes Applied
- **Tag System**: Unified service for cross-compatibility
- **Filtering**: Fixed hierarchy and synonym resolution
- **Capitalization**: Consistent handling across content types

## Known Issues & Future Improvements

### Database Architecture
- Tags need foreign key relationships to concepts
- Requires migration to unified tag_instances table
- See `TAG_SYSTEM_ANALYSIS.md` for detailed plan

### UI Enhancements Needed
- Consistent tag display across all views
- Better error handling for broken media URLs
- Performance optimization for large datasets

### Integration Opportunities
- Complete Semantic Scholar API integration
- Add CrossRef API for DOI metadata
- Implement Google Scholar tracking
- Add real-time Twitter streaming

## Quick Start Commands

### Daily Operations
```bash
# Collect tweets
cd backend
python collect_tweets.py

# Collect newsletters
python -m app.collectors.gmail_substack_collector

# Start services
cd backend && python app/main.py  # API on :8000
cd frontend && npm run dev         # UI on :3000
```

### Maintenance
```bash
# Fix timezone issues
python fix_twitter_timestamps.py

# Clean article footers
python clean_substack_footers.py

# Rebuild RAG index
python rebuild_rag_index.py

# Check tag consistency
python check_tag_consistency.py --analyze

# Fix tag consistency issues
python check_tag_consistency.py --fix
```

Last updated: January 13, 2025