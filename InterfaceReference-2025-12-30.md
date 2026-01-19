# SmartTrendTracer API Interface Reference

**Version**: 2.0.0 (MongoDB Edition)
**Datum**: 2025-12-30
**Typ**: REST API (FastAPI)
**Base URL**: `http://localhost:8000`

---

## 1. Überblick

SmartTrendTracer ist ein AI-gestütztes Content-Monitoring-System für:
- **Twitter/X**: Tracking von AI-bezogenen Accounts
- **Substack**: Newsletter-Sammlung und -Analyse
- **Research Papers**: PDF-Verarbeitung mit Marker/MinerU
- **Books**: PDF/EPUB-Bibliotheksverwaltung
- **Reddit**: Subreddit-Monitoring (r/LLM, r/MachineLearning, etc.)

### Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                  │
│                    http://localhost:3000                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────┐
│                  Backend (FastAPI + Uvicorn)                │
│                    http://localhost:8000                    │
├─────────────────────────────────────────────────────────────┤
│  PDF Services:                                              │
│  - Marker Service (Port 8002)                               │
│  - MinerU Service (Port 8003)                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                 MongoDB (localhost:27017)                   │
│                 Database: smarttrendtracer                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Quickstart

### Backend starten

```bash
cd backend
./start_stt.sh
# Oder manuell:
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### API-Gesundheitscheck

```bash
# Mit curl
curl http://localhost:8000/health

# Mit HTTPie
http GET localhost:8000/health
```

**Erwartete Antwort**:
```json
{"status": "healthy", "database": "connected"}
```

### Erster API-Aufruf

```bash
# Tweets abrufen
curl "http://localhost:8000/api/tweets/?page=1&page_size=10"

# Mit HTTPie
http GET localhost:8000/api/tweets/ page==1 page_size==10
```

---

## 3. Konfiguration

### Umgebungsvariablen (`~/.env`)

| Variable | Beschreibung | Erforderlich |
|----------|--------------|--------------|
| `OPENAI_API_KEY` | OpenAI API-Schlüssel | Ja |
| `ANTHROPIC_API_KEY` | Claude API-Schlüssel | Ja |
| `GOOGLE_API_KEY` | Gemini API-Schlüssel | Ja |
| `XAI_API_KEY` | Grok API-Schlüssel | Optional |
| `MONGODB_URL` | MongoDB URI (Standard: `mongodb://localhost:27017/`) | Optional |

### LLM-Konfiguration (`backend/llm.json`)

```json
{
  "models": {
    "tag_suggestion": {
      "model": "gemini-3-flash-preview",
      "temperature": 0.3,
      "max_tokens": 1000
    },
    "articleSummarization": {
      "model": "claude-sonnet-4-20250514",
      "temperature": 0.5,
      "max_tokens": 4000
    }
  }
}
```

### LiteLLM Router (`backend/litellm_config.yaml`)

Konfiguriert Fallback-Chains und Load-Balancing für 60+ Modelle.

---

## 4. API-Referenz

### 4.1 Tweets API (`/api/tweets`)

#### GET `/api/tweets/`
Tweets mit Filterung und Paginierung abrufen.

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|----------|--------------|
| `page` | int | 1 | Seitennummer (≥1) |
| `page_size` | int | 50 | Einträge pro Seite (1-200) |
| `authors` | List[str] | - | Filter nach Autoren-Usernamen |
| `concept_ids` | List[str] | - | Filter nach Concept-IDs |
| `search` | str | - | Volltextsuche |

**Beispiel**:
```bash
curl "http://localhost:8000/api/tweets/faceted-search?page=1&page_size=20&authors=karpathy"
```

