# SmartTrendTracer - Claude Assistant Documentation

<!-- smooth-switch-current:start -->
## Smooth Switch — current implementation (2026-09-07)

This section is the current handoff contract; earlier dated session notes below describe historical behavior. General standard: [smooth_switch.md](../../smooth_switch.md); commands and limitations: [runtime README](../../smooth-switch/README.md). Run commands from the project root.

- `./smooth-switch doctor` / `status` are read-only inventory checks, not application health tests. `setup` prints a plan; `setup --apply` installs local dependencies without importing data or starting services.
- `smooth-switch.json` defines transferable assets. The project wrapper uses the vendored runtime; update the central implementation and run its `vendor.py` when changing shared behavior.
- Stop all project writers before `prepare --to DEVICE --writers-stopped`. Review `receive PACKAGE` (first transfer: `--initial`), then apply the identical plan with its token and `--writers-stopped`. Use `rollback` for reviewed recovery. Data packages do not transfer source code; synchronize the matching code separately.
- `guard` blocks starts in released/importing/failed states. `guard --export` additionally blocks exports where initial import is required but incomplete. An outstanding first import alone does not block normal starts or imports. This is cooperative single-writer handoff, not a distributed lock.
- Local state/backups: `~/.local/state/smooth-switch/smarttrendtracer/`; transfer outbox defaults to `~/SmoothSwitch/smarttrendtracer/`. Keep secrets (`~/.env`), native environments, PIDs, caches and service registrations local. Include `smooth-switch.ignore` at the actual Syncthing root; do not sync raw active databases or native environments.
- A complete Mac → Linux → Mac acceptance test is still outstanding. Do not infer application readiness from an installed adapter or successful import.

Imported `dump_DenkZentrale_20260906_214843.tar.gz` into `smarttrendtracer`: 23 collections / 236,975 documents, verified against the Mac archive. Local handoff state is initialized/received. The initial export restriction is cleared here; do not repeat the import merely to start the app. Backend/frontend, collectors, OCR/ML services and external integrations have NOT yet been exercised in this Linux test session. Samanta's successful application test does not certify STT.

Pause backend/frontend, collectors, cron jobs, converters and book workers before handoff; shared MongoDB stays running. Existing `start_stt.sh`/`stop_stt.sh` retain legacy service-management behavior and still require a separate runtime audit; do not use MongoDB-stop options for an individual app. Provision Python 3.12/backend and frontend dependencies locally via the adapter; optional Marker/MinerU environments need their own setup. Review media, documents and `accounts.json` separately.

Shared database operations: see [MongoDB service](../../infrastructure/mongodb/README.md) and [verified import status](../../infrastructure/mongodb/IMPORT_STATUS.md). Linux uses shared `development-mongodb` (MongoDB 8.3.8, loopback :27017); database for this app is `smarttrendtracer`. Keep application/database/import lifecycle separate; never set one global database name for all apps. The Compose rseq setting is local infrastructure, not a host-kernel change. Logical dumps preserve modern `prelude.json` metadata; empty-target rollback was tested separately.

Legacy `scripts/sync-in.sh` now delegates to `legacy-receive` and requires an explicit archive/SHA-256 and reviewed apply token. `sync-out.sh` requires destination and writer-pause acknowledgement. No automatic latest-dump selection, backup bypass or unattended hourly export is supported by these wrappers. Existing schedulers were not enabled by these changes.

<!-- smooth-switch-current:end -->

## 1. Project Overview

SmartTrendTracer (STT) is a comprehensive AI content monitoring system that collects and
analyzes content from Twitter/X, Substack newsletters, Reddit, research papers, and books
to identify emerging trends, hot topics, and declining discussions in the AI space.

### Data Sources

**Twitter/X** — 21 monitored accounts, managed via the Twitter Account Manager UI and
stored in `backend/accounts.json` / MongoDB. Current set:
@OpenAI, @emollick, @stanfordnlp, @AnthropicAI, @GoogleDeepMind, @huggingface, @sama,
@kaggle, @rasbt, @JayAlammar, @hwchase17, @Sebastienbubeck, @Shayneredford, @Langchainai,
@Colm_Conf, @GH_Wiegand, @ABosselut, @LorenaRaichle, @_akhaliq, @zurichnlp, @AiBreakfast.
Collection runs in Basic Account Mode by default (10k tweets/month budget, tiered
priorities, 15-minute intervals).

