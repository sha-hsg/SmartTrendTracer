# InterfaceReference-2025-09-20

> **Hinweis:** Die folgenden Informationen basieren auf dem aktuellen SmartTrendTracer-Backend (FastAPI) sowie den vorhandenen Dienstskripten. Wo nicht eindeutig dokumentiert, sind Annahmen als solche markiert.

---

## Überblick
SmartTrendTracer stellt eine FastAPI-basierte HTTP-API bereit, die Inhalte (Tweets, Papers, Articles etc.) aus MongoDB bedient und verknüpft. Zusätzlich existieren CLI-Skripte in `backend/` für Wartungsaufgaben (z. B. Tag-Backfill, Collector).

- **API-Basis-URL (Annahme):** `http://localhost:8000/api`
- **CLI-Einstiegspunkt:** Python-Skripte unter `backend/`, meist via `backend/venv/bin/python SCRIPT.py`.

```
             ┌──────────┐        HTTP(S)        ┌──────────────┐
 Nutzer/App ▶│ Frontend │◁─────────────────────▶│ FastAPI-API │
             └──────────┘                        │ (backend/app│
                                                 │   /main.py) │
                                                 └─────▲───────┘
                                                       │
                                                      MongoDB
```

---

## Quickstart

### API
1. **Backend starten** (Annahme):
   ```bash
   backend/venv/bin/uvicorn app.main:app --reload --port 8000
   ```
2. **OpenAPI-Dokumentation:** `http://localhost:8000/docs`
3. **Health-Check:** `GET http://localhost:8000/api/system/statistics/overview`

### CLI
- Beispiel: Tag-Backfill ausführen
  ```bash
  cd backend
  venv/bin/python backfill_tag_instances_concepts.py
  ```

---

## Konfiguration

| Variable | Zweck | Standard (Annahme) |
|----------|-------|--------------------|
| `MONGODB_URI` | MongoDB-Verbindungsstring | `mongodb://localhost:27017/` |
| `MONGODB_DB` | Datenbankname | `smarttrendtracer` |
| `MONGODB_REPLICA_SET` | Optionaler Replica-Set-Name | _leer_ |
| `MONGODB_APP_NAME` | MongoDB App-Name | _leer_ |
| `OPENAI_API_KEY` | Embedding-Generierung (`vector_store`) | _erforderlich für Rebuild_ |
| `REDDIT_CLIENT_ID`/`SECRET` | Reddit-Collector | _erforderlich für Collector_ |

Konfigurationsdateien:
- `backend/llm.json`: LLM-Modelle für Tag-Vorschläge (Annahme).
- `backend/prompts_config.json`: Prompt-Konfigurationen.

---

## API-Referenz

### `GET /api/tweets/`
- **Beschreibung:** Liste der Tweets mit optionalem Filter.
- **Parameter:**
  | Name | Typ | Beschreibung |
  |------|-----|--------------|
  | `limit` | int (1–500) | Anzahl Einträge (Standard 50) |
  | `skip` | int | Offset (Standard 0) |
  | `with_media_only` | bool | Nur Tweets mit Medien |
  | `concept_id` | str | Filter nach Konzept |
  | `include_concepts` | bool | Konzeptdetails anfügen |
- **Antwort:** `200 OK` – Liste von Tweet-Objekten.
- **Beispiel (HTTPie):**
  ```bash
  http GET :8000/api/tweets/ limit==5 with_media_only==true
  ```
- **curl:**
  ```bash
  curl -s "http://localhost:8000/api/tweets/?limit=5&with_media_only=true"
  ```

### `GET /api/papers/`
- **Beschreibung:** Paginierte Paper-Liste mit Filtern.
- **Parameter (Auszug):** `page`, `page_size`, `search`, `concept_ids`, `author`, `year`, `special_filter`, usw.
- **Antwort:**
  ```json
  {
    "papers": [ ... ],
    "total": 123,
    "page": 1,
    "page_size": 20,
    "total_pages": 7
  }
  ```
- **curl-Beispiel:**
  ```bash
  curl -s "http://localhost:8000/api/papers/?page=1&page_size=10&year=2025"
  ```

