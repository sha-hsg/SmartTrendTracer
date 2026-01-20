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

## Development Requirements and Standards

### Cross-Platform Portability (MANDATORY)

SmartTrendTracer must work seamlessly on both macOS and Linux systems. All code must follow these requirements:

#### 1. Path Handling - Dynamically Determined Absolute Paths (REQUIRED)

**ALWAYS use dynamically determined absolute paths in shell scripts:**

```bash
# ✅ CORRECT - Portable across systems
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="$SCRIPT_DIR/logs/startup.log"
DATA_DIR="$SCRIPT_DIR/data"

# ❌ WRONG - Hardcoded absolute path (breaks portability)
LOG_FILE="/Users/siehan/Documents/Research/SmartTrendTracer/logs/startup.log"

# ❌ WRONG - Relative path (breaks when changing directories)
LOG_FILE="logs/startup.log"  # Breaks after 'cd backend'
```

**Why this matters:**
- Works on any macOS path, any Linux path, any user's home directory
- Immune to directory changes during script execution (`cd backend`, etc.)
- No hardcoded paths that break when moving between machines

#### 2. Virtual Environment Handling (REQUIRED)

**ALWAYS use explicit virtual environment paths, NEVER use `source activate` with background processes:**

```bash
# ✅ CORRECT - Explicit path to venv Python
PYTHON_BIN="venv/bin/python"
nohup $PYTHON_BIN -m uvicorn app.main:app ... &

# ❌ WRONG - Activation doesn't transfer to background processes
source venv/bin/activate
nohup python -m uvicorn app.main:app ... &  # Uses system Python!
deactivate
```

**Rationale:** Background processes started with `nohup ... &` do not inherit shell environment from `source activate`.

**Cross-Platform venv Validation:**
venvs created on macOS have symlinks pointing to macOS Python paths, which break on Linux (and vice versa). Always validate venvs before use:

```bash
# Check if venv is valid (python binary exists and is executable)
check_venv_valid() {
    local venv_path=$1
    if [ -d "$venv_path" ] && [ -x "$venv_path/bin/python" ]; then
        return 0  # Valid
    fi
    return 1  # Invalid - needs recreation
}

# Usage in start_stt.sh
if ! check_venv_valid "venv"; then
    log "venv invalid or has broken symlinks, recreating..."
    rm -rf venv
    python3 -m venv venv
    venv/bin/pip install -r requirements.txt
fi
```

**Key Point:** When syncing project files between macOS and Linux via Syncthing, venvs will have broken symlinks and must be recreated on each platform.

#### 3. MongoDB Cross-Machine Synchronization (REQUIRED)

Each machine runs its own local MongoDB instance. Use sync scripts to synchronize databases when switching machines:

**Workflow:**
```bash
# END of work session on Machine A:
cd backend
./sync-out.sh  # Export MongoDB to mongodb_sync/latest/

# Wait for Syncthing to sync...

# START of work session on Machine B:
cd backend
./sync-in.sh   # Import MongoDB from mongodb_sync/latest/
```

**Key Points:**
- Each machine has independent MongoDB instance on `localhost:27017`
- `sync-out.sh` creates mongodump in `mongodb_sync/latest/`
- `sync-in.sh` imports with `--drop` flag (overwrites local database)
- Only sync when switching machines, not during daily work
- MongoDB indexes are recreated on import (causes 30-60s startup delay on first run)

#### 4. Environment Variables (REQUIRED)

**LLM API keys and credentials MUST be in `~/.env` (user home directory), NOT in project directory:**

```bash
# ✅ CORRECT - ~/.env (synced across machines, not in git)
~/.env contains:
  OPENAI_API_KEY=sk-...
  ANTHROPIC_API_KEY=sk-ant-...
  GOOGLE_API_KEY=...
  GEMINI_API_KEY=...

# ❌ WRONG - backend/.env (project-specific, in gitignore)
backend/.env  # DO NOT USE THIS
```

**Rationale:**
- `~/.env` exists on both Linux and macOS machines
- Contains all LLM keys for all projects
- Not checked into git
- `start_stt.sh` automatically loads `~/.env` using `set -a` (auto-export)

**~/.env Format** (with or without `export` prefix):
```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=...
```

**Automatic Loading in start_stt.sh:**
```bash
if [ -f "$HOME/.env" ]; then
    set -a  # automatically export all variables
    source "$HOME/.env"
    set +a
fi
```

#### 5. Service Startup Timeouts (REQUIRED)

Different services have different startup times. Configure timeouts appropriately:

```bash
# Backend API - 60 seconds (MongoDB index creation takes 44s)
wait_for_service 8000 "Backend API" 60

# Marker Service - 30 seconds (default)
wait_for_service 8002 "Marker Service"

# MinerU Service - 30 seconds (default)
wait_for_service 8003 "MinerU Service"
```

**Why Backend needs 60s:**
- Creates 23 MongoDB indexes on startup
- With 22,000+ documents, index creation takes 30-44 seconds
- Especially slow for text indexes on papers/articles collections

#### 6. Comprehensive Logging (REQUIRED)

All startup scripts must create detailed, timestamped logs:

```bash
# Timestamped log file with absolute path
STARTUP_LOG="$SCRIPT_DIR/logs/startup_$(date +%Y%m%d_%H%M%S).log"

# Log function with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$STARTUP_LOG"
}

# Log important events
log "Starting Backend API Server (port 8000)..."
log "Backend process started with PID: $BACKEND_PID"
log "Using Python: $PYTHON_BIN"
```

**Must include:**
- Timestamp for every log entry
- Process IDs (PIDs) for all services
- Port availability checks
- Service startup timing
- Python/venv paths being used
- MongoDB connection status

#### 7. Platform-Specific Considerations

**MongoDB Service Management:**
```bash
# macOS
brew services start mongodb-community
brew services stop mongodb-community

# Linux
sudo systemctl start mongod
sudo systemctl stop mongod
```

**Scripts must detect platform and use appropriate commands when needed.**

### Summary of MUST Requirements

1. ✅ **Use `$SCRIPT_DIR` pattern** for all paths in shell scripts
2. ✅ **Use explicit venv paths** (`venv/bin/python`), not `source activate`
3. ✅ **Use sync scripts** for MongoDB synchronization between machines
4. ✅ **Put LLM keys in `~/.env`**, never in project directory
5. ✅ **Set appropriate timeouts** (backend needs 60s, others 30s)
6. ✅ **Log everything** with timestamps, PIDs, and timing information
7. ✅ **Test on both macOS and Linux** before considering code complete

## Recent Enhancements (January 20, 2026)

### RAG Search Content Type Filtering Fix - COMPLETE

#### Problem
When searching with multiple content types selected (e.g., Tweets + Articles), only tweets appeared in results despite articles like "AI Agents of the Week" being relevant to queries about "agentic AI".

#### Root Cause
The RAG search used FAISS similarity ranking, which returns results sorted by embedding similarity. With ~11,422 tweets but only ~65 articles in the index, tweets dominated the top rankings and filled all result slots (k=50) before any articles appeared.

**Example**: First article might appear at position 847 in FAISS ranking, but search stopped after collecting 50 results.

#### Solution Implemented
**Proportional blending** when multiple content types are selected:

1. **Collect ALL matching results separately by type** (not just first k)
2. **Ensure minimum quota** from each type:
   - At least 3 items from each selected type
   - Or `k / (2 * num_types)` items
3. **Fill remaining slots** with highest-scoring items across all types
4. **Sort final results** by similarity score

**Code Location**: `backend/app/services/rag_service_concepts.py:312-402`

#### Enhanced Logging Added
```
FIRST ARTICLE at position 847: AI Agents of the Week: Papers You Should Know About
COLLECTED per type (before blending): tweets=11000, articles=65, papers=0
Added 12 tweets (minimum quota)
Added 12 articles (minimum quota)
FINAL results by type: tweets=38, articles=12, papers=0
```

#### Files Modified
- `backend/app/services/rag_service_concepts.py` - Proportional blending logic and debug logging
- `backend/app/services/rag_helpers.py` - Added doc_id and inferred_type parameters
- `backend/app/api/rag_simple.py` - content_types parameter in RAGQuery model

#### Result
When selecting Tweets + Articles, results now include representation from both types instead of being dominated by tweets.

### Cross-Platform Scripts Enhancement - COMPLETE

#### Overview
Complete rewrite of startup/shutdown scripts for seamless macOS ↔ Linux operation.