**Response** (200 OK):
```json
{
  "tweets": [
    {
      "id": "1234567890",
      "text": "Tweet-Inhalt...",
      "author_username": "karpathy",
      "created_at": "2025-12-30T10:00:00Z",
      "metrics": {"likes": 1500, "retweets": 200},
      "concepts": [
        {"concept_id": "abc123", "display_name": "Machine Learning", "slug": "machine-learning"}
      ]
    }
  ],
  "facets": {
    "authors": [{"username": "karpathy", "count": 45}],
    "concepts": [{"concept_id": "abc123", "display_name": "ML", "count": 30}]
  },
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

#### POST `/api/tweets/{tweet_id}/concepts`
Concept zu Tweet hinzufügen.

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `text` | Query[str] | Concept-Name |

```bash
curl -X POST "http://localhost:8000/api/tweets/123456/concepts?text=Machine%20Learning"
```

#### DELETE `/api/tweets/{tweet_id}/concepts/{concept_id}`
Concept von Tweet entfernen.

```bash
curl -X DELETE "http://localhost:8000/api/tweets/123456/concepts/abc123"
```

---

### 4.2 Papers API (`/api/papers`)

#### GET `/api/papers/`
Forschungspapiere mit Facetten abrufen.

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|----------|--------------|
| `page` | int | 1 | Seitennummer |
| `page_size` | int | 50 | Einträge pro Seite |
| `concept_ids` | List[str] | - | Filter nach Concepts |
| `years` | List[int] | - | Filter nach Publikationsjahren |
| `processors` | List[str] | - | Filter nach PDF-Prozessor |
| `search` | str | - | Volltextsuche |

**Beispiel**:
```bash
curl "http://localhost:8000/api/papers/?page=1&years=2025&search=transformer"
```

#### POST `/api/papers/{paper_id}/process`
PDF-Verarbeitung starten (Hintergrundprozess).

| Body-Parameter | Typ | Beschreibung |
|----------------|-----|--------------|
| `preferred_processor` | str | "marker", "mineru", "auto" |

```bash
curl -X POST "http://localhost:8000/api/papers/abc123/process" \
  -H "Content-Type: application/json" \
  -d '{"preferred_processor": "marker"}'
```

**Response** (202 Accepted):
```json
{
  "status": "processing",
  "message": "PDF processing started with marker",
  "paper_id": "abc123"
}
```

#### GET `/api/papers/{paper_id}/processing-status`
Verarbeitungsstatus abfragen.

```bash
curl "http://localhost:8000/api/papers/abc123/processing-status"
```

**Response**:
```json
{
  "status": "processing",
  "progress": 45,
  "message": "Recognizing Text: 45% 99/220",
  "elapsed_seconds": 120
}
```

#### POST `/api/papers/{paper_id}/tags/suggest`
KI-Tag-Vorschläge generieren.

```bash
curl -X POST "http://localhost:8000/api/papers/abc123/tags/suggest" \
  -H "Content-Type: application/json" \
  -d '{"model": "gemini-3-flash-preview"}'
```

**Response**:
```json
{
  "existing_suggestions": [
    {"display_name": "Transformer", "concept_id": "xyz789", "score": 0.92}
  ],
  "new_suggestions": [
    {"display_name": "Attention Mechanism", "score": 0.85}
  ],
  "already_tagged": ["Machine Learning"],
  "model_used": "gemini-3-flash-preview"
}
```

---

### 4.3 Articles API (`/api/articles`)

#### GET `/api/articles/faceted-search`
Substack-Artikel mit Facetten durchsuchen.

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `authors` | List[str] | Autorennamen |
| `concept_ids` | List[str] | Concept-Filter |
| `search` | str | Volltextsuche |
| `has_summary` | bool | Filter: hat AI-Zusammenfassung |

```bash
curl "http://localhost:8000/api/articles/faceted-search?authors=Sebastian%20Raschka&has_summary=true"
```

#### POST `/api/articles/{article_id}/summarize`
AI-Zusammenfassung generieren.

```bash
curl -X POST "http://localhost:8000/api/articles/abc123/summarize" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-4-20250514"}'
```

---

### 4.4 RAG Search API (`/api/rag`)

#### POST `/api/rag/ask`
Semantische Suche mit KI-Antwort.

| Body-Parameter | Typ | Standard | Beschreibung |
|----------------|-----|----------|--------------|
| `question` | str | - | Suchanfrage (erforderlich) |
| `content_types` | List[str] | alle | "tweet", "article", "paper" |
| `k` | int | 10 | Anzahl Dokumente (für Trends: 50) |

**Beispiel mit curl**:
```bash
curl -X POST "http://localhost:8000/api/rag/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key trends in LLM research?",
    "content_types": ["paper", "tweet"],
    "k": 50
  }'
```

**Beispiel mit Python**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/rag/ask",
    json={
        "question": "What are the key trends in LLM research?",
        "content_types": ["paper", "tweet"],
        "k": 50
    }
)
print(response.json()["answer"])
```

**Response**:
```json
{
  "answer": "# Top Trending Topics in LLM Research\n\n1. **Reasoning Models**...",
  "sources": [
    {"type": "paper", "id": "abc123", "title": "DeepSeek R1", "score": 0.95}
  ],
  "is_trend_analysis": true,
  "documents_analyzed": 50
}
```