### `POST /api/direct-url-import/import-url`
- **Beschreibung:** Importiert ein Paper über eine PDF-URL.
- **Body:**
  ```json
  {
    "url": "https://example.org/paper.pdf",
    "title": "Example Paper",
    "authors": "Doe, Smith",
    "add_tags": ["LLM", "Benchmark"]
  }
  ```
- **Antwort:** `200 OK` – enthält `paper_id`, ggf. Hinweis auf bestehende Einträge.

### `GET /api/system/statistics/overview`
- **Beschreibung:** Zusammenfassung wichtiger Systemzahlen (gecached, 60 s TTL).

### Weitere relevante Endpunkte
| Pfad | Beschreibung |
|------|--------------|
| `/api/articles/` | Artikel-Listing mit Konzepten |
| `/api/references/` | Referenz-Verwaltung (Paper-Zitate) |
| `/api/trend-analysis/` | Trends und Statistiken über Konzepte |
| `/api/tags/` | Tagging-Endpunkte (Tweets etc.) |
| `/api/statistics/overview` | Detaillierte Statistiken (gecached) |

---

## CLI-Referenz

| Kommando | Beschreibung | Exit-Code |
|----------|--------------|-----------|
| `venv/bin/python backfill_tag_instances_concepts.py` | Backfill für `tag_instances` → verknüpft alte Tags mit Konzepten. | `0` bei Erfolg, `>0` bei Fehler |
| `venv/bin/python collect_tweets.py` (Annahme) | Twitter-Collector (setzt API Keys voraus). | `0` oder Fehlercode |
| `venv/bin/python rebuild_rag_index.py` (Annahme) | Rebuilds RAG/Vector-Index. | `0` oder Fehlercode |

**Beispiel (erfolgreicher Backfill):**
```bash
cd backend
venv/bin/python backfill_tag_instances_concepts.py
# Ausgabe: "Backfill complete. Total examined=0, updated=0, concepts_created=0"
# Exit-Code $? == 0
```

---

## Beispiele

### API – Konzeptisierte Paper-Liste (Python)
```python
import requests

BASE = "http://localhost:8000/api"
params = {"page": 1, "page_size": 5, "concept_ids": ["663b..."], "include_concepts": True}
response = requests.get(f"{BASE}/papers/", params=params)
response.raise_for_status()
for paper in response.json()["papers"]:
    print(paper["title"], paper["concepts"])
```

### CLI – Trend-Statistik caching demonstrieren
```bash
http GET :8000/api/system/statistics/overview
http GET :8000/api/system/statistics/overview  # < 60s später → cached
```

---

## Fehlerbehandlung

| Szenario | Antwort | Beschreibung |
|----------|---------|--------------|
| Ungültiger Import-URL (`POST /direct-url-import`) | `400 Bad Request` | Download-Fehler oder kein PDF |
| Ressource nicht gefunden (z. B. `GET /papers/{id}`) | `404 Not Found` | Paper existiert nicht |
| Validierungsfehler | `422 Unprocessable Entity` | Query-/Body-Parameter fehlerhaft |
| Serverfehler | `500 Internal Server Error` | Unerwartete Ausnahme |

Fehler werden typischerweise als JSON mit `detail`-Feld zurückgegeben.

---

## Versionierung
- API-Version: **2.0.0** (siehe `app/main.py`).
- Kein explizites SemVer pro Endpoint dokumentiert (Annahme). Breaking Changes sollten via Changelog im Repo kommuniziert werden.

---

## Konventionen
- JSON Responses, snake_case Keys, ISO8601-Zeiten.
- IDs aus MongoDB als Strings (`_id` → `id`).
- Query-Parameter klein geschrieben, boolsches `true/false`.
- Konzepte (Tags) werden durch `concept_id`, `display_name` identifiziert.

---

## Glossar
| Begriff | Beschreibung |
|---------|--------------|
| **Concept** | Normalisierter Tag/Entität in `tag_concepts_v2`. |
| **Tag Instance** | Verknüpfung zwischen Content (`content_type`, `content_id`) und Konzept. |
| **RAG** | Retrieval-Augmented Generation; Vector Store für Papers/Artikel. |
| **Direct URL Import** | Endpoint zum Abruf von PDFs über externe Links. |

---

## Änderungsverlauf
| Datum | Änderung |
|-------|---------|
| 2025-09-20 | Erstfassung dieser Referenz, Konsolidierung der FastAPI & CLI Oberfläche (Annahme). |

