# SmartTrendTracer API Contract Audit

**Date:** 2026-03-06
**Version:** 2.0.0 (MongoDB Edition)
**Total Endpoints:** 343 (across 78 router files, 38 `include_router` calls in `main.py`)

---

## Executive Summary

**Health Score: F (17/100)**

SmartTrendTracer's API surface grew organically from a personal research tool to 343 endpoints without any contract governance. The three most urgent findings:

1. **Zero authentication** on all 343 endpoints, including destructive operations (DELETE, bulk mutations, index rebuilds).
2. **155 `str(e)` exception leaks** across 47 files expose internal stack traces, MongoDB ObjectId formats, and file paths to any caller.
3. **95% of endpoints lack a `response_model`**, meaning the OpenAPI spec documents almost nothing about what callers will receive.

**Methodology:** Static analysis of all files under `backend/app/api/`, correlated with `main.py` router registrations. Endpoint counts from `@router.(get|post|put|patch|delete)` regex. Pydantic model counts from `class \w+(BaseModel)` regex. Sample-based verification on 5 representative endpoints.

---

## Health Score Card

| # | Area | Weight | Score /10 | Grade | Rationale |
|---|------|--------|-----------|-------|-----------|
| 1 | Request Validation | 15% | 2 | F | 22% Pydantic coverage; 17 endpoints accept `Dict[str, Any]` bodies |
| 2 | Response Contracts | 15% | 1 | F | 18 `response_model` usages (5%); 3+ envelope patterns; wrong status codes |
| 3 | Error Handling | 15% | 1 | F | No global handler; 155 `str(e)` leaks; 3 inconsistent error keys |
| 4 | Authentication | 10% | 0 | F | Zero auth on any endpoint |
| 5 | Pagination | 10% | 3 | D | Two competing patterns; inconsistent defaults |
| 6 | Rate Limiting | 5% | 0 | F | None at endpoint level |
| 7 | Documentation | 10% | 3 | D | ~40% docstrings; sparse parameter descriptions |
| 8 | Naming & Versioning | 10% | 3 | D | Mixed naming; no versioning strategy |
| 9 | Consumer Experience | 10% | 2 | F | 1 PASS, 2 PARTIAL, 2 FAIL (see Section 9) |
| | **Weighted Total** | **100%** | **1.7** | **F** | **17/100** |

**Formula:** `Sum(weight_i * score_i) / 10 * 100`

---

## 1. Contract Inventory

### 1.1 Router Registrations (main.py:132-170)

38 `include_router` calls, listed by prefix:

| # | Prefix | Module | Tags |
|---|--------|--------|------|
| 1 | `/api/tweets` | tweets (package) | tweets |
| 2 | `/api/papers` | papers (package, 15 sub-routers) | papers |
| 3 | `/api/entities` | entity_extraction | entity_extraction |
| 4 | `/api/llm` | llm_preferences | llm |
| 5 | `/api/books` | books (package) | books |
| 6 | `/api/articles` | articles (package) | articles |
| 7 | `/api/authors` | authors_management | authors |
| 8 | `/api/twitter-accounts` | twitter_accounts (package) | twitter_accounts |
| 9 | `/api/substack` | substack_mongodb | substack |
| 10 | `/api/reddit` | reddit_mongodb | reddit |
| 11 | `/api/statistics` | statistics (package) | statistics |
| 12 | `/api/tags` | tags_mongodb | tags |
| 13 | `/api/trends` | trends_mongodb | trends |
| 14 | `/api/user-trends` | user_trends_mongodb | user_trends |
| 15 | `/api/unified` | unified_trends_mongodb | unified_trends |
| 16 | `/api/analytics/trends` | analytics_trends (package) | analytics_trends |
| 17 | `/api/trends/analysis` | trend_analysis_mongodb | trend_analysis |
| 18 | `/api/topics` | topic_explorer | topic_explorer |
| 19 | `/api/rag` | rag_concepts | rag |
| 20 | `/api/ontology` | tag_ontology (package) | ontology |
| 21 | `/api/ontology-graph` | ontology_graph | ontology_graph |
| 22 | `/api/concepts/suggestions` | concepts_suggestions_mongodb | suggestions |
| 23 | `/api/concepts/organization` | concept_organization | concept_organization |
| 24 | (own prefix) | system_stats (package) | — |
| 25 | (own prefix) | references | — |
| 26 | `/api/media-gallery` | media_gallery_mongodb | media |
| 27 | `/api/arxiv` | arxiv | arxiv |
| 28 | `/api/acl-anthology` | acl_anthology | acl-anthology |
| 29 | (own prefix) | acm_import | acm |
| 30 | `/api/papers` | direct_url_import | direct-url |
| 31 | (own prefix) | openreview_import | openreview |
| 32 | `/api/article-clustering` | article_clustering_mongodb | clustering |
| 33 | `/api/v2/articles` | article_import (package) | article-import |
| 34 | `/api/article-preview` | article_preview | article-preview |
| 35 | `/api/pdf` | pdf_export | pdf-export |
| 36 | `/api/tags/reorganize` | tag_reorganization (package) | tag-reorganization |
| 37 | (own prefix) | dblp_mongodb.router | dblp |
| 38 | (own prefix) | dblp_mongodb.papers_router | dblp |