#### GET `/api/rag/stats`
Index-Statistiken abrufen.

```bash
curl "http://localhost:8000/api/rag/stats"
```

**Response**:
```json
{
  "total_documents": 1740,
  "index_size_mb": 45.2,
  "last_updated": "2025-12-30T08:00:00Z"
}
```

#### POST `/api/rag/rebuild`
RAG-Index neu aufbauen.

```bash
curl -X POST "http://localhost:8000/api/rag/rebuild"
```

---

### 4.5 Analytics API (`/api/analytics/trends`)

#### POST `/api/analytics/trends/summarize`
KI-generierte Zusammenfassung mit Filtern.

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|----------|--------------|
| `period` | str | "7days" | today, 3days, week, 30days, 60days, 90days, 365days, all |
| `author` | str | - | Twitter-Autor-Filter (nur Tweets!) |
| `tags` | List[str] | [] | Concept-Filter |
| `model` | str | - | LLM-Modell |
| `include_tweets` | bool | true | Tweets einschließen |
| `include_articles` | bool | true | Artikel einschließen |
| `include_papers` | bool | true | Papers einschließen |
| `max_tweets` | int | 100 | Max Tweets (10-500) |
| `max_articles` | int | 50 | Max Artikel (5-200) |
| `max_papers` | int | 50 | Max Papers (5-200) |

**Wichtig**: Wenn `author` gesetzt ist, werden nur Tweets gefiltert (Articles/Papers werden automatisch ausgeschlossen).

```bash
curl -X POST "http://localhost:8000/api/analytics/trends/summarize?period=30days&author=karpathy&model=gemini-3-flash-preview&max_tweets=200"
```

**Response**:
```json
{
  "summary": "## AI Research Analysis Report...",
  "stats": {
    "tweet_count": 45,
    "article_count": 0,
    "paper_count": 0,
    "unique_authors": 1,
    "time_range": {
      "start": "2025-11-30T00:00:00Z",
      "end": "2025-12-30T00:00:00Z"
    }
  },
  "filters": {
    "period": "30days",
    "author": "karpathy",
    "tags": []
  },
  "model_used": "gemini-3-flash-preview"
}
```

---

### 4.6 Ontology API (`/api/ontology`)

#### GET `/api/ontology/tree`
Vollständige Concept-Hierarchie abrufen.

```bash
curl "http://localhost:8000/api/ontology/tree"
```

#### POST `/api/ontology/concept`
Neues Concept erstellen.

```bash
curl -X POST "http://localhost:8000/api/ontology/concept" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Reinforcement Learning",
    "slug": "reinforcement-learning",
    "parent_id": "abc123",
    "description": "Learning from rewards"
  }'
```

#### GET `/api/ontology/search?q={query}`
Concepts suchen.

```bash
curl "http://localhost:8000/api/ontology/search?q=machine%20learning"
```

---

### 4.7 Books API (`/api/books`)

#### POST `/api/books/upload`
Buch hochladen (PDF/EPUB).

```bash
curl -X POST "http://localhost:8000/api/books/upload" \
  -F "file=@/path/to/book.pdf" \
  -F "title=Deep Learning" \
  -F "authors=Ian Goodfellow" \
  -F "genre=Textbook"
```

#### POST `/api/books/{book_id}/process`
Buchverarbeitung starten (Hintergrund, bis 6 Stunden).

```bash
curl -X POST "http://localhost:8000/api/books/abc123/process?preferred_processor=marker"
```

---

## 5. Beispiele

### 5.1 Vollständiger Workflow: Tweet-Analyse

```bash
#!/bin/bash
# 1. Tweets eines Autors abrufen
tweets=$(curl -s "http://localhost:8000/api/tweets/faceted-search?authors=karpathy&page_size=50")
echo "Gefundene Tweets: $(echo $tweets | jq '.total')"

# 2. AI-Zusammenfassung generieren
summary=$(curl -s -X POST \
  "http://localhost:8000/api/analytics/trends/summarize?period=30days&author=karpathy&model=gemini-3-flash-preview")
echo "$summary" | jq '.summary'

# 3. Concept zu einem Tweet hinzufügen
tweet_id=$(echo $tweets | jq -r '.tweets[0].id')
curl -X POST "http://localhost:8000/api/tweets/${tweet_id}/concepts?text=Neural%20Networks"
```