#### setup_python.sh - New Commands
```bash
./setup_python.sh           # Full setup (backend + frontend)
./setup_python.sh backend   # Backend only (all Python venvs)
./setup_python.sh frontend  # Frontend only (npm install)
./setup_python.sh check     # Check environment status
./setup_python.sh activate  # Print venv activation command
```

#### Features Implemented
| Feature | Description |
|---------|-------------|
| **venv validation** | Detects broken symlinks from other platform, auto-recreates |
| **node_modules check** | Detects wrong platform's native modules (@rollup/rollup-darwin vs linux) |
| **mise integration** | Auto-activates mise for Python version management |
| **API key check** | Validates ~/.env contains required LLM keys |
| **Status display** | Shows all environments, MongoDB status, API keys |

#### stop_stt.sh - CLI Arguments
```bash
./stop_stt.sh              # Interactive (asks about MongoDB)
./stop_stt.sh -y           # Stop MongoDB without asking
./stop_stt.sh -n           # Keep MongoDB running without asking
./stop_stt.sh --help       # Show usage
```

#### Platform-Specific Handling
| Operation | macOS | Linux |
|-----------|-------|-------|
| MongoDB start | `brew services start mongodb-community` | `systemctl start mongod` |
| MongoDB stop | `brew services stop mongodb-community` | `systemctl stop mongod` |
| File timestamps | `date -r` / `stat -f` | `stat -c` |
| Native modules | `@rollup/rollup-darwin-*` | `@rollup/rollup-linux-x64-gnu` |

#### Files Modified
- `setup_python.sh` - Complete rewrite with all features above
- `start_stt.sh` - Fixed `date -r` → `stat -c` for Linux
- `stop_stt.sh` - Added platform detection, CLI args, Linux MongoDB support

#### Workflow beim Plattformwechsel
```bash
# Auf neuem System:
cd backend && ./sync-in.sh     # MongoDB importieren
cd .. && ./setup_python.sh     # Erkennt & fixt alles automatisch
./start_stt.sh                 # Starten
```

---

## Recent Enhancements (January 19, 2026)

### TypeScript Error Cleanup - COMPLETE

#### Overview
Comprehensive TypeScript error cleanup reducing blocking issues and enabling clean production builds.

#### Changes Made

**1. Vite Environment Types**
- Created `frontend/src/vite-env.d.ts` with proper `ImportMetaEnv` interface
- Fixed 6 `import.meta.env` type errors

**2. Interface Extension Conflicts Fixed**
- `ConceptManagementCenter.tsx`: `ConceptTreeNode` no longer extends `Concept` (conflicting `children` types)
- `types/tagConcept.ts`: `TagConceptNode` made standalone interface (same issue)

**3. Missing Interface Properties Added**
| File | Properties Added |
|------|------------------|
| `FacetedPapersDashboard.tsx` | `pdf_path`, `authors_detailed`, `year`, `concepts`, `ai_summary`, `key_findings`, `dblp_url` |
| `GROBIDMetadataPanel.tsx` | `year`, `journal`, `volume`, `pages`, `eprint`, `bibtex_raw`, `dblp_key` |
| `FacetedTweetsDashboardModern.tsx` | `like_count`, `retweet_count`, `reply_count`, `quote_count`, `concepts` |
| `TwitterMediaGalleryModern.tsx` | `preview_image_url`, `alt_text`, `media_key` |
| `TrendAnalysisOverview.tsx` | `peak_day`, `peak_value` |
| `ArticleViewerErrorBoundary.tsx` | `onClose` prop |
| `ArticleViewerModern.tsx` | `subdomain`, `url` in authors array |

**4. Set Type Mismatches Fixed**
- `FacetedArticlesDashboardModern.tsx`: Changed `Set<number>` to `Set<string | number>` for article ID sets

**5. ReactMarkdown v9 Migration**
- Replaced deprecated `inline` prop with `className?.includes('language-')` check
- Added proper type assertions for custom `think` component
- Files: `PaperViewerOptimized.tsx`, `ArticleViewerModern.tsx`, `BookViewerOptimized.tsx`

**6. Component Prop Fixes**
- `FacetedRedditDashboardModern.tsx`: Fixed `TagBadge` usage (use children, not `concept` prop)
- `FacetedRedditDashboardModern.tsx`: Fixed `TagSuggestionModalModern` props
- `FacetedRedditDashboardModern.tsx`: Fixed `SemanticConceptSearch` handler signature
- `FacetedTweetsDashboardModern.tsx`: Removed conflicting `Tweet` import

#### Build Status
- **TypeScript Errors**: 229 (mostly unused variables - non-blocking)
- **Production Build**: ✅ Successful (12.62s)
- **All APIs**: ✅ Working (Papers, Tweets, Articles)

---

## Recent Enhancements (January 4, 2026)

### Paper Date Type Selection for AI Summarization - COMPLETE

#### Feature
Users can now choose between **Import Date** (`created_at`) or **Publication Date** (`published_date`) when filtering papers in AI-Powered Summarization.

#### Implementation
- **Backend** (`analytics_trends_mongodb.py`): Added `paper_date_type` parameter with values `"created"` or `"published"`
- **Frontend** (`SummarizationModern.tsx`): Added toggle buttons for date type selection
- **Fallback Logic**: If `published_date` missing, checks `publication_date` (legacy), then `year`
- **ACL Import** (`acl_anthology.py`): Standardized to use `published_date` field (was `publication_date`)
- **Metadata Endpoint** (`papers_mongodb.py`): Now accepts both `published_date` and `publication_date`

#### Files Modified
- `backend/app/api/analytics_trends_mongodb.py` - paper_date_type parameter
- `backend/app/services/analytics_helpers.py` - date_type in fetch functions
- `backend/app/api/acl_anthology.py` - field name standardization
- `backend/app/api/papers_mongodb.py` - metadata update endpoint
- `frontend/src/components/SummarizationModern.tsx` - Date Type Selector UI

### Paper Analyses Pipeline - "Generate All Analyses" Fix - COMPLETE

#### Problem
The "Generate All Analyses" button (for "All" category) had poor UX:
- Sent all 14 analyses in ONE batch request
- No progress tracking during generation
- 1-7 minute wait with only "Generating All..." spinner
- Timeout risk for large batches

#### Solution
Rewrote `generateAllAnalyses()` to use sequential pattern with real-time progress:

**Before:**
```typescript
// One batch request, no progress
axios.post('/analyses/generate-multiple', {analysis_types: allTypes})
```

**After:**
```typescript
// Sequential with progress tracking
for (let i = 0; i < allAnalyses.length; i++) {
  setBatchProgress({ current: analysisName, completed: i })
  await axios.post('/analyses/generate', { analysis_type })
  setBatchProgress({ completed: i + 1, skipped: skippedCount })
}
```

#### UI Enhancement
Added Progress Bar for "All" tab (same as category view):
- `"3 of 14 completed (2 skipped)"`
- Visual progress bar with percentage
- `"Generating: Layman Summary"` current step indicator

#### Files Modified
- `frontend/src/components/PaperAnalysisPanel.tsx`
  - Lines 614-688: Rewrote `generateAllAnalyses()` function
  - Lines 906-945: Added Progress Bar UI for "All" tab

### ArXiv Import Fix - COMPLETE

#### Problem
ArXiv import failed with: `"cannot unpack non-iterable coroutine object"`

#### Root Cause
`validate_arxiv_id()` is an async endpoint being called without `await`

#### Solution
Replaced async endpoint call with synchronous service method:
```python
# Before (broken)
is_valid, result = validate_arxiv_id(request.url_or_id)

# After (fixed)
validated_id = arxiv_service.extract_arxiv_id(request.url_or_id)
```

#### File Modified
- `backend/app/api/arxiv.py` - Lines 108-121

---

## Recent Enhancements (December 30, 2025)

### Optimistic UI Updates - IN PROGRESS

#### Goal
Nach Aktionen auf Articles/Papers/Tweets soll die Liste lokal aktualisiert werden, ohne Full Refresh.

#### Implemented
- **FacetedSubstackDashboardModern**: Local state updates for add/remove concepts
- **FacetedTweetsDashboardModern**: Local state updates for concept operations
- **FacetedPapersDashboard**: Custom event listener for tag updates from PaperViewer
- **Backend APIs**: Konsistente concept response mit `concept_id`, `slug`, `display_name`

#### Known Issue (DEF-001)
Article Viewer `onClose` callback und Custom Events funktionieren nicht korrekt.
- Event wird dispatched aber Parent empfängt es nicht
- Workaround: Manuell "Refresh" klicken

**Details:** Siehe `DEFECTS.md` und `DEFECTS_OPTIMISTIC_UI.md`

