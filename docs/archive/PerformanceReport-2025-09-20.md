# PerformanceReport-2025-09-20

## Überblick
- Fokus auf offensichtliche Engpässe in MongoDB-basierten APIs und Hilfsdiensten.
- Bewertung anhand vorhandener Implementierungen ohne Micro-Optimierungen.
- Quick Wins priorisieren, anschließend mittel-/langfristige Maßnahmen nennen.

## Hotspots & Empfehlungen

| Problem | Ursache | Empfehlung | Aufwand | Nutzen |
|---------|---------|------------|---------|--------|
| N+1-Abfragen in `get_papers` (`backend/app/api/papers_mongodb.py:323ff`) | Für jede Seite werden pro Paper individuelle `tag_instances`- und Konzept-Lookups ausgeführt. | Aggregation umbauen: `db.tag_instances` per `$match` + `$group` für alle Paper der Seite und Konzepte via `$lookup` oder einmaligem `find` laden. | Mittel | Signifikante Reduktion der DB-Roundtrips bei größeren Seiten, bessere Latenz. |
| Blockierende Downloads in `import_paper_from_url` (`backend/app/api/direct_url_import.py:103ff`) | `requests.get(..., stream=True)` läuft im FastAPI-Thread; bei langsamen Quellen blockiert der Worker. | Download in `asyncio.to_thread` auslagern oder zu `httpx.AsyncClient` wechseln und Chunk-Verarbeitung beibehalten. | Mittel | Stabilere Latenz & besserer Durchsatz bei parallelen Imports. |
| Umfangreiche Abfragen in `trend_analysis_mongodb` & `trends_mongodb` | Mehrere `distinct`/`aggregate`-Pipelines auf ungefilterten Collections ohne Indizes. | Index-Check (`created_at`, `concept_ids`, `content_type`) und ggf. zusammengesetzte Indizes ergänzen. | Mittel | Schnellere Trendberechnungen und geringere CPU-Auslastung. |
| Mehrfaches Laden großer Collections bei Statistikendpunkten (`statistics_mongodb.py`, `system_statistics.py`) | `count_documents` & `distinct` auf gesamte Collections pro Request. | Caching-Schicht (Redis/In-Memory) oder periodisches Pre-Aggregat per Background Task. | Hoch | Klar bessere Antwortzeiten für Dashboards, geringere DB-Last. |
| `VectorStore` Neubau (`backend/app/services/vector_store_mongodb.py`) | `build_from_mongodb` iteriert Konzepte sequentiell, ruft OpenAI-Embeddings je Konzept einzeln auf. | Batch-Verarbeitung (z.B. 50er Gruppen) & parallele Requests (Rate-Limits beachten), Zwischenspeicherung nur geänderter Konzepte (Change Tracking). | Hoch | Massiv kürzere Rebuild-Zeiten, weniger API-Kosten. |

## Quick Wins (konkret)
1. **Paper-Listing aggregieren** – Beispiel:
   ```python
   pipeline = [
       {"$match": query},
       {"$lookup": {
           "from": "tag_instances",
           "let": {"paperId": {"$toString": "$_id"}},
           "pipeline": [
               {"$match": {"$expr": {"$eq": ["$content_id", "$$paperId"]}}},
               {"$group": {"_id": "$concept_id"}}
           ],
           "as": "concept_refs"
       }}
   ]
   papers = list(db.papers.aggregate(pipeline))
   ```
   → reduziert `find`-Aufrufe auf zwei pro Request.
2. **Async Download beim Direct Import** – `await asyncio.to_thread(download_pdf, ...)` oder kompletter Wechsel auf `httpx.AsyncClient` inkl. Timeout-/Retry-Konfiguration.

## Langfristige Schritte
- **Indizierung offensiver beobachten**: regelmäßiger Index-Report (z.B. `system_statistics`) und automatisierte Alerts bei Collection-Growth.
- **Materialisierte Views für Statistiken**: Background-Worker, der Aggregationen (Top-Konzept-Trends, Counts) minütlich aktualisiert.
- **Streaming/Pipeline für VectorStore**: Event-gesteuerte Aktualisierung statt kompletter Neubau.

## Ressourcen & Parallelität
- MongoDB-Operationen feingliedrig für Bulk-Szenarien planen (Bulk Writes für Backfills/Reorganisation).
- Worker-Konfiguration von FastAPI/Uvicorn prüfen: bei blockierenden Tasks (PDF-Verarbeitung) separate Worker (Celery/BackgroundTasks) nutzen.

## Fazit
Mit Aggregations-Umbau und Async-I/O lassen sich kurzfristig deutliche Verbesserungen erzielen. Mittel- bis langfristig sollten Caching und materialisierte Aggregationen vorgesehen werden, um Trend-/Statistik-Endpunkte skalierbar zu halten.