**Substack newsletters** — collected from Gmail (direct subscriptions, e.g. Ethan Mollick
"One Useful Thing") and forwarded university mail. Forwarded authors are configured in
`backend/forwarded_authors.json`: Gary Marcus (Marcus on AI), Nathan Lambert
(Interconnects), Sebastian Raschka (Ahead of AI). ~14 authors in the database.

**Reddit** — AI/ML subreddits configured in `backend/reddit_config.json`:
r/LLM, r/LLMDevs, r/LocalLLM, r/MachineLearning, r/artificial, r/OpenAI, r/ChatGPT,
r/singularity. Collected via PRAW (`app/collectors/reddit_collector.py`; requires
REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET).

**Research papers** — PDF upload plus importers for arXiv, ACL Anthology, ACM DL,
OpenReview, JAIR, DBLP and direct URLs. Processed with Marker or MinerU, enriched via
GROBID (external server https://kermitt2-grobid.hf.space), analyzed with LLMs.
A separate **review mode** (`paper_type: 'review'`) keeps papers under review out of
global statistics, trends, and the RAG index (default is `paper_type: 'research'`).

**Books** — PDF/EPUB library with extended processing timeouts (Marker 6h, MinerU 5h),
TOC extraction, reading-difficulty assessment. Processing jobs are queued in
`book_processing_jobs` and consumed by `backend/book_processing_worker.py`
(started by `start_stt.sh`).

All content types share one concept/tagging system (poly-hierarchical ontology),
faceted dashboards, entity extraction, batch annotation, and a concept-based RAG search
with automatic trend-query detection.

---

## 2. Architecture

### Stack

- **Backend**: FastAPI + MongoDB (PyMongo). Fully migrated — SQLite/SQLAlchemy are gone.
- **Frontend**: React + TypeScript + Vite, Tailwind + shadcn/ui, react-force-graph-2d,
  framer-motion. Config: `frontend/.env` (`VITE_API_URL=http://localhost:8088`),
  proxy in `vite.config.ts`.
- **PDF services**: Marker (port 8002) and MinerU (port 8003), each with its own venv
  (`backend/marker_service/marker_env`, `backend/mineru_service/mineru_env`).
  Only Marker has the real-time progress pipeline (PTY output capture, TQDM parsing,
  psutil CPU/RAM health, progress callbacks to the backend). MinerU does **not** —
  the pipeline was documented but never implemented.
- **LLM access**: central `llm_manager` / LiteLLM router driven by `backend/llm.json`,
  `backend/prompts_config.json` and `backend/litellm_config.yaml`. Providers: Anthropic,
  OpenAI, Google (Gemini), xAI. Keys come from `~/.env`.

### MongoDB Collections (database `smarttrendtracer`, localhost:27017)

| Collection | Approx. size | Content |
|---|---|---|
| `tweets` | ~27k | Tweet documents; **`_id` is the Twitter ID string**, not ObjectId |
| `papers` | ~360 | Papers incl. content, analyses, review fields (`paper_type`) |
| `articles` | ~560 | Substack/imported articles |
| `books` | few | PDF/EPUB books |
| `reddit_posts` | varies | Reddit posts |
| `tag_concepts_v2` | ~25k | Concept ontology (poly-hierarchy); `_id` is ObjectId |
| `tag_instances` | ~129k | Tag usage (content_type/content_id/concept_id) |
| `tag_aliases_v2` | ~330 | Concept aliases/synonyms |
| `substack_authors` | ~14 | Newsletter authors |
| `references` | ~2.4k | Normalized paper references |
| `book_processing_jobs` | queue | Consumed by book_processing_worker.py |
| `collection_state` | 1-few | Tweet collector state |

Backend startup creates/repairs indexes centrally in
`app/database/mongodb.py::_ensure_indexes` (incl. combined text indexes
`papers_text_search` / `articles_text_search` / `tweets_text_search`; legacy
single-field text indexes are dropped in `main.py` startup). Index creation on a fresh
import can take 30-60s — hence the 60s backend startup timeout.

### Repository Layout (orientation)

```
SmartTrendTracer/
├── start_stt.sh / stop_stt.sh      # start/stop all services
├── setup_python.sh                 # venv + frontend setup
├── mise.toml                       # Python 3.12 pin
├── .db-sync-config                 # MongoDB sync settings
├── scripts/                        # setup.sh, sync-out/in/status.sh, sync_manual.md
├── db-sync/                        # dumps/ (synced), backups/ (local only)
├── docs/
│   └── funktionsinventur.md        # 2026-07-24 full function inventory + fix status
├── DEFECTS.md                      # defect tracking
├── AUTHOR_UI_DESIGN.md             # planned author-management UI
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, router registration, startup index care
│   │   ├── api/                    # routers; larger areas are packages
│   │   │   │                       #   (tweets/, papers/, books/, articles/, article_import/,
│   │   │   │                       #    twitter_accounts/, statistics/, system_stats/,
│   │   │   │                       #    analytics_trends/, tag_ontology/, tag_reorganization/)
│   │   ├── config.py               # Settings singleton — the ONLY place env vars are read
│   │   ├── paths.py                # data paths (+ *_REL forms as persisted in MongoDB)
│   │   ├── collectors/             # gmail_substack_collector, reddit_collector, playwright
│   │   ├── database/mongodb.py     # client singleton + _ensure_indexes, concept_id_query_variants
│   │   ├── repositories/           # data-access layer: queries + their rules (tweets save path,
│   │   │                           # facets, stats, authors); raise repositories.errors, never HTTP
│   │   └── services/               # llm_manager (the only LLM stack), pdf_service_client
│   │                               # (Marker/MinerU), rag/, analytics/, anomaly_detection, …
│   ├── tests/                      # pytest: regression tests + test_arch_guard.py (layer rules)
│   ├── tweet_collector_service.py  # standalone Twitter collector
│   ├── book_processing_worker.py   # consumes book_processing_jobs queue
│   ├── llm.json / prompts_config.json / litellm_config.yaml
│   ├── marker_service/  (+ marker_env)   # Marker PDF service, port 8002
│   ├── mineru_service/  (+ mineru_env)   # MinerU PDF service, port 8003
│   └── data/                       # papers, paper_repository, book_repository,
│                                   # rag_index_concepts (FAISS), media, tei_xml, …
└── frontend/                       # React/TS/Vite app: src/components/<feature>/ (no flat
                                    # files), src/services/http.ts (only axios importer), src/config
```

### Port Allocation

| Project | Ports |
|---|---|
| **STT Backend** | **8088** (`BACKEND_PORT`, exported by start_stt.sh) |
| STT Frontend (Vite) | 3470 |
| STT Marker / MinerU | 8002 / 8003 |
| MongoDB | 27017 |
| Honcho (Docker — occupies 8000!) | 8000, 5433, 6379 |
| Samanta | 3270, 8100, 8800 |
| StatCoach | 8888, 3001, 5432 |
| Docendi | 3005, 8005 |

Never use port 8000 for STT — Honcho's Docker container binds it. CORS origins default
to `http://localhost:3470` (plus 3000/3001/3002); override via `CORS_ORIGINS` env var.

---

## 3. Development Requirements (MANDATORY)

SmartTrendTracer must work seamlessly on both macOS and Linux (project is synced via
Syncthing between machines).

### 3.1 Path Handling — dynamically determined absolute paths

Always use the `$SCRIPT_DIR` pattern in shell scripts. Never hardcode absolute paths,
never rely on relative paths (they break after `cd backend` etc.):

```bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="$SCRIPT_DIR/logs/startup.log"
```

### 3.2 Virtual Environments — explicit paths, validated

- Always call venv binaries explicitly (`venv/bin/python`), **never**
  `source venv/bin/activate` before `nohup ... &` — background processes do not inherit
  the activated environment.
- venvs synced between macOS and Linux have broken symlinks. Validate before use and
  recreate if invalid:

```bash
check_venv_valid() {  # valid if bin/python exists and is executable
    [ -d "$1" ] && [ -x "$1/bin/python" ]
}
```

`setup_python.sh` and `start_stt.sh` do this automatically for backend venv,
marker_env and mineru_env. Frontend `node_modules` also contain platform-native modules
(`@rollup/rollup-darwin-*` vs `-linux-x64-gnu`) — run `npm install` after switching
platforms.

### 3.3 MongoDB Cross-Machine Synchronization

Use the current Smooth Switch contract above. Shared MongoDB stays running while this project's writers are paused. Review explicit snapshots rather than choosing the latest dump by time. This Linux device has already received the verified Mac dump; application testing is still pending.

### 3.4 Environment Variables — API keys in `~/.env`, never in the project

`~/.env` (home directory, synced across machines, not in git) contains all LLM keys:
`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`/`GEMINI_API_KEY`, `XAI_API_KEY`,
plus `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET`. Do **not** use `backend/.env`.
`start_stt.sh` auto-loads it with `set -a; source "$HOME/.env"; set +a`
(works with or without `export` prefixes).

**Code reads configuration only via `from app.config import settings`** (pydantic
Settings). No `os.getenv` anywhere else — enforced by `tests/test_arch_guard.py`.
Marker/MinerU URLs and the progress-callback URL come from
`app.services.pdf_service_client`; data paths from `app.paths`.

### 3.5 Service Startup Timeouts

- Backend API: **60 seconds** (MongoDB index creation on large collections)
- Marker / MinerU: 30 seconds (default)

### 3.6 Comprehensive Logging

All startup scripts create timestamped logs (`logs/startup_YYYYmmdd_HHMMSS.log`) via a
`log()` function with `tee`. Must include: timestamps, PIDs of all services, port checks,
startup timing, Python/venv paths, MongoDB connection status.

### 3.7 Platform Detection

> Legacy service-management behavior below still needs a runtime audit; do not stop shared MongoDB for STT handoff.

Scripts detect the platform via `$OSTYPE` and use the appropriate commands:

| Operation | macOS | Linux |
|---|---|---|
| MongoDB start/stop | `brew services start/stop mongodb-community` | `systemctl start/stop mongod` |
| File timestamps | `stat -f` / `date -r` | `stat -c` |

Python version is pinned via `mise.toml` (Python 3.12); scripts activate mise if present.

### 3.8 Configuration Rules

- **NEVER hardcode prompts or LLM model access.** Models/temperatures come from
  `backend/llm.json` (per task type), prompts from `backend/prompts_config.json`,
  the LiteLLM router from `backend/litellm_config.yaml`. All LLM calls go through the
  central `llm_manager` (the former parallel `llm_service` stack was removed 2026-09):
  `llm.get_prompt(key)` for prompts, `llm.complete_text(task_type, ...)` for single-turn
  calls, and `llm.resolve_model_override(ui_value)` to map a UI model choice to a
  routable model_name. Never write per-endpoint model alias dicts — they silently
  ignored every model not listed in them. Retries/fallbacks belong in the router config.
- **Deprecated models must not appear in any selection list** (backend defaults,
  litellm_config model lists, `frontend/src/config/models.ts`). Removed models are
  mapped to successors via `MODEL_MIGRATION_MAP`
  (`app/api/llm_preferences.py` / `app/services/llm_manager.py`); saved user preferences
  pointing to dead models are detected at startup and migrated via
  `POST /api/llm/preferences/migrate`.
- **Feature policy: extend existing modules, never create parallel implementations.**
  The 2026-07-24 function inventory traced most real bugs to exactly such parallel
  implementations (duplicate tag services, a second tweet-save path with an incompatible
  schema, duplicate footer cleaners).

### 3.9 Code Conventions (learned the hard way — do not regress)

- **Register static routes before `/{id}` routes.** FastAPI matches in registration
  order; `GET /{book_id}` registered before `GET /facets` shadows it into a 404.
  Applies to every APIRouter package (`books/__init__.py`, `articles/__init__.py`, …).
- **`tag_instances.concept_id` is stored in mixed form: ObjectId (~98%), plus
  legacy slug-string ids like `c_method_...` (from 177 concepts whose `_id` is a
  string).** Any count/lookup must query all variants — use
  `app.database.mongodb.concept_id_query_variants(cid)` (id in hand) or
  `app.api.tag_ontology.utils.concept_id_variants(concept)` (document in hand)
  with `{'concept_id': {'$in': variants}}`. A single-form query silently drops rows.
- **`tweets._id` is the Twitter ID string** — never insert tweets with an auto ObjectId
  `_id` or a separate `tweet_id` field. All writers use `app.repositories.tweets`
  (`build_tweet_document`, `insert_tweet_if_new`, `advance_collection_state` — the
  latter keeps `last_tweet_id` monotonic via `$max`).
- **Layering (enforced by `tests/test_arch_guard.py`):** api → services → repositories/
  database, never upward; no import cycles; import packages via their `__init__`, not
  their internal submodules. New MongoDB queries go into `app/repositories/`, not into
  routers — the guard ratchets the remaining API-layer query count (lower it when you
  move queries). Repositories raise `app.repositories.errors.*` (mapped to HTTP in
  `app/main.py`); a repository that needs a service gets it injected as a parameter.
- **Frontend:** HTTP only via `src/services/http.ts` (plus `apiErrorMessage`); components
  live in `src/components/<feature>/` — the guard fails on direct axios imports or new
  flat files in `components/`.
- **`tag_concepts_v2._id` is ObjectId** — wrap incoming string IDs with `ObjectId()`.
- **MongoDB filters: use `{'$nin': [None, '']}`**, never `{'$ne': None, '$ne': ''}` —
  Python dict deduplication silently drops the first key.
- **`tag_instances.created_at` is a native BSON datetime** — never insert
  `.isoformat()` strings; query with datetime objects. Use
  `datetime.now(timezone.utc)` (naive `utcnow()` is deprecated and caused
  naive/aware TypeErrors).
- **When modularizing/moving files**: re-check relative imports
  (`..services` vs `...services`) and `Path(__file__).parents[n]` depths — both broke
  silently during past refactors.
- Prefer `except Exception:` over bare `except:`; never swallow `HTTPException` in a
  generic `except` (turned documented 400s into empty 200s).

---

## 4. Key Commands

### Start / Stop

```bash
./start_stt.sh          # MongoDB, backend :8088, Marker :8002, MinerU :8003,
                        # book_processing_worker, frontend :3470.
                        # Also: resets stale processing_* statuses to 'pending',
                        # runs paper_type migration, loads ~/.env, validates venvs.
./stop_stt.sh           # interactive (asks about MongoDB)
# Do not use -y/--mongo-yes with shared MongoDB.
./stop_stt.sh -n        # keep MongoDB running (--mongo-no)
```

After port/env changes: hard-reload the browser (Cmd+Shift+R) so Vite picks up `.env`.

### Setup

```bash
./scripts/setup.sh              # full cross-platform setup (detects macOS/Linux)
./scripts/setup.sh check        # status only (also: mongodb|python|frontend|sync)
./setup_python.sh               # Python venvs + frontend (also: backend|frontend|check|activate)
```

### Machine Sync

```bash
./scripts/sync-out.sh           # export MongoDB (end of session)
./scripts/sync-status.sh        # show sync status of all systems
./scripts/sync-in.sh            # import (start of session on other machine)
```

### Collectors

```bash
cd backend
python tweet_collector_service.py            # Basic Account Mode default, 15-min loop
./start_basic_collector.sh                   # wrapper for the above
python -m app.collectors.gmail_substack_collector             # Gmail newsletters
python -m app.collectors.gmail_substack_collector --forwarded # forwarded only
python -m app.collectors.reddit_collector                     # Reddit posts
```

### Maintenance (all in `backend/`, all MongoDB-based)

```bash
python monitor_collection.py          # live collection status, 5s refresh (--once for snapshot)
python check_collection_state.py      # tweet collector state
python check_tag_consistency.py --analyze   # (or --fix, --test "tag")
python rebuild_rag_index.py           # rebuild concept RAG FAISS index
python clean_substack_footers.py --clean    # (or --test)
python fix_previews.py                # fix article previews
python summarize_articles.py          # batch article summaries
```

### MongoDB Quick Checks

```bash
mongosh smarttrendtracer --eval "db.tweets.countDocuments({})"
mongosh smarttrendtracer --eval "db.papers.countDocuments({paper_type: 'review'})"
mongodump --db smarttrendtracer --out backup_$(date +%Y%m%d)   # backup
```

---

## 5. API Surface (overview)

Router registration lives in `backend/app/main.py` (~266 routes). One line per prefix:

| Prefix | Module | Content |
|---|---|---|
| `/api/tweets` | `api/tweets/` | browse, `faceted-search`, hierarchy-facets, per-tweet concepts, batch-annotate(+`-all`, status, cancel) |
| `/api/papers` | `api/papers/` | CRUD/upload/facets, Marker/MinerU processing + progress/health callbacks, analyses, entities, concepts/tags, snippets, sections, references, TEI/PDF/images, GROBID, affiliations |
| `/api/papers` (also) | `direct_url_import` | `POST /import-url`, `GET /validate-url` |
| `/api/papers/dblp`, `/api/dblp` | `dblp_mongodb` | DBLP search/BibTeX/metadata |
| `/api/books` | `api/books/` | CRUD/upload/facets, concepts, content, `process` (queue → worker) / `process-direct` |
| `/api/articles` | `api/articles/` | browse/faceted-search, concepts/snippets, **author management** (`/authors/...`), extract-metadata, tags/suggest, summarize, recollect. (Old `/api/substack/articles` paths are gone.) |
| `/api/v2/articles` | `article_import/` | URL import: smart dispatch, cookies, Playwright, batch |
| `/api/article-preview` | `article_preview` | regenerate / beautify previews |
| `/api/article-clustering` | `article_clustering_mongodb` | k-means/topic clustering |
| `/api/substack` | `substack_mongodb` | `/trends` (concept-based tags/growth/velocity), `/health` |
| `/api/reddit` | `reddit_mongodb` | faceted-search, facets, tags, collect, stats |
| `/api/twitter-accounts` | `api/twitter_accounts/` | account CRUD, lookup, stats/dashboard/usage (10k budget), collector-status, toggle/refresh/collect |
| `/api/authors` | `authors_management` | author merge/analytics endpoints — **UI not built yet** (see AUTHOR_UI_DESIGN.md) |
| `/api/statistics`, `/api/system` | `statistics/`, `system_stats/` | statistics dashboards |
| `/api/trends`, `/api/trends/analysis`, `/api/user-trends` | trends modules | trend queries and analysis |
| `/api/analytics/trends` | `analytics_trends/` | Trend Dashboard data: at-a-glance, heatmap, bubble-chart, network, cooccurrence, animated-timeline; AI summarization (`/summarize`) |
| `/api/topics` | `topic_explorer` | frequency / correlation / popular topics |
| `/api/rag` | `rag_concepts` | `ask` (auto trend detection), stats, rebuild, sample-questions |
| `/api/ontology`, `/api/ontology-graph` | `tag_ontology/`, `ontology_graph` | concept ontology CRUD + visualization |
| `/api/concepts/suggestions` | `concepts_suggestions_mongodb` | concept suggestions for content |
| `/api/concepts/organization` | `concept_organization` | organizing unorganized concepts |
| `/api/tags/reorganize` | `tag_reorganization/` | async ontology reorganization (SSE + apply) |
| `/api/entities` | `entity_extraction` | entity extraction & review |
| `/api/llm` | `llm_preferences` | model preferences, status, deprecated-model migration |
| `/api/user-settings` | `user_settings` | per-user key-value settings (TweetDeck columns etc.) |
| `/api/arxiv`, `/api/acl-anthology`, `/api/acm`, `/api/openreview`, `/api/jair` | importers | paper imports |
| `/api/references` | `references` | normalized references, top-cited, import (arXiv path; DOI → 501) |
| `/api/pdf` | `pdf_export` | article PDF export |
| `/api/media-gallery` | `media_gallery_mongodb` | Twitter media gallery |
| `/health`, `/` | `main.py` | health check (DB counts + Marker/MinerU status) |

Static mounts: `/papers` (PDF dir), `/books` (book repository).

### Notable behaviors

- **Paper review mode**: `paper_type` param on papers list/upload/facets/stats; review
  papers are excluded from global stats, trends and the RAG index.
- **RAG trend detection**: `/api/rag/ask` detects trend keywords, retrieves 50 docs and
  returns `is_trend_analysis` / `documents_analyzed` / `source_type` metadata; supports
  `content_types` filtering with proportional blending across types and
  `concept_filter`.
- **Batch annotation**: `/api/tweets/batch-annotate[-all]` with in-memory task state
  (404 after backend restart is handled frontend-side), concurrency 1-8, cancel support.
- **Suggest Concept Tags / Entity Extraction** on papers require processed content
  (HTTP 400 otherwise; frontend disables the buttons).
- **Analyses saves are atomic** (`$push`/`$pull`, never `$set` of the whole array) to
  survive concurrent generation.
- Global exception handlers sanitize 500s; request timing middleware adds
  `X-Process-Time-Ms` and logs slow requests (>1s).

---

## 6. Configuration Files

| File | Purpose |
|---|---|
| `backend/llm.json` | Model per task type (tag_suggestion, summarization, trend_analysis, paper_section_extraction, …). Includes **`models.rag_embedding`**: primary `models/text-embedding-004` (Google, 768d), fallback `text-embedding-ada-002` (OpenAI, 1536d). **Changing embedding model/dimension requires rebuilding the FAISS index** (`rebuild_rag_index.py`, index at `data/rag_index_concepts`). |
| `backend/prompts_config.json` | All LLM prompts/templates (incl. paper analyses catalog, rag_trend_analysis). Never inline prompts in code. |
| `backend/litellm_config.yaml` | LiteLLM router model list. No explicit `api_key:` lines — keys are auto-detected from env. Gemini 3 preview models pinned to temperature 1.0 (infinite-loop bug below 1.0). |
| `backend/reddit_config.json` | Monitored subreddits, priorities, score thresholds. |
| `backend/forwarded_authors.json` | Forwarded-newsletter author matching (name/email/search patterns). |
| `backend/accounts.json` | Twitter accounts (also managed via UI/DB). |
| `.db-sync-config` | MongoDB sync settings (dump dir, retention, backup-before-import). |
| `frontend/.env` | `VITE_API_URL=http://localhost:8088`. |
| `frontend/src/config/models.ts` | Model choices shown in the UI — keep in sync with litellm_config (no deprecated models). |
| `mise.toml` | Pins Python 3.12. |

---

## 7. Known Issues & Open Work

Full defect list with priorities: **`DEFECTS.md`** (currently open: DEF-003 Twitter media
URL expiry [by design], DEF-005 React key warning [won't fix — floods the console in
Concept Graph/Management], DEF-007 Gary Marcus attribution [fixed in code, latent],
DEF-008 rate limiting [use collector service]. DEF-001, -002, -004, -006 are resolved).

Open work items (state after the 2026-07-24 inventory + fix pass, see
`docs/funktionsinventur.md`):

1. **Test suite is thin** (H-Q1): `backend/tests/` has 58 pytest tests (regression tests
   for 2026-08/09 fixes + the architecture guard), no endpoint integration tests and no
   frontend tests yet. Next: httpx TestClient for the core endpoints.
2. **MinerU progress pipeline not implemented** — only Marker has PTY/TQDM/psutil
   progress reporting; MinerU processing shows no live progress (deliberately not built,
   docs corrected instead).
3. **DOI-based reference import returns 501** — CrossRef integration planned
   (`references.py`).
4. **Author merge/analytics UI missing** — `/api/authors` endpoints exist and are kept
   deliberately; UI design in `AUTHOR_UI_DESIGN.md`.
5. **Reddit UI gaps** — frontend only uses `faceted-search` + `facets`; the collect
   trigger and stats endpoints are kept but have no UI.
6. **"Coming Soon" views** in navigation (author-analytics, author-merge, reddit-trends,
   books-analysis) are placeholders.
7. **Semantic concept search is lexical** (text + alias matching with relevance tiers);
   an embedding-based search would reuse the existing FAISS stack.
8. **Architecture debt, ratcheted** (arch audit 2026-09): 387 MongoDB call sites remain
   in `app/api/` (was 565; hotspots `authors_management`, `papers/content`,
   `articles/content` next) — move them into `app/repositories/` and lower
   `API_DB_CALL_SITES_MAX`. Frontend domain API modules can grow on `services/http.ts`.
9. **Nondeterministic top-N lists** in `/api/papers/facets` (authors, concepts,
   institutions) and `/api/papers/stats/overview` (top_concepts, top_conferences):
   truncated without a stable tie-break, so repeated calls return different sets.
10. Pre-existing frontend `tsc` error count: 18 (non-blocking, build is green).

---

## 8. Changelog (condensed)

Details live in `git log` and `docs/`; do not re-expand here.

- **2026-07-24 — Function inventory + complete fix pass** (`docs/funktionsinventur.md`;
  commits a28dc269, b4799d3e, a1e17616). ~360 items audited; all P1/P2/P3 findings
  fixed: router shadowing (books/facets, articles/authors, without-author),
  ObjectId-vs-string usage counts, paper tag-delete stub + missing snippet POST,
  ACL/OpenReview/ACM background processing, media gallery sort/filter/search, topic
  explorer date filters, fake statistics values, RAG trend metadata + concept_filter,
  entity-review persistence, DEF-001; PERF-002 text indexes live, import schema drift
  (ACM/DBLP/JAIR/ACL/direct-url), book worker wired into start/stop scripts, real
  cancels, config-driven RAG embeddings (`llm.json rag_embedding`), deprecated models
  removed with MODEL_MIGRATION_MAP; ~60 dead files (~12k+ LOC) and ~90 dead endpoints
  deleted. Verified: 266 routes import, frontend build green.
- **2026-05-12** — Backend port migration 8000 → **8088** (Honcho Docker conflict);
  `BACKEND_PORT` env var everywhere, frontend `.env`/proxy updated.
- **2026-03-08** — Paper Review Mode: `paper_type` field, separate dashboard, review
  papers excluded from stats/trends/RAG.
- **2026-03-07** — Code-quality sweep: `datetime.now(timezone.utc)`, `$nin` fixes,
  batch `$in` lookups in anomaly detection, `tag_instances.created_at` → native BSON.
- **2026-01-28** — Trend Detection Dashboard (7 visualizations under
  `/api/analytics/trends`, `anomaly_detection.py` service); TimeWindowAnalysis with
  separate start/end sliders.
- **2026-01-25/26** — Atomic `$push`/`$pull` for concurrent analysis saves; papers
  facets 500/CORS fix (`$nin`, array-vs-string authors); Suggest Concept Tags requires
  processed content; stale `processing_*` cleanup at startup.
- **2026-01-23/24** — `scripts/` reorganization (setup.sh, sync scripts with SHA-256 +
  auto-backup); batch Marker processing ("Process All" with localStorage resume).
  A MinerU progress UI was documented but the pipeline never landed (see 2026-07-24).
- **2026-01-19/20/21** — RAG proportional blending across content types; cross-platform
  script rewrite (venv validation, node_modules checks); dashboard refresh buttons;
  TypeScript cleanup; legacy SQLite scripts purged (DEBT-001).
- **2026-01-04** — Paper date-type selection (import vs published) for summarization;
  "Generate All Analyses" made sequential with progress; arXiv import await-bug fix.
- **2025-12-24 → 30** — Cross-platform macOS↔Linux fixes (mise, ~/.env auto-load);
  LiteLLM key auto-detection; Gemini 3 array-response handling + temperature 1.0;
  model-name mapping fixes; Topic Explorer mouse selection; API key status banner.
- **2025-11-23** — Marker real-time progress: TQDM parser, progress callbacks to
  MongoDB, 10s frontend polling, CPU/RAM health.
- **2025-09-16** — Book management system (PDF/EPUB, extended timeouts, TOC/difficulty).
- **2025-09-15** — Retweet truncation fix (referenced_tweets expansions, full text).
- **2025-09-05** — Reddit integration (PRAW collector, API, dashboard).
- **2025-08-25 → 09-01** — Paper metadata/import fixes (ACL authors_detailed, ACM
  errors, date formats, React hooks); section editing; DBLP MongoDB API; LLM affiliation
  extraction; missing-data facets; external GROBID server.
- **2025-08-22** — Tag ontology migrated to MongoDB (poly-hierarchy, entity types).
- **2025-08-08 → 12** — RAG search implementation (FAISS + concept index); enhanced tag
  suggestions with vector store; shadcn/ui migration; Substack Gmail collection;
  Twitter timezone fix; automatic footer removal.
- **2025-01** — Full MongoDB migration of all content data (SQLite retired); trends &
  analytics phases; knowledge graph; unified tag filtering; text-selection tagging.

---

Last updated: July 24, 2026