### Fixes Applied
- **Gemini 3 Temperature**: Set to 1.0 in `litellm_config.yaml` to avoid infinite loops
- **ANTHROPIC_API_KEY**: Removed hardcoded check in `articles_mongodb.py`
- **Papers Endpoint**: Added `slug` field to POST `/api/papers/{id}/concepts` response
- **API Key Status Banner**: Added UI warning when LLM API keys are missing

### New Files
- `DEFECTS.md` - Zentrale Mängelliste für alle bekannten Issues
- `DEFECTS_OPTIMISTIC_UI.md` - Detail-Dokumentation für Optimistic UI Issues
- `frontend/src/components/ApiKeyStatusBanner.tsx` - API Key Status Warning

---

## Recent Enhancements (December 26, 2025)

### Topic Explorer & LLM Model Selection Fixes - COMPLETE

#### Topic Explorer Mouse Click Selection Fix
**Problem**: Users could not select topics by clicking with mouse in Topic Explorer dropdown
**Root Cause**: The cmdk library (shadcn/ui Command component) was capturing mouse events and only allowing keyboard selection

**Solution**: Replaced cmdk-based Command component with native HTML elements
- Standard `<input>` for search functionality
- Standard `<div>` elements with `onClick` handlers for topic items
- Added `Search` icon import from lucide-react

**Files Modified**:
- `frontend/src/components/TopicExplorerModern.tsx` - Replaced Command with native HTML

**Current Status**:
- ✅ Mouse click selection works
- ⚠️ Keyboard navigation temporarily disabled (TODO: restore later)

#### LLM Model Selection Fix
**Problem**: User selected "Gemini 3 Flash Preview" but system used "gemini-2.5-pro" instead

**Root Cause**: The `model_mapping` dictionaries were mapping to full LiteLLM paths (`gemini/gemini-3-flash-preview`) but LiteLLM Router expects `model_name` from config (without prefix: `gemini-3-flash-preview`)

**Solution**: Updated all model_mapping values to use `model_name` format (without `gemini/` prefix)

**Before (Wrong)**:
```python
model_mapping = {
    "gemini/gemini-3-flash-preview": "gemini/gemini-3-flash-preview",  # WRONG!
}
```

**After (Correct)**:
```python
model_mapping = {
    "gemini/gemini-3-flash-preview": "gemini-3-flash-preview",  # Correct - matches model_name in litellm_config.yaml
    "gemini-3-flash-preview": "gemini-3-flash-preview",
}
```

**Files Modified**:
- `backend/app/api/papers_mongodb.py` - Fixed 2 locations with model_mapping dictionaries

**Verification**: User confirmed working - "success gemini/gemini-3-flash-preview"

---

### AI Summarization Fixes & Enhancements - COMPLETE

#### Problems Fixed

1. **Date Range Bug in Summaries**: User selected "last week" but received summary mentioning "Oct 24 – Oct 31, 2024" - completely wrong dates
2. **Concept Filter Not Working**: Filtering by concept (e.g., "Agentic AI") returned generic content instead of tagged content
3. **"All Time" Period Not Sent**: Frontend skipped sending period parameter for "All Time", causing backend to default to 7 days
4. **Missing Time Period Options**: Only had today, 3 days, week, 2 weeks, 30 days

#### Root Causes & Solutions

**1. LLM Prompt Missing Explicit Dates** (`backend/app/api/analytics_trends_mongodb.py`):
```python
# BEFORE: LLM didn't know actual dates, hallucinated them
prompt = f"...Analyze content from the past {days} day(s)..."

# AFTER: Explicit date range in prompt
date_range_str = f"from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
prompt = f"...Analyze content {date_range_str} (the past {days} day(s))..."
```

**2. Concept Filter Applied AFTER Limit** (`backend/app/api/analytics_trends_mongodb.py`):
```python
# BEFORE: Got first 200 tweets, THEN filtered by concept (missed tagged tweets beyond position 200)
tweets = list(db.tweets.find(tweet_filter).limit(max_tweets))
# Then loop through tweets checking for concept tags...

# AFTER: Get tagged content IDs FIRST, add to query filter, THEN apply limit
if tags:
    tweet_ids = [inst['content_id'] for inst in db.tag_instances.find({
        'content_type': 'tweet',
        'concept_id': {'$in': concept_ids}
    })]
    tweet_filter['_id'] = {'$in': tweet_ids}

tweets = list(db.tweets.find(tweet_filter).sort('created_at', -1).limit(max_tweets))
```

**3. Frontend Skipping "All Time" Period** (`frontend/src/components/SummarizationModern.tsx`):
```typescript
// BEFORE: Period not sent for "all", backend defaulted to 7 days
if (period !== 'all') params.append('period', period)

// AFTER: Always send period
params.append('period', period)  // Always send period, including 'all'
```

**4. Extended Time Period Options**:
- Frontend: Added 60, 90, 120, 200, 365 days options
- Backend: Added handlers for all new periods, changed "all" from 365 to 3650 days (~10 years)

#### Configurable Data Limits Feature - NEW

Users can now configure max tweets/articles/papers in the UI with persistent settings.

**Backend** (`analytics_trends_mongodb.py`):
```python
@router.post("/summarize")
def generate_summary(
    # ... existing params ...
    max_tweets: int = Query(100, ge=10, le=500),
    max_articles: int = Query(50, ge=5, le=200),
    max_papers: int = Query(50, ge=5, le=200)
):
```

**Frontend** (`SummarizationModern.tsx`):
- Collapsible "Data Limits" settings panel with gear icon
- Number inputs for tweets (10-500), articles (5-200), papers (5-200)
- Settings persist to localStorage across sessions
- Truncation warning displays when data exceeds limits

#### Time Period Options (Complete List)

| Value | Description | Days |
|-------|-------------|------|
| `today` | Today | 1 |
| `3days` | Last 3 Days | 3 |
| `week` | Last Week | 7 |
| `14days` | Last 2 Weeks | 14 |
| `30days` | Last 30 Days | 30 |
| `60days` | Last 60 Days | 60 |
| `90days` | Last 90 Days | 90 |
| `120days` | Last 120 Days | 120 |
| `200days` | Last 200 Days | 200 |
| `365days` | Last Year | 365 |
| `all` | All Time | 3650 |

#### Files Modified
- `backend/app/api/analytics_trends_mongodb.py` - Concept filter fix, period handlers, configurable limits
- `frontend/src/components/SummarizationModern.tsx` - Period options, always send period, settings UI
- `backend/app/api/media.py` - Fixed missing function definition (IndentationError)
- `backend/app/api/collection.py` - Fixed missing function definition (IndentationError)

---

## Recent Enhancements (December 25, 2025)

### LLM Model Configuration & API Fixes - COMPLETE

#### Problems Fixed

1. **Gemini 3 Models 404 Errors**: Free Analysis with Gemini 3 Flash/Pro returned 404
2. **Gemini Response Format**: Gemini 3 returns `[{type: 'text', text: '...'}]` array instead of string
3. **Claude API Key Not Loading**: LiteLLM's `os.environ/ANTHROPIC_API_KEY` syntax not working
4. **Frontend Crash**: ReactMarkdown received object instead of string

#### Solutions Implemented

**1. Gemini Model Name Fix** (`backend/app/services/llm_service.py:137-138`):
```python
# Strip 'gemini/' prefix - ChatGoogleGenerativeAI expects just the model name
google_model = model.replace('gemini/', '') if model.startswith('gemini/') else model
```

**2. Gemini Array Response Handling** (`backend/app/services/llm_service.py:170-187`):
```python
# Gemini 3 models may return list of content blocks
if isinstance(content, list):
    text_parts = []
    for part in content:
        if isinstance(part, str):
            text_parts.append(part)
        elif hasattr(part, 'text'):
            text_parts.append(part.text)
        elif isinstance(part, dict) and 'text' in part:
            text_parts.append(part['text'])
    content = '\n'.join(text_parts)
```

**3. Frontend Content Extraction** (`frontend/src/components/PaperAnalysisPanel.tsx:59-78`):
```typescript
// Helper to handle both string and Gemini's array format
const extractTextContent = (content: unknown): string => {
  if (typeof content === 'string') return content
  if (Array.isArray(content)) {
    return content.map(part => {
      if (typeof part === 'string') return part
      if (part && typeof part === 'object' && 'text' in part) return part.text
      return ''
    }).join('\n')
  }
  return String(content || '')
}
```

**4. LiteLLM API Key Loading** (`backend/litellm_config.yaml`):
- Removed all explicit `api_key: os.environ/...` lines
- LiteLLM auto-detects API keys from environment variables
- Keys loaded from `~/.env`: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `XAI_API_KEY`