### 1.2 Flags

- **Duplicate prefix:** `/api/papers` is shared by `papers` (package) and `direct_url_import` (#2 and #30). Route collisions possible.
- **Self-prefixed routers:** 6 routers define their own prefix internally (`system_stats`, `references`, `acm_import`, `openreview_import`, `dblp_mongodb` x2), making the routing invisible from `main.py` alone.
- **Only versioned path:** `/api/v2/articles` (article_import). No other endpoints are versioned.
- **Concept/tag overlap:** Tags managed via `/api/tags`, concepts via `/api/concepts/suggestions`, `/api/concepts/organization`, and per-resource routes (`/api/papers/{id}/concepts`, `/api/tweets/{id}/concepts`). At least 4 distinct surfaces for the same domain concept.

---

## 2. Request Validation

**Pydantic coverage:** ~53 `BaseModel` classes exist across 17 files, but only ~40 are used as endpoint parameters. The remaining 303 endpoints accept raw `Query` params, `Dict[str, Any]` bodies, or no validation at all.

### Top Findings

| Endpoint | File:Line | Issue | Impact |
|----------|-----------|-------|--------|
| `POST /api/papers/{id}/tags` | `papers/concepts.py:76` | Accepts `body: Dict[str, Any]` — no schema, no field validation | Caller can send anything; no OpenAPI docs for body |
| `POST /api/papers/{id}/analyses/generate` | `papers/analysis_generation.py:175` | `data: Dict[str, Any] = Body(...)` — requires `analysis_type` but no schema enforces it | Missing field gives runtime KeyError, not 422 |
| `POST /api/papers/{id}/analyses/generate-multiple` | `papers/analysis_generation.py:206` | Same `Dict[str, Any]` pattern | No validation on `analysis_types` array |
| `PUT /api/papers/{id}/metadata` | `papers/metadata.py:65` | `metadata: Dict[str, Any]` | Any field writable; no allow-list |
| `POST /api/reddit/{id}/tags` | `reddit_mongodb.py:301` | `tag_data: Dict[str, Any] = Body(...)` | No field constraints |
| `POST /api/ontology/concepts` | `tag_ontology/concepts_ontology.py:21` | `concept_data: Dict[str, Any]` | Concept creation with zero schema |
| `POST /api/books/{id}/concepts` | `books/concepts.py:25` | `concept_data: Dict[str, Any] = Body(...)` | Same pattern |
| `POST /api/papers/{id}/apply-affiliations` | `papers/affiliations.py:168` | `affiliations_data: Dict[str, Any]` | Complex nested structure unvalidated |

**Recommendation:** Replace all `Dict[str, Any]` body parameters with typed Pydantic models. This is the single highest-impact improvement for API contract quality.

---

## 3. Response Contracts

### 3.1 response_model Coverage

Only **18 out of 343 endpoints** (5%) declare a `response_model`. Files with any coverage: `reddit_mongodb.py` (1), `llm_preferences.py` (4), `twitter_accounts/crud.py` (4), `article_import/url_import.py` (2), `authors_management.py` (2), `entity_extraction.py` (1), `tweets/__init__.py` (1), `tweets/browse.py` (1), `articles/browse.py` (1), `arxiv.py` (1).

### 3.2 Competing Envelope Patterns

At least 3 distinct response shapes are used:

**Pattern A — Flat result with metadata:**
```json
{"posts": [...], "pagination": {"page": 1, "total_pages": 5}}
```
Used by: `reddit_mongodb.py:205`, `articles/browse.py`, `tweets/browse.py`

**Pattern B — Success wrapper:**
```json
{"success": true, "analysis_type": "...", "content": "..."}
```
Used by: `papers/analysis_generation.py:191`

**Pattern C — Error-in-200:**
```json
{"question": "...", "answer": "The search index is empty.", "needs_rebuild": true}
```
Used by: `rag_concepts.py:98-104` — returns HTTP 200 with an error condition buried in the body.

### 3.3 Missing Status Codes

| Situation | Expected | Actual | Example |
|-----------|----------|--------|---------|
| Resource created (upload) | 201 Created | 200 OK | `papers/crud.py:390` — `POST /upload` returns 200 |
| Async task started | 202 Accepted | 200 OK | `papers/analysis_generation.py:174` — analysis generation returns 200 immediately |
| Resource deleted | 204 No Content | 200 OK | `papers/concepts.py:54` — DELETE returns `{"message": "..."}` |

Only **1 endpoint** in the entire API uses a non-200 success code: `papers/content.py:236` returns `204`.

---

## 4. Error Handling

### 4.1 No Global Exception Handler

`main.py` has no `@app.exception_handler` registration. Unhandled exceptions produce FastAPI's default 500 response, which includes the Python traceback in development mode.

### 4.2 Internal Exception Leaks

**155 occurrences of `str(e)`** across 47 files are passed directly to callers via:
- `raise HTTPException(status_code=500, detail=str(e))` — 70+ instances
- `return {"error": str(e)}` — 30+ instances (error-in-200 pattern)
- `return {"success": False, "error": str(e)}` — 15+ instances

Example from `papers/crud.py:454`:
```python
raise HTTPException(status_code=500, detail=f"Error uploading paper: {str(e)}")
```
This can leak: file system paths, MongoDB connection strings, ObjectId internals, or Python tracebacks.

### 4.3 Inconsistent Error Keys

Three different keys are used for error messages in JSON responses:

| Key | Example File | Example Value |
|-----|-------------|---------------|
| `"error"` | `rag_concepts.py:63` | `{"error": str(e)}` |
| `"detail"` | `papers/concepts.py:28` | HTTPException `detail` field |
| `"message"` | `direct_url_import.py:249` | `{"message": str(e)}` |

A consumer cannot reliably determine where to find the error message.

---

## 5. Authentication & Authorization

### 5.1 Evidence of Zero Auth

- `main.py:124-130`: CORS middleware is the only security-adjacent configuration. `allow_origins` is a list of localhost ports; `allow_methods=["*"]`, `allow_headers=["*"]`.
- No `Depends()` with auth middleware appears anywhere in the codebase.
- No API key, Bearer token, session, or OAuth2 flow.

### 5.2 Unprotected Destructive Endpoints (sample)

| Endpoint | Risk |
|----------|------|
| `DELETE /api/papers/{id}` | Permanently deletes paper and all data |
| `POST /api/rag/rebuild` | Rebuilds entire search index (CPU-intensive) |
| `POST /api/tags/reorganize/start` | Triggers LLM-powered bulk reorganization |
| `DELETE /api/ontology/concepts/{id}` | Deletes concept from hierarchy |
| `POST /api/tags/update-concept-links` | Bulk-modifies tag-concept links |
| `DELETE /api/twitter-accounts/{id}` | Removes tracked Twitter account |

---

## 6. Pagination & Limits

### 6.1 Two Competing Patterns

**Pattern 1: `skip` / `limit` (offset-based)**
Used by: `reddit_mongodb.py:30-31`, `tweets/browse.py:28`
```python
limit: int = Query(50, ge=1, le=500)
skip: int = Query(0, ge=0)
```

**Pattern 2: `page` / `page_size` (page-based)**
Used by: `reddit_mongodb.py:147-148`, `papers/crud.py:175`, `books/crud.py:45`, `articles/browse.py:31`, `tweets/browse.py:85`, `media_gallery_mongodb.py:20`, `authors_management.py:64`, `articles/content.py:251`
```python
page: int = Query(1, ge=1)
page_size: int = Query(20, ge=1, le=100)
```

### 6.2 Both Patterns in Same File

`reddit_mongodb.py` uses **both** patterns:
- `GET /api/reddit/` (line 30): `skip` + `limit` (default limit=50, max=500)
- `GET /api/reddit/faceted-search` (line 147): `page` + `page_size` (default page_size=20, max=100)

`tweets/browse.py` also uses both:
- Line 28: `skip` + `limit`
- Line 85: `page` + `page_size`

### 6.3 Inconsistent Defaults and Maximums

| Endpoint | Default | Maximum |
|----------|---------|---------|
| `GET /api/reddit/` | limit=50 | 500 |
| `GET /api/reddit/faceted-search` | page_size=20 | 100 |
| `GET /api/papers/` | page_size=20 | 100 |
| `GET /api/tweets/` | limit=100 | (no max) |
| `GET /api/articles/` | page_size=20 | 100 |

---

## 7. Documentation & OpenAPI

### 7.1 Docstring Coverage

779 docstring delimiters (`"""`) across 97 API files. With 343 endpoints plus module docstrings, estimated ~40% of endpoints have a docstring. Most are one-liners without parameter or return documentation.

### 7.2 Missing Parameter Descriptions

Most `Query()` parameters lack `description`. Example from `tweets/browse.py`:
```python
skip: int = Query(0, ge=0)  # No description
limit: int = Query(100)      # No ge/le constraints, no description
```

Contrast with better-documented endpoints like `reddit_mongodb.py:30-40` which include descriptions for every parameter.

### 7.3 No Error Response Schemas

No endpoint declares `responses={404: {...}, 500: {...}}` in its decorator. The OpenAPI spec shows only the happy-path response (usually untyped `200 OK`).

---

## 8. Naming & Versioning

### 8.1 Mixed Naming Conventions

| Pattern | Examples |
|---------|----------|
| Kebab-case | `/api/twitter-accounts`, `/api/media-gallery`, `/api/acl-anthology`, `/api/user-trends` |
| Flat/lowercase | `/api/ontology`, `/api/tags`, `/api/reddit`, `/api/rag` |
| Slash-nested | `/api/analytics/trends`, `/api/concepts/suggestions` |
| Camelish compound | `/api/article-clustering`, `/api/article-preview` |

### 8.2 Singular vs. Plural Inconsistency

| Singular | Plural |
|----------|--------|
| `/api/rag` | `/api/papers` |
| `/api/ontology` | `/api/tweets` |
| `/api/pdf` | `/api/articles` |

### 8.3 No Versioning Strategy

- Only one versioned path exists: `/api/v2/articles` (article_import package).
- All other endpoints are unversioned.
- No deprecation headers or sunset dates on any endpoint.

---

## 9. Consumer Perspective Test

### Test 1: `GET /api/papers/` — Complex Query

| Criterion | Result | Notes |
|-----------|--------|-------|
| Parameters documented in OpenAPI? | PARTIAL | `page`, `page_size` have `ge` constraints but sparse descriptions |
| Response shape predictable? | PARTIAL | Returns `{"papers": [...], "pagination": {...}}` but no `response_model` |
| Error on bad input? | PASS | `page=-1` returns 422 (FastAPI validation) |
| Pagination consistent? | PASS | Uses `page`/`page_size` pattern |
| **Verdict** | **PARTIAL** | |

### Test 2: `POST /api/rag/ask` — Pydantic Model

| Criterion | Result | Notes |
|-----------|--------|-------|
| Request validated? | PASS | `RAGQuery` model enforces `question: str` |
| Response shape predictable? | FAIL | Returns error-in-200 when index empty (line 98-104) |
| Error on missing field? | PASS | Missing `question` returns 422 |
| Internal errors hidden? | FAIL | Line 125: `raise HTTPException(status_code=500, detail=str(e))` |
| **Verdict** | **PARTIAL** | |

### Test 3: `POST /api/tags/tweet/{tweet_id}` — Mutation

| Criterion | Result | Notes |
|-----------|--------|-------|
| Request validated? | PASS | `TagCreate` model with `tag: str` |
| 404 on missing tweet? | PASS | Line 52-53 checks tweet existence |
| Response shape documented? | FAIL | No `response_model`; returns ad-hoc dict with nested `concept` object |
| Consistent error format? | PARTIAL | Uses HTTPException `detail` but also prints to stdout (line 84) |
| **Verdict** | **PARTIAL** | |

### Test 4: `GET /api/reddit/faceted-search` — Pagination

| Criterion | Result | Notes |
|-----------|--------|-------|
| Pagination parameters? | PASS | `page`/`page_size` with constraints |
| Consistent with `GET /api/reddit/`? | FAIL | Parent endpoint uses `skip`/`limit` — different pattern |
| Response includes pagination metadata? | PASS | Returns `pagination` object |
| Total count accurate? | PASS | Count query matches filter |
| **Verdict** | **FAIL** | Pagination inconsistency within same resource |

### Test 5: `POST /api/papers/{id}/analyses/generate` — Async

| Criterion | Result | Notes |
|-----------|--------|-------|
| Request validated? | FAIL | `Dict[str, Any]` body — no schema |
| Returns 202 for async? | FAIL | Returns 200 with result (line 191) |
| Error handling? | FAIL | Line 199-203: catches all exceptions, returns `{"success": false, "error": str(e)}` as 200 |
| Status code on error? | FAIL | Error conditions return 200, not 4xx/5xx |
| **Verdict** | **FAIL** | |

### Summary: 0 PASS, 3 PARTIAL, 2 FAIL

---

## Appendix A: Top 30 Contract Violations

Priority levels: **BREAKING** (would cause consumer failures), **CONFUSING** (inconsistent behavior), **MINOR** (cosmetic/docs).

| # | Priority | Endpoint / Area | Description | Consumer Impact | Recommendation |
|---|----------|----------------|-------------|----------------|----------------|
| 1 | BREAKING | All 343 endpoints | Zero authentication | Any network-adjacent caller can read/write/delete all data | Add API key or session auth |
| 2 | BREAKING | 47 files (155 occurrences) | `str(e)` leaks internal exceptions | Exposes file paths, ObjectIds, stack traces | Global exception handler + opaque error messages |
| 3 | BREAKING | `POST .../analyses/generate` | Error returns 200 `{"success": false}` | Consumer must check body for errors, not status code | Return proper 4xx/5xx status codes |
| 4 | BREAKING | `POST /api/rag/ask` | Empty index returns 200 with error message | Consumer cannot distinguish success from failure by status code | Return 503 or 422 |
| 5 | BREAKING | `GET /api/rag/stats` | Error returns 200 `{"error": str(e)}` | Same error-in-200 pattern | Use HTTPException |
| 6 | BREAKING | `GET /api/rag/health` | Error returns 200 `{"status": "error", "error": str(e)}` | Health check never fails at HTTP level | Return 503 |
| 7 | CONFUSING | `papers/concepts.py:76` | `body: Dict[str, Any]` — no schema for tag body | No OpenAPI docs; any field accepted | Create `TagAddRequest` model |
| 8 | CONFUSING | 17 endpoints | `data: Dict[str, Any] = Body(...)` pattern | No field documentation or validation | Replace with typed Pydantic models |
| 9 | CONFUSING | `reddit_mongodb.py` | Two pagination patterns in same file | Consumer must learn different params per endpoint | Standardize on `page`/`page_size` |
| 10 | CONFUSING | `tweets/browse.py` | Same dual-pagination within one module | Same issue | Standardize |
| 11 | CONFUSING | Error responses | 3 different error keys: `error`, `detail`, `message` | Consumer guesses which key to read | Standardize on `detail` (FastAPI convention) |
| 12 | CONFUSING | `papers/crud.py:390` | `POST /upload` returns 200, not 201 | Consumer can't distinguish "found existing" from "created new" | Return 201 Created |
| 13 | CONFUSING | `papers/concepts.py:54` | `DELETE` returns 200 with body, not 204 | Inconsistent with REST conventions | Return 204 No Content |
| 14 | CONFUSING | `/api/papers` prefix | Shared by `papers` package AND `direct_url_import` | Route collision risk; confusing OpenAPI grouping | Give `direct_url_import` its own prefix |
| 15 | CONFUSING | Concept/tag surfaces | 4+ distinct API surfaces for managing concepts/tags | Consumer unsure which endpoint to use | Consolidate under `/api/concepts` |
| 16 | CONFUSING | `/api/v2/articles` | Only versioned path; implies v1 exists (it doesn't in that form) | Suggests a versioning scheme that doesn't exist | Remove `v2` or version all paths |
| 17 | CONFUSING | `tags_mongodb.py:84` | `print()` used for error logging | Inconsistent with `logger` used elsewhere | Use `logger.error()` |
| 18 | CONFUSING | `papers/analysis_generation.py:218` | Bare `except:` (no exception type) | Silently catches everything including KeyboardInterrupt | Catch `Exception` |
| 19 | MINOR | 338 endpoints (95%) | No `response_model` declared | OpenAPI spec shows no response schema | Add response models |
| 20 | MINOR | ~60% of endpoints | No `description` on Query parameters | OpenAPI docs lack field explanations | Add descriptions |
| 21 | MINOR | `tweets/browse.py` | `limit: int = Query(100)` — no `le` constraint | Consumer can request unlimited results | Add `le=500` or similar |
| 22 | MINOR | 0 endpoints | No `responses={}` error schemas in decorator | OpenAPI shows only happy-path | Add error response schemas |
| 23 | MINOR | Naming | Mixed kebab-case, flat, nested prefixes | No discoverability pattern | Adopt consistent kebab-case |
| 24 | MINOR | Naming | Singular vs plural inconsistency (`/rag` vs `/papers`) | Minor confusion | Standardize on plural nouns for collections |
| 25 | MINOR | Self-prefixed routers | 6 routers define own prefix, invisible from `main.py` | Harder to audit routing | Define all prefixes in `main.py` |
| 26 | MINOR | `reddit_mongodb.py:88,103` | Bare `except:` clauses | Swallows all errors silently | Catch specific exceptions |
| 27 | MINOR | `papers/analysis_generation.py` | In-memory `analysis_tasks` dict for async status | Lost on restart; no persistence | Use MongoDB for task state |
| 28 | MINOR | No rate limiting | Any caller can trigger N index rebuilds | CPU/memory exhaustion | Add rate limiting on expensive endpoints |
| 29 | MINOR | `papers/concepts.py:87-92` | `remove_tag_from_paper` is a stub — always returns success | Consumer thinks tag was removed | Implement or remove endpoint |
| 30 | MINOR | `rag_concepts.py:211` | Bug: `content_type` variable in loop scope leaks | All concepts get last loop's content_type | Fix variable scoping |

---

## Appendix B: Methodology

### Scoring Formula

```
health_score = sum(weight_i * score_i for each area) / 10 * 100
```

Each area scored 0-10:
- **0:** Feature completely absent
- **1-3:** Present but fundamentally broken or inconsistent
- **4-6:** Partially implemented with significant gaps
- **7-9:** Well implemented with minor issues
- **10:** Exemplary

### Data Collection

- **Endpoint count:** `grep -c '@router\.(get|post|put|patch|delete)'` across all `.py` files in `backend/app/api/` = 343
- **str(e) count:** `grep -c 'str(e)'` across same directory = 155 in 47 files
- **response_model count:** `grep -c 'response_model'` = 18 in 10 files
- **Pydantic model count:** `grep 'class \w+(BaseModel)'` = 53 classes in 17 files
- **Router registrations:** Manual count from `main.py:132-170` = 38

### Sampling Approach

Consumer perspective tests selected to cover:
1. Read-heavy endpoint with query complexity (papers list)
2. Endpoint with Pydantic validation (RAG ask)
3. Mutation endpoint (tag creation)
4. Pagination edge case (Reddit — both patterns in one file)
5. Async operation (analysis generation)

### Scope Exclusions

- Frontend code not audited
- Service layer (`backend/app/services/`) not audited for contract purposes
- Performance/latency not measured
- WebSocket endpoints not found (none exist)