### 5.2 Python: Paper-Verarbeitung

```python
import requests
import time

BASE_URL = "http://localhost:8000"

def process_paper(paper_id: str, processor: str = "marker"):
    """Paper verarbeiten und auf Abschluss warten."""

    # 1. Verarbeitung starten
    resp = requests.post(
        f"{BASE_URL}/api/papers/{paper_id}/process",
        json={"preferred_processor": processor}
    )
    resp.raise_for_status()
    print(f"Verarbeitung gestartet: {resp.json()}")

    # 2. Status pollen
    while True:
        status = requests.get(
            f"{BASE_URL}/api/papers/{paper_id}/processing-status"
        ).json()

        print(f"Status: {status.get('message', 'Unknown')} ({status.get('progress', 0)}%)")

        if status.get("status") == "completed":
            print("Verarbeitung abgeschlossen!")
            break
        elif status.get("status") == "failed":
            raise Exception(f"Verarbeitung fehlgeschlagen: {status.get('error')}")

        time.sleep(10)

    # 3. Tag-Vorschläge abrufen
    suggestions = requests.post(
        f"{BASE_URL}/api/papers/{paper_id}/tags/suggest",
        json={"model": "gemini-3-flash-preview"}
    ).json()

    return suggestions

# Verwendung
if __name__ == "__main__":
    result = process_paper("6789abcdef012345", "marker")
    print(f"Vorgeschlagene Tags: {result['existing_suggestions']}")
```

### 5.3 HTTPie: RAG-Suche

```bash
# Trend-Analyse
http POST localhost:8000/api/rag/ask \
  question="What are the trending topics in AI?" \
  content_types:='["tweet", "paper"]' \
  k:=50

# Normale Frage
http POST localhost:8000/api/rag/ask \
  question="How does transformer attention work?" \
  k:=10
```

---

## 6. Fehlerbehandlung

### HTTP-Statuscodes

| Code | Bedeutung | Typische Ursache |
|------|-----------|------------------|
| 200 | OK | Erfolgreiche Anfrage |
| 201 | Created | Ressource erstellt |
| 202 | Accepted | Hintergrundverarbeitung gestartet |
| 400 | Bad Request | Ungültige Parameter |
| 404 | Not Found | Ressource nicht gefunden |
| 422 | Unprocessable Entity | Validierungsfehler |
| 429 | Too Many Requests | Rate-Limit erreicht |
| 500 | Internal Server Error | Server-Fehler |
| 503 | Service Unavailable | LLM-API nicht erreichbar |

### Fehler-Response-Format

```json
{
  "detail": "Article not found",
  "status_code": 404,
  "error_type": "NotFoundError"
}
```

### Beispiel: Fehlerbehandlung in Python

```python
import requests
from requests.exceptions import HTTPError

def safe_api_call(url: str, method: str = "GET", **kwargs):
    try:
        resp = requests.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except HTTPError as e:
        if e.response.status_code == 404:
            print(f"Ressource nicht gefunden: {url}")
        elif e.response.status_code == 429:
            print("Rate-Limit erreicht, bitte warten...")
        elif e.response.status_code >= 500:
            print(f"Server-Fehler: {e.response.text}")
        raise
    except requests.ConnectionError:
        print("Backend nicht erreichbar. Läuft der Server?")
        raise
```

---

## 7. Versionierung

### API-Version
- **Aktuell**: v2.0.0 (MongoDB Edition)
- **Legacy**: v1.x (SQLite) - nicht mehr unterstützt

### Breaking Changes in v2.0.0
- Alle Daten in MongoDB statt SQLite
- `tag` → `concept` Umbenennung
- Neue Poly-Hierarchie für Concepts
- Geänderte ID-Formate (MongoDB ObjectId statt int)

### Deprecation Policy
- Deprecated Endpoints: 6 Monate Vorlauf
- Entfernte Endpoints: `/api/statistics/*` (alte SQLite-Version)

---

## 8. Konventionen

### URL-Struktur
```
/api/{resource}/{id?}/{action?}
```

### Benennungen
- **Ressourcen**: Plural, kebab-case (`/api/twitter-accounts`)
- **Parameter**: snake_case (`page_size`, `concept_id`)
- **Response-Felder**: snake_case

### Paginierung
- Standard: `page=1`, `page_size=50`
- Maximum: `page_size=200`
- Response enthält: `total`, `page`, `page_size`