#### Tested & Working Models

| Provider | Models | Status |
|----------|--------|--------|
| Google | `gemini-3-flash-preview`, `gemini-3-pro-preview`, `gemini-2.5-pro`, `gemini-2.5-flash` | ✅ |
| Anthropic | `claude-sonnet-4-20250514`, `claude-opus-4-1-20250805`, `claude-3-haiku-20240307` | ✅ |
| OpenAI | `gpt-5.2`, `gpt-5.1`, `gpt-5-nano`, `gpt-4o` | ✅ |
| xAI | `grok-4-1-fast-reasoning`, `grok-4-1-fast`, `grok-2-latest` | ✅ |

#### Files Modified
- `backend/app/services/llm_service.py` - Gemini prefix strip + array response handling
- `backend/litellm_config.yaml` - Removed explicit api_key lines
- `frontend/src/components/PaperAnalysisPanel.tsx` - Added extractTextContent helper
- `frontend/src/config/models.ts` - Updated model IDs and labels
- `backend/llm.json` - Updated model configurations

---

## Recent Enhancements (December 24, 2025)

### Cross-Platform Compatibility Fixes (macOS ↔ Linux) - COMPLETE

#### Problem
After syncing project from macOS to Linux (Arch Linux) via Syncthing, `start_stt.sh` failed with:
- `venv/bin/python: No such file or directory` - venv symlinks pointed to macOS paths
- `ModuleNotFoundError: No module named 'psutil'` - Marker service missing dependencies
- Frontend `node_modules` had macOS-native bindings that failed on Linux
- API keys from `~/.env` not being loaded by backend services

#### Solutions Implemented

**1. Automatic ~/.env Loading in start_stt.sh:**
```bash
if [ -f "$HOME/.env" ]; then
    set -a  # automatically export all variables
    source "$HOME/.env"
    set +a
fi
```

**2. venv Validation Function:**
- Added `check_venv_valid()` to detect broken venvs (symlinks pointing to wrong platform)
- Automatically recreates venv if python binary doesn't exist or isn't executable
- Works for backend venv, marker_env, and mineru_env

**3. Platform Detection:**
```bash
detect_platform() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        PLATFORM="linux"
    fi
}
```

**4. Mise Integration:**
- Added mise activation at script start for Python version management
- Created `mise.toml` to pin Python 3.12 (3.14 too new for many packages)

**5. node_modules Handling:**
- Frontend `node_modules` with native bindings (rollup, etc.) must be reinstalled per platform
- Run `npm install` after syncing to Linux/macOS

#### Files Modified
- `start_stt.sh` - Added ~/.env loading, venv validation, platform detection, mise activation
- `mise.toml` - Created to pin Python 3.12

#### Cross-Platform Workflow
```bash
# On macOS (end of session):
cd backend && ./sync-out.sh

# On Linux (start of session):
cd backend && ./sync-in.sh
cd .. && ./start_stt.sh  # Auto-detects broken venvs, recreates them
cd frontend && npm install  # Reinstall native modules
```

---

## Recent Enhancements (November 23, 2025)

### Marker PDF Processing - Real-time Progress Tracking - COMPLETE

#### Problem
The Marker PDF processing progress indicator showed static "CPU: 0.0%, RAM: 0 MB, Output: Processing..." without updates, even though processing was working in the background.

#### Root Cause
The `_parse_marker_progress()` function in `marker_server.py` used synthetic regex patterns that didn't match the actual TQDM progress bar format output by Marker CLI.

**Before (Broken)**:
```python
# Looking for patterns that don't exist in real Marker output
if "Processing page" in line:  # ← This string never appears!
    match = re.search(r"Processing page (\d+)[/\s]+(\d+)", line, re.IGNORECASE)
```

#### Solution Implemented

**Updated TQDM Parser** (`backend/marker_service/marker_server.py:138-206`):
```python
def _parse_marker_progress(line: str) -> Optional[dict]:
    """Parse marker output for progress information (supports TQDM format)"""

    # TQDM progress bar pattern: "50%|█████     | 25/50 [00:15<00:15, 1.66it/s]"
    tqdm_match = re.search(r'(\d+)%\s*\|[█\s]*\|\s*(\d+)/(\d+)', line)
    if tqdm_match:
        percent, current, total = tqdm_match.groups()
        # Extract description and determine stage
        # Returns: {stage, message, progress, current, total}

    # Fallback patterns for standalone percentages and keywords
    # ...
```

**Real Marker Output Examples**:
```
Recognizing Layout:  38% 5/13 [00:20<00:26, 3.35s/it]
Recognizing Text:    9% 19/220 [02:32<15:26, 4.61s/it]
Converting to Markdown: 100% 13/13 [00:30<00:00, 1.29s/it]
```

#### Complete Progress Pipeline

**End-to-End Data Flow**:
```
1. Marker CLI (TQDM output)
   ↓
2. PTY captures output line-by-line (marker_server.py)
   ↓
3. _parse_marker_progress() extracts: percentage, current/total, stage
   ↓
4. Progress callback sent to Backend API (every 2 seconds, throttled)
   POST /api/papers/{id}/progress-callback
   ↓
5. Backend stores in MongoDB (papers_mongodb.py:1958-1996)
   papers.processing_progress = {stage, message, progress, health}
   papers.marker_process_health = {cpu_percent, memory_mb, pid}
   ↓
6. Frontend polls two endpoints (every 10 seconds)
   GET /api/papers/{id}/processing-status  (message, percentage)
   GET /api/papers/{id}/process-health     (CPU, RAM)
   ↓
7. UI updates in real-time
   ProcessingStatusIndicator.tsx displays live metrics
```

#### Frontend Polling Configuration

**Updated Intervals** (`frontend/src/components/ProcessingStatusIndicator.tsx`):
- **Progress Status**: 10 seconds (down from 60s) - Line 100
- **Process Health**: 10 seconds (down from 30s) - Line 133

```typescript
// Near real-time updates for better user experience
const interval = setInterval(checkStatus, 10000);
const healthInterval = setInterval(checkHealth, 10000);
```

#### Asynchronous Processing Architecture

**Key Features**:
- ✅ **Background Processing**: Marker runs as separate service, continues even if browser closes
- ✅ **Persistent State**: Progress stored in MongoDB, survives browser/tab closures
- ✅ **Resume on Return**: When user comes back to UI, sees current status from database
- ✅ **FastAPI BackgroundTasks**: Non-blocking processing with immediate API response

**User Workflow**:
1. User uploads PDF and starts processing
2. Backend starts Marker service in background
3. User can close browser/navigate away
4. Processing continues on server
5. User returns later → sees current progress or completed status

#### Files Modified

**Backend**:
- `backend/marker_service/marker_server.py` - TQDM parser fix (lines 138-206)
- `backend/app/api/papers_mongodb.py` - Progress callback handler (lines 1958-1996)

**Frontend**:
- `frontend/src/components/ProcessingStatusIndicator.tsx` - 10-second polling intervals

#### Testing & Verification

**Monitor Live Progress**:
```bash
# Watch Marker logs for TQDM output
tail -f backend/marker_service/../../logs/marker.log

# Check MongoDB for stored progress
mongosh smarttrendtracer --eval "db.papers.findOne({_id: ObjectId('...')}, {processing_progress: 1, marker_process_health: 1})"

# Test API endpoints
curl http://localhost:8000/api/papers/{id}/processing-status | jq
curl http://localhost:8000/api/papers/{id}/process-health | jq
```

#### UI Display

**What Users See Now**:
- ✅ Live progress message: `"Recognizing Text: 45% 99/220 [05:30<06:42, 3.5s/it]"`
- ✅ CPU usage: `"98.8%"` (updated every 10s)
- ✅ RAM usage: `"2279 MB"` (updated every 10s)
- ✅ Progress bar: Visual percentage indicator
- ✅ Elapsed time: Minutes since processing started

**Status**: ✅ COMPLETE - Full end-to-end real-time progress tracking working

## Recent Enhancements (September 16, 2025)

### Book Management System - COMPLETE

#### Comprehensive Book Library Extension
SmartTrendTracer now includes a complete book management system similar to the research paper management but optimized for longer documents:

**Features Implemented**:
- **MongoDB Collection**: Complete `books` collection with book-specific schema
- **File Support**: PDF and EPUB books with dedicated processors
- **Extended Processing**: 6-hour timeouts for Marker, 5-hour for MinerU to handle large books
- **EPUB Native Processing**: Built-in EPUB parsing using langchain-community
- **Book-Specific Metadata**: Publishers, ISBN, genres, reading difficulty, table of contents
- **Faceted Browsing**: Filter by genre, publisher, author, difficulty level, file type
- **Smart Pagination**: Optimized viewer for book-length content with overlap
- **Concept Integration**: Full tagging system compatibility with existing hierarchy

**Technical Architecture**:
```
backend/app/api/books_mongodb.py          # Complete books CRUD API
backend/app/services/book_processor_service.py  # Extended PDF/EPUB processing
frontend/src/components/FacetedBooksDashboard.tsx  # Main books interface
frontend/src/components/BookUploadModal.tsx        # Book upload with metadata
frontend/src/components/BookViewerOptimized.tsx    # Book content viewer
```

**API Endpoints**:
- `GET /api/books/` - Browse books with filtering and pagination
- `POST /api/books/upload` - Upload PDF/EPUB with metadata
- `GET /api/books/{book_id}` - Get book details
- `POST /api/books/{book_id}/process` - Background book processing
- `POST /api/books/{book_id}/process-direct` - Direct processing (1-6 hours)
- `GET /api/books/{book_id}/content` - Get extracted markdown content
- `POST /api/books/{book_id}/concepts` - Add concept tags to books

**Book-Specific Features**:
- **Table of Contents Extraction**: Automatic TOC generation from headings
- **Glossary Term Detection**: Extract definitions and terminology
- **Reading Difficulty Assessment**: Automatic difficulty estimation (beginner/intermediate/advanced/expert)
- **Chapter Detection**: Smart chapter boundary identification
- **Extended Timeouts**: Handles books up to 500MB and 2000+ pages
- **Multiple Formats**: PDF processing via Marker/MinerU, native EPUB parsing

**Navigation Integration**: Added to ModernNavigation with dedicated "Book Library" section including "Browse Books" and "Book Analytics" views.

## Recent Enhancements (January 24, 2025)

### Complete MongoDB Migration - ALL DATA NOW IN MONGODB

#### Full System Migration
- **Status**: ✅ COMPLETE - Entire system migrated from SQLite to MongoDB
- **Migration Date**: January 24, 2025
- **Data Migrated**:
  - 1,169 tweets with full metadata and media
  - 34 papers with authors, content, and references
  - 40 articles with summaries and metrics
  - 13 Substack authors
  - 1,746 tag concepts with hierarchy
  - 2,854 tag instances
  - **Books collection added** for PDF/EPUB book management

#### MongoDB Collections
```
smarttrendtracer database:
├── tweets           # 1,169 tweet documents
├── papers           # 34 paper documents
├── articles         # 40 article documents
├── books            # PDF/EPUB book collection (new)
├── substack_authors # Author information
├── tag_concepts_v2  # Tag concepts/hierarchy
├── tag_aliases_v2   # Tag aliases/synonyms
├── tag_instances    # Tag usage tracking
└── collection_state # Tweet collector state
```

#### System Components Updated
- **Main API** (`app/main.py`): Fully MongoDB-based, no SQLite dependencies
- **Tweet Collector** (`tweet_collector_service.py`): Uses MongoDB for all storage
- **API Modules**:
  - `tweets_mongodb.py` - Complete MongoDB tweets API
  - `papers_mongodb.py` - MongoDB papers API with embedded data
  - `articles_mongodb.py` - MongoDB articles API
  - `statistics_mongodb.py` - MongoDB aggregation pipelines
- **Dependencies** (`requirements.txt`): SQLAlchemy removed, PyMongo added

#### Benefits of Full MongoDB Migration
1. **Unified Data Store**: All data in one database system
2. **Better Performance**: Native aggregation pipelines for complex queries
3. **Flexible Schema**: Easy to add fields without migrations
4. **Scalability**: Handles large datasets better than SQLite
5. **Native JSON**: Natural fit for JavaScript frontend
6. **No ORM Overhead**: Direct document operations

#### Backup Files Created
- `app/main_sqlite_backup.py` - Original SQLite-based main.py
- `tweet_collector_service_sqlite_backup.py` - Original collector
- `data/tweets.db` - Original SQLite database (preserved)

## Recent Enhancements (September 5, 2025)

### Reddit Integration - COMPLETE

#### Full Reddit Support Added to SmartTrendTracer
- **New Data Source**: Reddit posts from AI/ML subreddits now monitored alongside Twitter, articles, and papers
- **Subreddits Monitored**: r/LLM, r/LLMDevs, r/LocalLLM, r/MachineLearning, r/artificial, r/OpenAI, r/ChatGPT, r/singularity
- **Features**:
  - Complete CRUD API with faceted browsing and filtering
  - MongoDB storage with full schema compatibility
  - Tagging system integration using existing concept hierarchy
  - Real-time collection with configurable intervals
  - Full UI dashboard with filtering by subreddit, author, score, time range

#### Technical Implementation
- **Backend**:
  - `reddit_collector.py` - PRAW-based collector service
  - `reddit_mongodb.py` - Complete API endpoints
  - MongoDB models for posts, comments, and subreddit configuration
  - Integration with existing concept tagging system
- **Frontend**:
  - `FacetedRedditDashboardModern.tsx` - Full-featured dashboard
  - Navigation integration with dedicated Reddit section
  - Dashboard cards and feature overview
- **Configuration**: `reddit_config.json` - Subreddit monitoring configuration

#### Collection Features
- **Smart Collection**: Respects rate limits with 2-second delays between requests
- **Comment Integration**: Optionally collects top comments per post
- **URL Extraction**: Automatically extracts and indexes external links
- **Score Filtering**: Configurable minimum score thresholds
- **Time-based Collection**: Incremental collection with configurable time windows

#### UI Features Implemented
- **Faceted Browsing**: Filter by subreddit, author, score, time range, post type
- **Search**: Full-text search across titles and content
- **Concept Integration**: Use existing tag system for Reddit posts
- **Statistics**: Real-time statistics and collection monitoring
- **Manual Collection**: Trigger collection directly from UI

#### API Endpoints Added
- `GET /api/reddit/` - Browse Reddit posts with filtering
- `GET /api/reddit/faceted-search` - Paginated faceted search
- `GET /api/reddit/facets` - Get filter options and statistics
- `GET /api/reddit/{post_id}` - Get specific post details
- `POST /api/reddit/{post_id}/tags` - Add tags to posts
- `DELETE /api/reddit/{post_id}/tags/{concept_id}` - Remove tags
- `GET /api/reddit/stats/collection` - Collection statistics
- `POST /api/reddit/collect` - Manual collection trigger

#### Setup Requirements
- **Reddit API**: Requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables
- **Dependencies**: Added `praw==7.7.1` to requirements.txt
- **MongoDB**: Uses existing smarttrendtracer database with reddit_posts collection

## Recent Enhancements (September 1, 2025)

### Paper Metadata & Import System Fixes - COMPLETE

#### ACL Anthology Author Extraction Fixed
- **Problem**: Authors from ACL Anthology papers displayed correctly but didn't appear in "Edit Paper Metadata" dialog
- **Root Cause**: ACL papers used `authors_list` field but edit dialog expected `authors_detailed` field
- **Solution**: 
  - Updated all 24 ACL papers to include `authors_detailed` field extracted from `authors_list`
  - Enhanced edit dialog logic to handle multiple author field formats (`authors_detailed`, `authors_list`, `authors` string)
- **Result**: Edit dialog now shows all authors correctly regardless of import source

#### Date Format Warning Resolved
- **Problem**: HTML date inputs received "yyyy-MM-ddT00:00:00" format but expected "yyyy-MM-dd"
- **Solution**: Added date format conversion in metadata edit dialog
- **Code**: `date.toISOString().split('T')[0]` to extract proper format
- **Result**: No more browser console warnings for date format mismatches

#### React Hooks Violations Completely Fixed
- **Problem**: "Rendered fewer hooks than expected" errors in development
- **Solutions Applied**:
  - Moved early return statements after all hook declarations in `PaperViewerOptimized`
  - Refactored conditional `useMemo` in `PDFViewerModern` to prevent hooks order violations
  - Fixed function declaration order before hooks that use them
- **Result**: Frontend builds successfully without React hooks warnings

#### Enhanced ACM Import Error Handling  
- **Problem**: ACM Digital Library returns HTML instead of PDF for access-restricted papers
- **Solution**: Enhanced ACM service to detect 403/401 errors and prevent invalid PDF creation
- **Features**: Proper access restriction messages instead of "Invalid PDF structure" errors
- **Result**: ACM imports now work reliably and create valid PDF files when accessible