### Datums-/Zeitformat
- **ISO 8601**: `2025-12-30T10:00:00Z`
- **Zeitzone**: UTC

### ID-Formate
- **MongoDB ObjectId**: 24-stelliger Hex-String (`"6789abcdef012345abcdef01"`)
- **Tweet-ID**: String (Twitter-ID)

---

## 9. Glossar

| Begriff | Beschreibung |
|---------|--------------|
| **Concept** | Hierarchischer Tag im Ontologie-System |
| **Tag Instance** | Verknüpfung zwischen Concept und Content |
| **Facet** | Filterbare Dimension (Autor, Jahr, Concept) |
| **RAG** | Retrieval-Augmented Generation - semantische Suche mit LLM |
| **Marker** | PDF-zu-Markdown-Konverter (primärer Prozessor) |
| **MinerU** | Alternativer PDF-Prozessor |
| **Poly-Hierarchie** | Concepts können mehrere Eltern haben |
| **LiteLLM** | Router für mehrere LLM-Anbieter |
| **FAISS** | Vector-Datenbank für semantische Suche |

---

## 10. Änderungsverlauf

| Datum | Version | Änderungen |
|-------|---------|------------|
| 2025-12-30 | 2.0.5 | Author-Filter jetzt Twitter-only (schließt Articles/Papers aus) |
| 2025-12-30 | 2.0.4 | Dynamische Autor-Liste in Summarization |
| 2025-12-30 | 2.0.3 | Expandable Summary für Articles |
| 2025-12-30 | 2.0.2 | Summary/has_summary in faceted-search |
| 2025-12-26 | 2.0.1 | Topic Explorer Mouse-Click-Fix |
| 2025-12-25 | 2.0.0 | Gemini 3 Model-Fix, LiteLLM API-Key Loading |
| 2025-12-24 | 1.9.0 | Cross-Platform Fixes (macOS ↔ Linux) |
| 2025-11-23 | 1.8.0 | Marker Progress Tracking |
| 2025-09-16 | 1.7.0 | Book Management System |
| 2025-09-05 | 1.6.0 | Reddit Integration |
| 2025-08-22 | 1.5.0 | MongoDB Tag Ontology Migration |
| 2025-01-24 | 1.0.0 | Vollständige MongoDB-Migration |

---

## Sequenzdiagramm: Paper-Verarbeitung

```
┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
│  Client  │         │  FastAPI │         │  Marker  │         │  MongoDB │
└────┬─────┘         └────┬─────┘         └────┬─────┘         └────┬─────┘
     │                    │                    │                    │
     │ POST /papers/{id}/process               │                    │
     │───────────────────>│                    │                    │
     │                    │                    │                    │
     │                    │  Start Background Task                  │
     │                    │───────────────────>│                    │
     │                    │                    │                    │
     │ 202 Accepted       │                    │                    │
     │<───────────────────│                    │                    │
     │                    │                    │                    │
     │                    │                    │  Progress Updates  │
     │                    │<───────────────────│                    │
     │                    │                    │                    │
     │                    │  Save Progress     │                    │
     │                    │────────────────────────────────────────>│
     │                    │                    │                    │
     │ GET /papers/{id}/processing-status      │                    │
     │───────────────────>│                    │                    │
     │                    │  Query Status      │                    │
     │                    │────────────────────────────────────────>│
     │                    │                    │                    │
     │ {"status": "processing", "progress": 45}│                    │
     │<───────────────────│                    │                    │
     │                    │                    │                    │
     │     ... (polling) ...                   │                    │
     │                    │                    │                    │
     │                    │  Completed         │                    │
     │                    │<───────────────────│                    │
     │                    │                    │                    │
     │                    │  Save Content      │                    │
     │                    │────────────────────────────────────────>│
     │                    │                    │                    │
     │ {"status": "completed", "progress": 100}│                    │
     │<───────────────────│                    │                    │
     │                    │                    │                    │
```

---

## Annahmen und offene Punkte

> **[ANNAHME]** Rate-Limiting ist derzeit nicht implementiert. Bei hoher Last können 429-Fehler auftreten.

> **[ANNAHME]** Authentifizierung ist nicht aktiviert. Alle Endpoints sind öffentlich zugänglich.

> **[TODO]** WebSocket-Support für Echtzeit-Updates bei Paper-Verarbeitung.

> **[TODO]** GraphQL-Alternative zur REST-API.

---

*Generiert am 2025-12-30 | SmartTrendTracer v2.0.5*