#### Author Field Consistency Across All Import Sources
- **Database Schema**: All papers now have consistent author field structure:
  - `authors`: Comma-separated string for compatibility
  - `authors_detailed`: Array of author objects for structured data
  - `authors_list`: Preserved for ACL papers with position information
- **Import Sources Supported**:
  - ✅ ACL Anthology: 24 papers with authors properly extracted
  - ✅ ACM Digital Library: Enhanced error handling and valid PDF downloads
  - ✅ GROBID Processing: Authors extracted from TEI XML and saved correctly
  - ✅ Direct Upload: Manual author entry through edit dialog
- **Result**: "Edit Paper Metadata" dialog works consistently across all import methods

## Recent Enhancements (August 25, 2025)

### PDF Processing & Viewer Fixes - COMPLETE

#### Paper Image Serving Fixed
- **Problem**: Images from Marker-processed papers weren't being served (404 errors)
- **Solution**: Added missing `paper_images` module import and router to `main.py`
- **Result**: Images now correctly served at `/api/papers/{id}/images/...` endpoints

#### PDF Viewer Flickering Resolved
- **Problem**: PDF viewer would flicker/reload when Marker processing completed
- **Root Cause**: `ProcessingStatusIndicator` was reloading entire paper data on completion
- **Solutions Applied**:
  - Modified `onComplete` callback to only update markdown content
  - Reduced polling frequency from 30s to 60s
  - Wrapped `PDFViewerModern` component with `React.memo()`
  - Added proper display name for debugging

#### GROBID Processing Fixed
- **External Server**: Using https://kermitt2-grobid.hf.space (HuggingFace Spaces)
- **Issues Fixed**:
  - Removed incorrect `await` on non-async `process_pdf` function
  - Fixed citation processing endpoint (was using wrong API)
  - Added proper error handling for server connectivity
  - Added XML validation before parsing responses
- **Benefits**: No local GROBID installation needed on Mac

## Recent Enhancements (August 30, 2025)

### Paper Section Management - COMPLETE

#### Section Title Editing
- **Problem**: Extracted sections had numbers in titles (e.g., "11 Conclusion")
- **Solution**: Added inline editing capability with automatic number removal
- **Features**:
  - Hover-to-show edit buttons for section titles
  - Automatic removal of leading numbers when saving
  - PUT endpoint `/api/papers/{paper_id}/sections/{section_id}` for updates

#### DBLP Integration Fixed
- **Problem**: DBLP search was giving 404 errors due to SQLite dependencies
- **Solution**: Created MongoDB-compatible `dblp_mongodb.py`
- **Endpoints**:
  - `/api/dblp/search` - Search DBLP bibliography
  - `/api/dblp/bibtex` - Get BibTeX citations
  - `/api/dblp/metadata` - Get full paper metadata

### Author Affiliation Extraction - COMPLETE

#### LLM-Powered Affiliation Extraction
- **Feature**: Extract author affiliations from paper headers using AI
- **Configuration**: Uses `llm.json` and `prompts_config.json` (no hardcoding)
- **Model**: Claude Sonnet 4 with low temperature (0.1) for accuracy

#### API Endpoints
- **POST** `/api/papers/{paper_id}/extract-affiliations`
  - Extracts affiliations from paper header (title to abstract)
  - Returns suggestions with confidence levels (high/medium/low)
  - Handles both string and array author formats
- **PUT** `/api/papers/{paper_id}/apply-affiliations`
  - Applies selected affiliations to paper authors
  - Updates MongoDB with new author data

#### UI Components
- **Affiliations Button**: Appears in Paper Details when authors exist
- **Review Dialog**: 
  - Shows AI-extracted affiliation suggestions
  - Displays current vs. suggested affiliations
  - Color-coded confidence badges
  - Checkbox selection for each suggestion
  - Apply Selected / Cancel actions

### Missing Data Facets Fix - COMPLETE

#### Problem
- "Missing Data → Affiliation" count was incorrect
- Counted from current page (20 papers) instead of entire database
- Count changed when filters were applied

#### Solution
- **Backend**: Added `missing_data` counts to `/api/papers/facets` endpoint
  - Calculates counts from entire database (or filtered set)
  - Uses MongoDB aggregation for complex affiliation checks
  - Returns counts for: no_processor, no_year, no_conference, no_affiliation, no_annotations
- **Frontend**: Updated to use backend-provided counts
  - Changed from local `papers.filter()` to `facets?.missing_data?.no_affiliation`
  - Now shows accurate count of papers WITHOUT affiliations

#### Result
- Missing Data counts now always show papers MISSING that data (proper negation)
- Counts remain consistent whether selected or not
- Updates correctly when other filters are applied

## Recent Enhancements (August 22, 2025)

### MongoDB Migration for Tag Ontology - COMPLETE

#### Poly-hierarchy Support
- **Database**: Migrated tag system from SQLite to MongoDB for true poly-hierarchy support
- **Collections**: tag_concepts_v2, tag_aliases_v2, tag_instances
- **Features**:
  - Concepts can have multiple parent concepts (e.g., "Knowledge Graphs" under both "AI/ML Fundamentals" AND "Data and Datasets")
  - 43 concepts now have multiple parents in the hierarchy
  - Entity type integration from top_level.json schema

#### Entity Type Integration
- **Entity Types**: Integrated top_level.json entity type schema into concept hierarchy
- **Categories**: Named Entities, Research Entities, Content Types
- **Fixes Applied**:
  - India and Silicon Valley moved under Location entity type
  - People (Sam Altman, Dario Amodei) set as entity_type: person
  - Organizations (OpenAI, Anthropic) set as entity_type: organisation
  - Knowledge Graphs and Semantic Web given multiple parents

#### Backend Infrastructure
- **MongoDB Setup**: `setup_mongodb.py` - Creates collections with proper indexes
- **Data Migration**: `migrate_tags_to_mongodb.py` - Migrated 116 concepts, 308 aliases, 2,089 tag instances
- **Entity Integration**: `integrate_entity_types.py` - Integrates entity types and fixes misplaced concepts
- **API**: `tag_ontology_v2_mongodb.py` - MongoDB-based API with singleton connection pattern

#### UI Enhancements
- **Poly-hierarchy Display**: Shows all parent concepts with "(poly-hierarchy)" label when multiple
- **Usage Statistics**: Now includes papers alongside tweets and articles
- **Entity Type Icons**: Visual indicators for different entity types (👤 person, 🏢 organisation, 📍 location)
- **Color Coding**: Entity-specific colors for better visual hierarchy

#### MongoDB Commands
```bash
# Install MongoDB (macOS)
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
brew services start mongodb-community

# Access MongoDB shell
mongosh

# Database operations
use smarttrendtracer
db.tag_concepts_v2.find().count()  # 119 concepts
db.tag_aliases_v2.find().count()   # 308 aliases
db.tag_instances.find().count()    # 2089 instances

# Check poly-hierarchy concepts
db.tag_concepts_v2.find({parents: {$size: {$gt: 1}}}).count()  # 43 concepts

# View entity types
db.tag_concepts_v2.distinct("entity_type")
```

#### Current System Architecture (Full MongoDB - COMPLETE January 24, 2025)
- **MongoDB**: Stores ALL data (tweets, papers, articles, tags, concepts, everything)
- **SQLite**: No longer used (backup preserved at data/tweets.db)
- **Migration Status**: ✅ COMPLETE - Entire system migrated to MongoDB

#### Key Files Modified
- `backend/app/main.py` - Uses MongoDB API for ontology
- `backend/app/api/tag_ontology_v2_mongodb.py` - MongoDB-based ontology API
- `backend/app/api/orphan_tags.py` - Updated to query MongoDB
- `frontend/src/components/TagOntologyModern.tsx` - Shows poly-hierarchy and papers in usage stats

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

### Default Mode: Basic Account ($100/month plan)
The collector now defaults to Basic Account Mode with optimized settings for the $100/month Twitter API plan.

### Daily Collection Commands

#### 1. **Main Collection (Recommended)**
```bash
cd backend
./start_basic_collector.sh
# Press Enter to use default Basic Account Mode
```
- **Basic Account Mode is now DEFAULT**
- Collects 1 page (100 tweets max) per account
- Uses tiered priority system
- Monitors usage to stay within 10,000 tweets/month
- 15-minute collection intervals

#### 2. **Direct Collection**
```bash
cd backend
python tweet_collector_service.py
# Runs in Basic Account Mode by default
```

#### 3. **Pro/Enterprise Mode** (if you have higher tier)
```bash
cd backend
export BASIC_ACCOUNT_MODE=false
python tweet_collector_service.py
```

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
# Check last collection time (MongoDB)
python -c "from pymongo import MongoClient; db = MongoClient().smarttrendtracer; print(list(db.collection_state.find()))"

# View database statistics (MongoDB)
mongosh smarttrendtracer --eval "db.tweets.count()"
mongosh smarttrendtracer --eval "db.tweets.aggregate([{'\$group': {_id: '\$author_username', count: {'\$sum': 1}}}])"

# Check most recent tweet
mongosh smarttrendtracer --eval "db.tweets.find().sort({created_at: -1}).limit(1)"
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

## Book Management Commands

### Upload and Process Books
```bash
cd frontend
npm run dev
# Navigate to: http://localhost:3000 → "Book Library" → "Browse Books"
# Use "Upload Book" button for PDF/EPUB files
```

### Manual Book Processing
```bash
cd backend
# Start the API server
python app/main.py

# Use API endpoints directly:
# POST /api/books/{book_id}/process - Background processing (recommended)
# POST /api/books/{book_id}/process-direct - Direct processing (1-6 hours)
```

### Book Storage and Organization
```bash
# Check book repository
ls -la data/book_repository/
# Each book gets its own directory: data/book_repository/{book_id}/

# View book collection status
mongosh smarttrendtracer --eval "db.books.find().count()"
mongosh smarttrendtracer --eval "db.books.aggregate([{'\$group': {_id: '\$processing_status', count: {'\$sum': 1}}}])"

# Check processing status
mongosh smarttrendtracer --eval "db.books.find({processing_status: 'completed'}).count()"
mongosh smarttrendtracer --eval "db.books.find({processing_status: 'failed'}).count()"
```

### Book Processing Options
```bash
# Processor selection:
# - "auto": Automatically choose best processor (default)
# - "marker": Use Marker service (6-hour timeout, best for large books)
# - "mineru": Use MinerU service (5-hour timeout)
# - "epub_native": EPUB-specific processing (EPUB files only)

# Example: Process with specific processor
curl -X POST "http://localhost:8000/api/books/{book_id}/process?preferred_processor=marker"
```

### Book Features Testing
```bash
# Test EPUB processing (requires langchain-community)
pip install langchain-community

# Test table of contents extraction
# Upload a book with clear chapter headings

# Test glossary extraction
# Upload technical books with definition sections

# Test reading difficulty assessment
# Compare results across different book types (textbook vs novel)
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

### RAG Search with Trend Analysis (NEW - November 2025)

#### Overview
The RAG Search system now includes LLM-powered trend analysis that automatically detects when users are asking about trends and provides comprehensive analysis of hot topics across different content sources.

#### Trend Query Detection
The system automatically detects trend-related questions using keyword matching:
- **Trend keywords**: "trend", "trending", "hot topic", "popular", "what's happening", "latest", "emerging", "buzz", "key topics", "most discussed"
- **Auto-routing**: Questions with these keywords automatically use trend analysis instead of standard RAG search
- **Enhanced retrieval**: Retrieves 50 documents instead of 10 for better trend detection

#### API Endpoint
```http
POST /api/rag/ask
Content-Type: application/json

{
  "question": "What are the key trends on Twitter?",
  "content_types": ["tweet"],  // Optional: "tweet", "article", "paper"
  "k": 50  // Optional: number of documents to analyze
}
```

**Response for Trend Queries**:
```json
{
  "answer": "# Top 5 Trending Topics\n\n1. **Claude 4 Release**...",
  "sources": [
    {
      "type": "tweet",
      "id": "123",
      "author": "OpenAI",
      "score": 0.95,
      "concepts": ["gpt-4", "language-models"]
    }
  ],
  "is_trend_analysis": true,
  "documents_analyzed": 50,
  "source_type": "tweets"
}
```

**Response for Normal Queries**:
```json
{
  "answer": "GPT-4 is a large language model...",
  "sources": [...],
  "concepts_used": ["gpt-4", "transformer-architecture"]
}
```

#### Frontend Quick Actions
The UI includes quick action buttons for instant trend analysis:
- **🔥 Trending on Twitter** - Analyzes 50 recent tweets for hot topics
- **📄 Trending in Papers** - Identifies research trends from papers
- **📰 Hot Topics in Articles** - Finds trending topics in Substack articles

#### How It Works

1. **Question Analysis**:
   - User asks: "What are the key trends on Twitter?"
   - System detects trend keywords and routes to `analyze_trends()`

2. **Document Retrieval**:
   - Retrieves 50 documents (instead of 10 for normal queries)
   - Filters by content type if specified (`tweet`, `article`, `paper`)
   - Uses broad semantic search to capture recent content

3. **LLM Analysis**:
   - Uses Claude Opus 4.1 model (200K context, 32K output)
   - Analyzes all 50 documents to identify patterns
   - Generates structured trend report with:
     - Top 5 trending topics
     - Key insights and developments
     - Notable examples from documents
     - Emerging patterns

4. **Enhanced Display**:
   - Blue-highlighted card for trend analysis results
   - Badge showing number of documents analyzed
   - TrendingUp icon to distinguish from regular answers
   - Formatted markdown with headers and bullet points

#### Example Trend Queries
```
"What are the key trends on Twitter?"
"Show me trending topics in research papers"
"What's hot in articles right now?"
"What are people talking about in AI?"
"What are the most discussed topics?"
"What's the biggest emerging topic?"
```

#### Configuration

**Prompt Template** (`prompts_config.json`):
```json
{
  "rag_trend_analysis": {
    "system": "You are a trend analyst expert...",
    "user_template": "Analyze these {count} {source_type} documents...",
    "output_format": "text"
  }
}
```

**LLM Model** (`llm.json`):
```json
{
  "trend_analysis": {
    "model": "claude-opus-4-1-20250805",
    "temperature": 0.3,
    "max_tokens": 10000
  }
}
```

#### Testing
Run comprehensive trend analysis tests:
```bash
cd backend
export KMP_DUPLICATE_LIB_OK=TRUE  # For FAISS on macOS
python test_rag_trends.py
```

Tests include:
- Trend query detection accuracy
- Trend analysis for tweets, papers, and articles
- ask() method routing logic
- Normal query handling (ensuring they're not routed to trends)
- Response format validation

#### Source Filtering Verification
To verify that content type filtering works correctly:
```bash
cd backend
export KMP_DUPLICATE_LIB_OK=TRUE
python test_rag_source_filtering.py
```

This confirms that:
- Tweets-only filter returns only tweets
- Articles-only filter returns only articles
- Papers-only filter returns only papers
- Mixed filters work correctly
- Empty filter returns all content types

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
pymongo        # MongoDB driver (primary database)
motor          # Async MongoDB driver
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

### MongoDB Database Status
```bash
# Check MongoDB collections
mongosh smarttrendtracer --eval "show collections"

# Twitter stats
mongosh smarttrendtracer --eval "db.tweets.aggregate([{\$group: {_id: '\$author_username', count: {\$sum: 1}}}])"

# Papers stats
mongosh smarttrendtracer --eval "db.papers.count()"

# Articles stats
mongosh smarttrendtracer --eval "db.articles.count()"

# Tag concepts
mongosh smarttrendtracer --eval "db.tag_concepts_v2.count()"
```

### MongoDB Backup
```bash
# Backup entire database
mongodump --db smarttrendtracer --out backup_$(date +%Y%m%d)

# Restore from backup
mongorestore --db smarttrendtracer backup_20250124/smarttrendtracer
```

## Known Issues & Solutions

> **Full defect list:** See `DEFECTS.md` for comprehensive issue tracking with priorities and status.

### Quick Reference

| ID | Issue | Status | Workaround |
|----|-------|--------|------------|
| DEF-001 | Article Viewer optimistic updates | In Progress | Manual Refresh |
| DEF-002 | Topic Explorer keyboard nav | TODO | Use mouse |
| DEF-003 | Twitter media 404s | By Design | Re-collect tweets |
| DEF-004 | @sama duplicate detection | Known | Timezone fix script |
| DEF-005 | React key warning | Won't Fix | None needed |
| DEF-006 | Substack HTML previews | Has Fix | `python fix_previews.py` |
| DEF-007 | Gary Marcus attribution | Known | Manual correction |
| DEF-008 | Twitter rate limiting | Has Fix | Use collector service |

### Common Fixes

```bash
# Fix Substack previews
cd backend && python fix_previews.py

# Re-collect tweets for fresh media URLs
cd backend && python collect_tweets.py

# Use rate-limited collector
cd backend && python tweet_collector_service.py
```

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

### ✅ Phase 6: MongoDB Migration for Tag System (COMPLETE - January 22, 2025)
- **MongoDB Setup**: Installed MongoDB Community Edition via Homebrew
- **Data Migration**: Migrated all tag concepts from SQLite to MongoDB
  - 116 concepts with full poly-hierarchy support
  - 308 aliases for synonym resolution
  - 2,089 tag instances tracking usage
- **Collections Created**:
  - `tag_concepts_v2`: Main concept definitions with hierarchy
  - `tag_aliases_v2`: Aliases and synonyms
  - `tag_instances`: Actual tag usage on content
- **API Updates**: New MongoDB-based API with singleton connection pattern
- **Benefits**:
  - Poly-hierarchy support (concepts can have multiple parents)
  - Flexible schema for entity types, icons, colors
  - Better performance for hierarchical queries
  - Built-in text search capabilities

## MongoDB Tag System

### MongoDB Collections
```
smarttrendtracer database:
├── tag_concepts_v2     # 116 concept definitions
├── tag_aliases_v2      # 308 aliases/synonyms  
└── tag_instances       # 2,089 usage records (647 resolved, 1,442 orphans)
```

### MongoDB Service Management
```bash
# Start MongoDB
brew services start mongodb-community

# Stop MongoDB
brew services stop mongodb-community

# Restart MongoDB
brew services restart mongodb-community

# Check status
brew services list | grep mongodb
```

### Tag System Migration Commands
```bash
# Setup MongoDB collections and indexes
python setup_mongodb.py

# Migrate tags from SQLite to MongoDB
python migrate_tags_to_mongodb.py

# Verify migration
python -c "from pymongo import MongoClient; client = MongoClient(); db = client.smarttrendtracer; print(f'Concepts: {db.tag_concepts_v2.count_documents({})}'); print(f'Orphans: {db.tag_instances.count_documents({\"concept_id\": None})}')"
```

## Known Issues & Future Improvements

> **See `DEFECTS.md`** for full issue tracking. Technical debt items listed as DEBT-XXX.

### Technical Debt (DEBT-001)
- Tag Ontology uses MongoDB, but some legacy patterns remain
- See `TAG_SYSTEM_ANALYSIS.md` for migration plan

### Future Enhancements
- Complete Semantic Scholar API integration
- Add CrossRef API for DOI metadata
- Implement Google Scholar tracking
- Performance optimization for large datasets

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

## Environment Variables

```bash
# MongoDB (optional - defaults to localhost)
MONGODB_URL=mongodb://localhost:27017/

# OpenAI API
OPENAI_API_KEY=your_key_here

# Other LLM APIs as needed
GEMINI_API_KEY=your_key_here
```

## System Architecture Overview

### Current State (Full MongoDB - Completed January 24, 2025)
```
┌─────────────────────────────────────────┐
│            MongoDB                      │
├─────────────────────────────────────────┤
│ tweets (1,169 documents)               │
│ papers (34 documents)                  │
│ articles (40 documents)                │
│ substack_authors (13 documents)        │
│ tag_concepts_v2 (1,746 concepts)       │
│ tag_aliases_v2 (308 aliases)           │
│ tag_instances (2,854 instances)        │
│ collection_state (tweet collector)     │
└─────────────────────────────────────────┘
              ↑
              │
      ALL Data Operations

SQLite: Retired (backup at data/tweets.db)
```

### Migration Complete
- **Full System Migration**: All data moved from SQLite to MongoDB
- **1,169 tweets**, **34 papers**, **40 articles** migrated
- **Tweet collector** updated to use MongoDB
- **All APIs** now use MongoDB exclusively
- **SQLAlchemy removed** from dependencies

## Important Configuration Notes

- **NEVER hardcode prompts or LLM access** - always use `llm.json` and `prompts_config.json`
- **GROBID Server**: External service at https://kermitt2-grobid.hf.space (no local installation needed)
- **Image Storage**: Paper images stored in `data/paper_repository/{paper_id}/images/`
- **PDF Processing**: Supports both Marker and MinerU services for extraction

Last updated: September 16, 2025

## System Status: All Critical Issues Resolved ✅

### Latest Completions (September 16, 2025)
- ✅ **Book Management System**: Complete PDF/EPUB book library with extended processing, faceted browsing, and concept integration
- ✅ **Extended Processing Services**: 6-hour timeouts for Marker, 5-hour for MinerU, native EPUB support
- ✅ **Book-Specific Features**: Table of contents extraction, glossary detection, reading difficulty assessment
- ✅ **Full API Integration**: Background and direct processing endpoints with comprehensive error handling

### Latest Fixes (September 1, 2025)
- ✅ **ACL Author Extraction**: All 24 ACL papers now show authors correctly in edit dialog
- ✅ **Date Format Warnings**: HTML date inputs use proper "yyyy-MM-dd" format
- ✅ **React Hooks Violations**: Frontend builds without development warnings
- ✅ **ACM Import Reliability**: Enhanced error handling for access-restricted papers
- ✅ **Author Field Consistency**: All import sources use unified author schema

### New Features (September 14, 2025)

#### Large Document Virtual Scrolling - COMPLETE
**Problem**: Books and large documents (>200KB) cause performance issues when rendered all at once
**Solution**: Implemented intelligent virtual scrolling with lazy loading for large documents

**Features Implemented**:
- **Automatic Detection**: Documents >200KB automatically switch to "Large Document Mode"
- **Smart Chunking**: Splits content into 50KB chunks at natural paragraph boundaries
- **Lazy Loading**: Initially loads first 3 chunks, others load as user scrolls
- **Performance Optimized**:
  - Intersection Observer for efficient scroll tracking
  - Pre-loads chunks 500px before viewport
  - Memoized components prevent re-renders
- **User Experience**:
  - Blue banner shows "Large Document Mode" with chunk statistics
  - Loading placeholders with animations for unloaded sections
  - Table of Contents works seamlessly across all chunks
  - All navigation features (keyboard shortcuts, TOC clicking) remain functional
- **Backward Compatible**: Regular papers (<200KB) render normally without changes

**Technical Details**:
- Location: `frontend/src/components/PaperViewerOptimized.tsx`
- Thresholds: 200KB for large doc mode, 50KB per chunk
- Components: `MarkdownChunk` component handles individual chunk rendering
- State: Tracks `isLargeDocument`, `documentChunks`, `loadedChunks`

**Benefits**:
- Fast initial load even for 1000+ page books
- Smooth scrolling without lag
- Memory efficient - only renders visible content
- Scales from small papers to full textbooks

### Latest Fixes (September 15, 2025)

#### Twitter Retweet Truncation Fix - COMPLETE
**Problem**: Retweets were being truncated with "..." showing only partial content instead of full original tweet text
**Example**:
- **Before**: `"RT @laurentsifre: We've been cooking this summer: Holo1.5 is here! SOTA UI localization + QA, 3× gains vs Qwen-2.5 VL 🍳 Now up to 72B 💥 — a…"`
- **After**: `"RT @laurentsifre: We've been cooking this summer: Holo1.5 is here! SOTA UI localization + QA, 3× gains vs Qwen-2.5 VL 🍳 Now up to 72B 💥 — a strong base for computer-use agents like Surfer. • Open weights on HuggingFace 🤗 https://huggingface.co/Hcompany/Holo1.5-7B • Blog post 📝 https://hcompany.ai/blog/holo-1-5 (1/n 🧵)" + Media`

**Root Cause**: The `tweet_collector_service.py` was missing critical API parameters for fetching full retweet content
**Solution Applied**:
- **Enhanced API Request**: Added `'referenced_tweets.id'` and `'referenced_tweets.id.attachments.media_keys'` to expansions parameter
- **Referenced Tweets Processing**: Added logic to extract and process referenced tweets from API response
- **Text Replacement Logic**: Implemented smart text replacement that preserves "RT @username:" prefix while appending full original text
- **Media Handling**: Enhanced to capture media from original tweets in retweets

**Technical Implementation**:
- Location: `backend/tweet_collector_service.py` lines 550, 578-611
- **API Enhancement**: Uses existing requests more efficiently - no additional API calls required
- **Basic API Compatible**: Works within 15K tweets/month limit
- **Rate Limit Friendly**: Respects all existing rate limiting and tiered collection

**Benefits**:
- Complete retweet content with full text and media
- No impact on API usage limits
- Backward compatible with existing data
- Maintains all existing collector features and optimizations

### Technical Notes
- No batch mode for Concept reorganization! GPT-5 can handle ~3000 Concepts, if not, we use Gemini 2.5 Pro with large Context Window
- Always update existing implementations rather than creating new applications
- Virtual scrolling automatically activates for documents >200KB
- Twitter retweets now capture complete original content instead of truncated versions