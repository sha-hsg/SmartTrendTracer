# Funktionsinventur SmartTrendTracer

**Stand:** 2026-07-24 · **Methode:** Reine Analyse (keine Codeänderungen). 11 parallele Analysen über Backend-API (6 Bereiche), Services (3 Bereiche), Collectors/CLI-Skripte/Marker/MinerU und Frontend. Soll-Zustand abgeleitet aus CLAUDE.md, DEFECTS.md, Docstrings, Kommentaren und Commit-Messages. TOT-Prüfung per repo-weitem Grep (Endpunkte gegen frontend/src, Funktionen gegen backend/), teilweise ergänzt um Live-Verifikation gegen laufendes Backend (Port 8088) und MongoDB.

> ## ✅ FIX-STATUS (24.07.2026, gleicher Tag)
> Alle Befunde der Handlungsliste **P1, P2 und P3 wurden umgesetzt** (10 parallele Fix-Durchläufe + zentrale Verifikation):
> - **P1 komplett:** Router-Shadowing (books/facets, articles/authors, without-author → jetzt 200), Tag-Reorganizer-NameError, Paper-Tag-Lösch-Stub, Snippet-POST, ObjectId-Usage-Counts, ACL/OpenReview/ACM-Background-Processing, Media-Gallery (Sortierung/Filter/Suche), Topic-Explorer-Datumsfilter, Statistik-Dashboard-Fakes, RAG-Trend-Metadaten + concept_filter, Bubble-Chart-Tweets, Entity-Review-Persistenz, DEF-001, Frontend-Pfade auf reale Endpunkte.
> - **P2 komplett:** PERF-002-Textindizes aktiv (live verifiziert), Collect-Schema, apply-affiliations, Import-Schema-Drift (ACM/DBLP/JAIR/ACL/direct-url), Book-Worker in start_stt.sh/stop_stt.sh, echte Cancels, RAG-Skripte, rag/index_manager konfig-getrieben (llm.json `rag_embedding`, verhaltensgleich), LLM-Preference-Validierung (422) + veraltete Modelle (gpt-4o, gpt-4o-mini, grok-2-latest) aus allen Auswahllisten entfernt mit MODEL_MIGRATION_MAP, Reddit-Count/Regex-Fixes.
> - **P3 komplett:** ~60 tote Dateien (~12.000+ LOC) gelöscht (26 Service-Dateien + 2 Packages, 9 Collector-/Scheduler-Dateien, 18 Frontend-Dateien, diverse Skripte), ~90 tote Endpunkte entfernt, Footer-Cleaner konsolidiert, Doku (CLAUDE.md/DEFECTS.md) nachgezogen. Ausnahmen (bewusst behalten): Books PUT/DELETE, user-settings DELETE, Circuit-Breaker-Ops, authors_management-Endpunkte (geplante UI lt. AUTHOR_UI_DESIGN.md), „Coming Soon"-Views, POST /api/reddit/collect + /stats/collection.
> - **Zusätzlich gefixt (Funde während der Umsetzung):** kaputte relative Imports `..services` in papers/processing(_helpers).py, falscher Backend-Pfad-Fallback (parents[3]) 3×, vorbestehender KeyError-500 in GET /api/articles/, naive/aware-TypeError in anomaly_detection, AttributeError in bulk_ops (nicht existentes add_concept).
> - **Nicht umgesetzt (bewusst):** MinerU-Progress-Pipeline (Doku korrigiert statt Feature nachgebaut), DOI-Import (501, CrossRef geplant), Testsuite H-Q1 (eigenes Vorhaben).
> - **Verifikation:** compileall OK, `app.main` importiert (266 Routen), 27 Kern-Endpunkte per curl 200, 22 gelöschte Endpunkte 404, Textindizes in Live-DB vorhanden, Frontend-Build grün, tsc-Fehlerstand unverändert (18, vorbestehend).

## Bewertungsraster

| Status | Bedeutung |
|---|---|
| OK | Umsetzung entspricht der dokumentierten Absicht |
| UNVOLLSTÄNDIG | Kernpfad funktioniert; Randfälle, Fehlerbehandlung oder Validierung fehlen |
| FALSCH | Verhalten weicht von der dokumentierten Absicht ab |
| STUB | Platzhalter, hardcodierte Rückgabewerte, TODO, leerer Rumpf |
| TOT | Wird nirgends aufgerufen, keine Referenz im Projekt |
| FEHLT | Dokumentiert oder vom Frontend erwartet, aber nicht implementiert |

## Globale Feststellungen

1. **Keine automatisierte Testsuite.** Es existiert kein Test-Framework, keine test_*.py im Projektcode (einzige Ausnahme: das manuelle `backend/mineru_service/test_mineru_direct.py`), keine Frontend-Tests. Das Raster-Kriterium „sinnvoll getestet" ist damit projektweit nicht erfüllt; „OK" bedeutet in diesem Bericht „Implementierung entspricht der dokumentierten Absicht und wird real genutzt". Das Testdefizit selbst ist ein eigener Handlungspunkt (siehe Handlungsliste H-Q1).
2. **Große Mengen toter Code trotz Aufräum-Commit 49b0c53d.** ~137 tote Einträge, darunter ganze Service-Dateien (~4.500+ LOC), von denen mindestens 10 beim Import sofort crashen würden (SQLAlchemy-Relikte, fehlende Pakete, Syntaxfehler).
3. **Zwei systemische Bug-Muster:** (a) String-vs-ObjectId bei `tag_instances.concept_id`-Zählungen — alle Usage-Statistiken der Ontologie liefern immer 0 (live verifiziert); (b) Router-Registrierungsreihenfolge — drei aktiv vom Frontend aufgerufene Endpunkte werden von `/{id}`-Catch-all-Routen verschattet und liefern 404.
4. **Frontend-Backend-Drift nach Cleanups:** Mehrere aktiv geroutete UI-Komponenten (ConceptManagementCenter, TagOntologyModern, OrphanTagAssigner, OntologyAISuggestions) rufen Endpunkte, die in den Commits 49b0c53d/8d2a92fe gelöscht wurden.
5. **CLAUDE.md-Doku-Drift:** Mehrere als „COMPLETE" dokumentierte Features existieren nicht (MinerU-Progress-Pipeline) oder beschreiben veraltete Zustände (Substack-Endpoints, UnifiedTagService, spaCy-Fallback-Kette, DEF-002 „temporarily disabled", `tag`-Parameter der Tweets-API, Dashboard-Pfade `/api/trends/...`).

## Zusammenfassung: Anzahl je Status

Gezählt über ~360 bewertete Einträge (Endpunkte, öffentliche Funktionen/Klassen, CLI-Kommandos; Frontend auf Komponenten-Ebene). „Intention unklar" ist ein Sekundärlabel (in den Primärzahlen enthalten).

| Bereich | OK | UNVOLLST. | FALSCH | STUB | TOT | FEHLT |
|---|---|---|---|---|---|---|
| 1. Tweets/Twitter-Accounts/Media-API | 33 | 2 | 2 | 0 | 7 | 1 |
| 2. Papers-API/PDF-Export/References | 54 | 7 | 3 | 2 | 14 | 1 |
| 3. Books/Articles/Substack/Reddit-API | 40 | 9 | 3 | 1 | 13 | 1 |
| 4. Trends/Analytics/Statistics-API | 18 | 5 | 5 | 4 | 20 | 0 |
| 5. Tags/Ontologie/Konzepte/RAG-API | 22 | 15 | 9 | 1 | 23 | 6 |
| 6. Import-APIs/LLM-Preferences/main.py | 31 | 7 | 3 | 0 | 15 | 0 |
| 7. Services LLM/RAG/Embeddings | 8 | 3 | 3 | 0 | 5 | 1 |
| 8. Services Tags/Konzepte/Trends | 12 | 0 | 0 | 0 | 8 | 0 |
| 9. Services Paper/PDF/Import/Konverter | 19 | 0 | 1 | 2 | 12 | 0 |
| 10. Collectors/CLI-Skripte/Marker/MinerU | 14 | 3 | 3 | 1 | 5 | 1 |
| 11. Frontend (Komponenten-Ebene) | ~209 Dateien | 3 | 4 | 5 | 15 Dateien | 1 |
| **Summe (ohne Frontend-OK-Dateizählung)** | **251** | **54** | **36** | **16** | **137** | **12** |

Sekundärlabel „Intention unklar": ~14 Einträge (v. a. tote Trend-/User-Trends-/Visualisierungs-Endpunkte ohne dokumentierte Absicht).

## Priorisierte Handlungsliste (nach Risiko für den Nutzer)

### P1 — Nutzer sieht falsches Verhalten bei aktiv genutzten Features (Aufwand: überwiegend klein)

1. **Router-Shadowing → 404 trotz aktiver Frontend-Aufrufe:** `GET /api/books/facets` (books/__init__.py:22-24 — Books-Facetten im Dashboard komplett funktionslos), `GET /api/articles/authors`, `GET /api/articles/without-author` (articles/__init__.py:9-12). Fix: statische Routen vor Parameter-Routen registrieren. *klein*
2. **Tag-Reorganizer komplett tot:** `POST /api/tags/reorganize/start` crasht mit NameError `db` (tag_reorganization/routes.py:245) — jede persistente Reorganisation schlägt mit 500 fehl. *klein*
3. **Paper-Tag-Löschen ist ein Stub:** `DELETE /api/papers/{id}/tags/{tag}` (papers/concepts.py:133-138) meldet Erfolg ohne DB-Operation; wird aktiv aufgerufen (usePaperAnnotations.ts:126). *klein*
4. **Paper-Snippets nicht speicherbar:** `POST /api/papers/{id}/snippets` fehlt (Frontend usePaperActions.ts:103 → 405). *klein*
5. **Systemischer String-vs-ObjectId-Bug:** alle Ontologie-Usage-Statistiken liefern 0 (concepts.py:336-348, tools.py:121, ontology_graph.py:45/212/276, concept_organization.py:60). *klein, mehrere Stellen*
6. **PDF-Verarbeitung nach ACL-/OpenReview-Import schlägt seit jeher still fehl** (Default `process_pdf=True`): nicht existente Methoden `process_paper`/`analyze_paper` (acl_anthology.py:312/327) bzw. `process_pdf_async` (openreview_import.py:250-284). *klein–mittel*
7. **Media-Gallery:** „Most liked"/„Most retweeted" liefern Oldest-first, media_type-Filter nach Pagination, Suche/Tag-Filter serverseitig nicht implementiert (media_gallery_mongodb.py:18-71). *mittel*
8. **Topic Explorer:** `/correlation`-Datumsfilter wird nie angewandt, `/popular`-`days` wirkungslos, `/frequency` 500 ohne Datumsparameter (topic_explorer.py:225/353/77 — live verifiziert). *klein–mittel*
9. **Statistics-Dashboard zeigt erfundene/leere Werte:** growth_rate simuliert + trend hartkodiert „up" (system_stats/analytics.py:149-158), `with_marker`/`with_tags` immer 0 (overview_and_content.py:61ff), `summary.authors` immer leer (system_and_llm.py:334f). *klein–mittel*
10. **RAG-Trend-UI unsichtbar:** `/api/rag/ask` verwirft `is_trend_analysis`/`documents_analyzed`/`source_type` (rag_concepts.py:115-121); `concept_filter` ignoriert. *klein*
11. **Bubble-Chart-X-Achse ignoriert Tweets** (heatmap_bubble.py:184/190 — Twitter-String-IDs verworfen). *klein*
12. **Tweet-Tag-Suggestion unter /api/tags doppelt kaputt:** Template-KeyError liefert immer [] (tag_suggestion_service.py:73-77) + AttributeError im Vector-Store-Aufruf (tags_mongodb.py:162 vs. vector_store_mongodb.py:187), beide still geschluckt. *klein–mittel*
13. **Entity-Review persistiert nichts:** `POST /api/entities/review` baut Mock-Entities („for demonstration", entity_extraction.py:183-224), aktiv aus zwei Review-UIs aufgerufen; Paper-Pendant `bulk-action` taggt das Paper nicht (papers/bulk_ops.py:45-76). *mittel*
14. **DEF-001 Ursache identifiziert:** `articleViewerClosed`-Listener liegt nur in der toten Datei components/substack/FacetedSubstackDashboardModern.tsx:109; das live gerenderte articles-Dashboard hat keinen. *klein*
15. **Frontend ruft gelöschte Endpunkte:** ConceptManagementCenter (useConceptManagement.ts:72-206 → 404), TagOntologyModern IO/Synonym/AI-Suggestions (mehrere FEHLT-Gruppen). Frontend auf `/api/concepts/organization/*` bzw. `/alias` umbiegen oder Legacy-Views entfernen. *klein–mittel*

### P2 — Datenintegrität und stille Fehlschläge

16. **PERF-002-Volltextindizes werden nie angelegt:** startup_event legt konkurrierende Single-Field-Textindizes an (main.py:289-290); kombinierte Indizes scheitern still (Live-DB verifiziert). *klein*
17. **Manueller Tweet-Collect mit inkompatiblem Schema:** POST /api/twitter-accounts/{id}/collect schreibt ObjectId-`_id`+`tweet_id`-Feld → Duplikate, Einzeltweets unauffindbar; blockiert zudem den Event-Loop (twitter_accounts/collection.py:107-232). *mittel*
18. **apply-affiliations schreibt ins falsche Feld** (`authors` statt `authors_detailed`, papers/affiliations.py:222-230) — Institution-Facetten sehen Änderungen nie. *klein–mittel*
19. **Import-Schema-Drift:** ACM `authors_detailed` als String-Liste (acm_import.py:52), DBLP attach-metadata `authors` als Liste (dblp_mongodb.py:176-182), JAIR `published_date`-Roh-String (jair_import.py:103), ACL ohne `authors_detailed` + wirkungsloser Duplikat-Check (acl_anthology.py:99-164), direct_url_import-Tags ohne concept_id (direct_url_import.py:163-170). *je klein*
20. **Book-Processing-Queue ohne Konsument:** book_processing_worker.py wird von keinem Startskript gestartet → `/api/books/{id}/process`-Jobs bleiben liegen. *mittel*
21. **Kosmetische Cancels:** papers/cancel-processing stoppt Marker nicht (processing.py:140-161), reorganize/cancel greift in LLM-Phase nicht (routes.py:153). *mittel*
22. **RAG-Wartungsskripte defekt:** rebuild_rag_index.py NameError `db.close()` (Z.50), update_rag_index.py Port 8000 (=Honcho) + Rückgabewert-Bug, run.py Port 8000. *je klein*
23. **rag/index_manager:** hardcodierte Embedding-Modelle entgegen llm.json + Nullvektor bei API-Fehler korrumpiert Index still (index_manager.py:300-322). *mittel*
24. **LLM-Preferences ohne Modellvalidierung** (llm_preferences.py:261-267) und Altmodelle (gpt-4o, gpt-4o-mini, grok-2-latest) weiter in Auswahllisten (litellm_config.yaml:314-322/414-416, models.ts:178-198) — Konflikt mit der Regel „veraltete Modelle in keiner Auswahl" (unsicher, Entscheid nötig). *klein*
25. **Reddit:** faceted-search-Count ohne concept-Filter (reddit_mongodb.py:178-202), Regex-Injection in Filtern (49/53/76-77); Artikel-Endpunkte: fehlendes re.escape (articles/content.py:108), apply-concepts ohne concept_ids-Update (content_processing.py:312), DELETE-Artikel mit verwaisten tag_instances (browse.py:212-215). *je klein*

### P3 — Aufräumen (kein Nutzerrisiko, aber Wartungslast)

26. **Tote Services löschen (~4.500+ LOC):** langchain_llm_service, rag_helpers+rag_embedding_helpers, embeddings_service, spacy_tagger, mongodb_tag_service, tag_service_mongodb, unified_tag_service (nicht parsebar!), paper_tag_service, orphan_tag_assigner, slug_normalizer, trend_analysis/-Package+Shim, paper_service, paper_repository_service, paper_author_extraction_service, export_service, url_article_importer(+_auth), curl_parser, substack_auth_service, image_preserving_converter, playwright_converter_v2 (+ Entscheidung document_converter/+playwright_converter). *je klein*
27. **Tote Collector-Kette löschen (~600+596 LOC):** twitter_collector, twitter_collector_with_retweets, twscrape_collector + app/smart_startup_collector.py → background_tasks.py → scheduler.py (+ async_startup_collector, startup_collector); selective_gmail_collector archivieren. *klein*
28. **~90 tote Endpunkte** entfernen oder anbinden (Details in den Bereichs-Tabellen; markanteste Blöcke: 4 user-trends-Routen+impl ~680 LOC, statistics/-Paket 7/8 tot, Reddit 7 Routen, pdf_export 3 Routen, papers-Entities-Duplikate, authors_management-UI nie gebaut). *je klein*
29. **Tote Frontend-Dateien löschen (15):** components/substack/ (5, enthält den DEF-001-Listener!), ArticleViewerModern (top-level), TagReorganizer, Barrel-index.ts (3), useTagConcepts, useDraggable, OntologyGraphPage, types/tagConcept*.ts. *klein*
30. **Stub-Views entscheiden:** author-analytics, author-merge, reddit-trends, books-analysis („Coming Soon" in Navigation beworben), Paper-Viewer-Such-Tab, /api/analytics/trends/{sankey,radar,sparklines}, mineru /convert_advanced, references/batch-import. *klein (entfernen) bis groß (implementieren)*
31. **Doku nachziehen (CLAUDE.md):** Substack-Endpoints → /api/articles, UnifiedTagService historisch, spaCy-Fallback existiert nicht, MinerU-Progress nicht implementiert (oder implementieren, *mittel*), DEF-002 ist behoben, monitor_collection kein 5s-Loop, Trend-Dashboard-Pfade /api/analytics/trends, Proportional-Blending-Verweis auf rag/search.py. *klein*
32. **Duplikat-Drift `remove_substack_footer`** (2 divergierende Kopien) konsolidieren. *klein*

### Q — Querschnitt

- **H-Q1 Testsuite aufbauen:** Es gibt keinerlei automatisierte Tests. Empfehlung: pytest + httpx-TestClient für die ~30 aktiv genutzten Kern-Endpunkte (faceted-search je Content-Typ, Tagging-Roundtrip, Import-Flows, Batch-Annotation), dazu je ein Regressionstest pro P1-Fix. *groß, inkrementell*
- **H-Q2 Feature-Policy durchsetzen:** Mehrere Befunde (5 Tag-Services, 2 Trend-Implementierungen, manueller Collect-Endpoint, Entities-Duplikate, 2 Footer-Cleaner) sind genau die Parallel-Implementierungen, die die globale Regel verbietet.

---

# Bereichs-Berichte (Details und vollständige Tabellen)
## Bereich: Tweets-API, Twitter-Accounts-API, Media-Gallery (Backend)

**Vorbemerkung Soll-Zustand:** Dokumentierte Absicht aus Modul-Docstrings sowie CLAUDE.md ("Twitter Endpoints", "Tweet Filtering"). DEFECTS.md: DEF-003 (Media-URLs, "By Design"), DEF-008 (Rate Limiting). Alte Monolithen in Commit 49b0c53d entfernt; Packages sind Nachfolger.

### Tabelle

**Package `backend/app/api/tweets/` (Prefix `/api/tweets`)**

| Eintrag | Datei:Zeile | Status | Begründung (1 Satz) |
|---|---|---|---|
| GET `/` (get_tweets) | browse.py:25 | UNVOLLSTÄNDIG | Kernpfad ok, aber `with_media_only` matcht Tweets ohne media-Feld, DB-Fehler werden zu leerer Liste verschluckt, dokumentierter `tag`-Parameter existiert nicht mehr. |
| GET `/faceted-search` | browse.py:83 | OK | Haupt-Workhorse des Tweet-Dashboards; Anm.: tag_instances pro Tweet doppelt abgefragt (browse.py:166 + browse_helpers.py:200) — Ineffizienz. |
| GET `/hierarchy-facets` | browse.py:180 | OK | Genutzt (FacetedTweetsDashboardModern.tsx:165). |
| GET `/{tweet_id}` | browse.py:184 | OK | Genutzt; 404-Handling vorhanden. |
| GET `/stats/overview` | browse.py:235 | TOT | Keinerlei Referenz (repo-weiter Grep ohne Treffer); Nebenbefund: crasht falls `created_at` fehlt (browse.py:276). |
| POST `/{tweet_id}/concepts` | concepts.py:13 | OK | Genutzt via conceptService.ts:132. |
| DELETE `/{tweet_id}/concepts/{concept_id}` | concepts.py:50 | OK | Genutzt via conceptService.ts:157. |
| POST `/batch-annotate` | annotation.py:230 | OK | Genutzt (useBatchAnnotation.ts:232). |
| GET `/batch-annotate/{task_id}/status` | annotation.py:262 | OK | Genutzt; Tasks in-memory (utils.py:30), 404 nach Restart frontend-seitig behandelt (Commit 61cb4ca9). |
| POST `/batch-annotate-all` | annotation.py:292 | OK | Genutzt; String/ObjectId-Dualität korrekt (308-322), Concurrency 1-8. |
| POST `/batch-annotate/{task_id}/cancel` | annotation.py:356 | OK | Genutzt (useBatchAnnotation.ts:302). |
| `get_profile_images_for_usernames` | utils.py:36 | OK | Batch-Lookup mit TTL-Cache. |
| `generate_tag_suggestions_for_text` | annotation.py:32 | OK | Modell-Routing über llm_manager statt Hardcoding (67-72, gemäß CLAUDE.md-Regel). |
| `run_batch_annotation` | annotation.py:98 | OK | Sentinel-Schreiblogik nur bei echtem Leer-Ergebnis (166-180), Cancel/Progress thread-sicher. |
| browse_helpers (7 Funktionen) | browse_helpers.py:10-286 | OK | Alle genutzt; `apply_annotation_status_filter` lädt alle annotierten IDs in Speicher (Skalierungsrisiko, funktional korrekt). |

**Package `backend/app/api/twitter_accounts/` (Prefix `/api/twitter-accounts`)**

| Eintrag | Datei:Zeile | Status | Begründung (1 Satz) |
|---|---|---|---|
| GET `/` (list_accounts) | crud.py:18 | OK | Genutzt (TwitterAccountManager.tsx:78). |
| GET `/categories` | crud.py:45 | TOT | Keine Referenz. |
| GET `/lookup` | crud.py:52 | OK | Genutzt (TwitterAccountManager.tsx:144). |
| POST `/validate` | crud.py:74 | TOT | Keine Referenz; von POST `/` dupliziert. |
| GET `/{account_id}` | crud.py:118 | TOT | Kein Einzelabruf referenziert. |
| POST `/` (create_account) | crud.py:132 | OK | Genutzt; 409 bei Duplikat; Anm.: `print()` statt Logger (crud.py:174). |
| PUT `/{account_id}` | crud.py:200 | OK | Genutzt. |
| DELETE `/{account_id}` | crud.py:235 | OK | Genutzt; optionales Tweet-Löschen. |
| GET `/stats` | stats.py:17 | OK | Genutzt; Anm.: N+1-Queries pro Account (stats.py:36-51). |
| GET `/dashboard` | stats.py:142 | OK | Genutzt. |
| GET `/collection-history` | stats.py:296 | UNVOLLSTÄNDIG | Aggregiert nach `created_at` (Postzeitpunkt, stats.py:309) statt `collected_at` — unsicher ob beabsichtigt; `/usage` nutzt korrekt `collected_at` (549). |
| GET `/collector-status` | stats.py:357 | OK | pgrep-Check mit Timeout. |
| GET `/live-progress` | stats.py:481 | OK | Staleness-Erkennung implementiert. |
| GET `/usage` | stats.py:540 | OK | Monats-/Tagesbudget gegen 10k-Limit (CLAUDE.md "Basic Account Mode"). |
| POST `/bulk-toggle` | collection.py:13 | TOT | Keine Referenz; unübliche Signatur. |
| POST `/{account_id}/toggle` | collection.py:36 | OK | Genutzt. |
| POST `/{account_id}/refresh` | collection.py:61 | OK | Genutzt. |
| POST `/{account_id}/collect` | collection.py:107 | FALSCH | Schreibt Tweets mit abweichendem Schema (ObjectId-`_id` + `tweet_id`-Feld) statt `_id`=Twitter-ID wie Collector → Duplikate + nicht abrufbare Einzeltweets; Docstring behauptet Background, Implementierung blockierend-synchron. |
| `serialize_account`, Create/Update/Response-Models | models.py:65/17/27/36 | OK | Verwendet. |
| `TwitterAccountBase` | models.py:7 | TOT | Nirgends referenziert. |
| `TwitterLookupResponse` | models.py:58 | TOT | Nirgends referenziert; `/lookup` gibt untypisiertes Dict zurück. |

**Datei `backend/app/api/media_gallery_mongodb.py` (Prefix `/api/media-gallery`)**

| Eintrag | Datei:Zeile | Status | Begründung (1 Satz) |
|---|---|---|---|
| GET `/gallery` | media_gallery_mongodb.py:18 | FALSCH | Sortierungen "likes_desc"/"retweets_desc" des Frontends liefern faktisch Oldest-first; `media_type`-Filter erst nach Pagination; `search`/`tag` werden ignoriert. |
| Media-Suche/Tag-Filter (FE-Feature) | MediaFilterBar.tsx:63, TwitterMediaGalleryModern.tsx:68-69 | FEHLT | UI sendet `search`/`tag` an `/gallery`, Backend definiert diese Parameter nicht (19-26). |
| GET `/stats` | media_gallery_mongodb.py:105 | OK | Aggregationen korrekt. |
| GET `/authors` | media_gallery_mongodb.py:173 | OK | Genutzt. |
| GET `/types` | media_gallery_mongodb.py:206 | OK | Genutzt. |
| GET `/tweet/{tweet_id}/media` | media_gallery_mongodb.py:232 | TOT | Keine Referenz. |

### Details (alles nicht-OK) — Kernpunkte

**1. GET /api/tweets/ — UNVOLLSTÄNDIG**: `query['media'] = {'$ne': []}` (browse.py:60) matcht auch Docs ohne media-Feld (media_gallery macht `$exists: True` korrekt vor); DB-Fehler → leere Liste (65-67); CLAUDE.md-dokumentierter `tag`-Param existiert nicht (Doku-Drift, unsicher). Korrektur: `$exists`+`$ne`, Fehler propagieren, Doku aktualisieren. Aufwand: klein.

**2. GET /stats/overview — TOT** (browse.py:235): implementiert, nirgends referenziert; `isoformat()`-Crash-Risiko (276). Entfernen oder anbinden. Aufwand: klein.

**3-5. twitter-accounts TOT**: `/categories` (crud.py:45), `/validate` (crud.py:74), GET `/{account_id}` (crud.py:118), `/bulk-toggle` (collection.py:13) — keine Aufrufer. Entfernen. Aufwand: je klein.

**6. /collection-history — UNVOLLSTÄNDIG** (stats.py:296): aggregiert `created_at` statt `collected_at`, Docstring verspricht "collection history"; Nachimporte unsichtbar. unsicher: evtl. gewollt. Aufwand: klein.

**7. POST /{account_id}/collect — FALSCH** (collection.py:107): (a) synchron trotz "background"-Docstring, blockiert Event-Loop (tweepy in async def, 165-179); (b) Insert ohne `_id`, Duplikat-Check via `tweet_id`-Feld (205) findet Collector-Tweets nie → Duplikate; Einzeltweets via GET /api/tweets/{id} nicht auffindbar; (c) Feld-Abweichungen (`entities` roh, `is_retweet`-Bool). Parallel-Implementierung entgegen Feature-Policy. Korrektur: Collector-Speicherfunktion wiederverwenden + BackgroundTasks. Aufwand: mittel.

**8. Models TOT** (models.py:7, 58): löschen oder `/lookup` typisieren. Aufwand: klein.

**9. GET /media-gallery/gallery — FALSCH** (18): (a) `sort_order = DESCENDING if sort_by == "date_desc" else ASCENDING` (42) → `likes_desc`/`retweets_desc` werden zu created_at ASC → "Most liked" zeigt älteste Tweets; (b) engagement-Zweig sortiert `metrics.likes`/`metrics.retweets`, Schema heißt `like_count`/`retweet_count`; (c) media_type-Filter nach Pagination (51-71) → leere/untervolle Seiten, `total` falsch (95); (d) `search`/`tag` fehlen. Korrektur: sort-Werte serverseitig unterstützen, Filter in Mongo-Query, Parameter implementieren. Aufwand: mittel.

**10. GET /tweet/{tweet_id}/media — TOT** (232): entfernen oder anbinden. Aufwand: klein.

### Statuszählung
(45 Einträge: 22 Endpunkte + 22 Funktionen/Klassen + 1 FE-Feature)
**OK: 33, UNVOLLSTÄNDIG: 2, FALSCH: 2, STUB: 0, TOT: 7, FEHLT: 1, Intention unklar: 0** (2 Teilbefunde "unsicher")

Auffälligster Befund: Der manuelle Collect-Endpunkt (collection.py:107) ist eine Parallel-Implementierung des Collectors mit inkompatiblem Tweet-Schema.
## Bereich: Papers-API & Export/References

Mounting: `papers.router` → `/api/papers` (main.py:174), `direct_url_import.router` → `/api/papers` (main.py:202), `pdf_export.router` → `/api/pdf` (main.py:208), `references.router` → `/api/references` (references.py:14, main.py:197). Router-Reihenfolge (statisch vor `/{paper_id}`) korrekt in `papers/__init__.py:42-57`.

### Tabelle

| Eintrag | Datei:Zeile | Status | Begründung (1 Satz) |
|---|---|---|---|
| GET `/api/papers/` | papers/crud.py:175 | OK | Filter/Sort/Pagination inkl. `paper_type` (Review Mode). |
| GET `/api/papers/{id}` | papers/crud.py:284 | UNVOLLSTÄNDIG | CLAUDE.md nennt `paper_type`-Param auch für Single-Paper; fehlt (Review-Felder werden zurückgegeben, 356-360) — unsicher ob relevant. |
| DELETE `/api/papers/{id}` | papers/crud.py:364 | OK | Löscht Paper + tag_instances konsistent. |
| POST `/api/papers/upload` | papers/crud.py:399 | OK | Upload mit `paper_type` wie dokumentiert. |
| Helpers crud.py | papers/crud.py:43,124 | OK | Batch-Konzeptauflösung, keine N+1. |
| PUT `/{id}/content` | papers/metadata.py:29 | UNVOLLSTÄNDIG | `modified_count==0` → HTTP 500 auch bei identischem Inhalt (54-55); `updated_at` als ISO-String statt BSON-Datetime (45). |
| PUT `/{id}/metadata` | papers/metadata.py:64 | UNVOLLSTÄNDIG | Schreibt `flagged`/`rating` (97,103-105), System liest `is_flagged`/`user_rating` (crud.py:166-167) — wirkungslose Pfade. |
| POST `/{id}/flag` | papers/metadata.py:187 | OK | Korrekt `is_flagged`. |
| PATCH `/{id}/rating` | papers/metadata.py:218 | OK | `user_rating` setzen/löschen. |
| PATCH `/{id}` | papers/metadata.py:252 | OK | Nur import_url/import_source (bewusst). |
| GET `/facets` | papers/facets.py:51 | OK | Dokumentierte Fixes (`$nin`, Array/String-Autoren, missing_data) implementiert (facet_helpers.py:41-49). |
| GET `/stats/overview` | papers/facets.py:293 | OK | `paper_type`-Filter (295-299). |
| facet_helpers.py (11 Builder) | papers/facet_helpers.py:18-290 | OK | Alle genutzt. |
| query_builder.py (7 Builder) | papers/query_builder.py:20-120 | OK | Alle genutzt, inkl. `build_paper_type_filter`. |
| GET `/{id}/content` | papers/processing.py:36 | OK | Genutzt. |
| POST `/{id}/process-with-marker` | papers/processing.py:59 | OK | Async-Start, Semaphore. |
| POST `/{id}/cancel-processing` | papers/processing.py:140 | UNVOLLSTÄNDIG | Nur DB-Status-Flip; Background-Task prüft `cancelled` nie, überschreibt Status — Abbruch rein kosmetisch. |
| GET `/{id}/processing-status` | papers/processing.py:174 | OK | Progress/Stage wie dokumentiert. |
| GET `/{id}/process-health` | papers/processing.py:223 | OK | CPU/RAM aus `marker_process_health`. |
| POST `/{id}/process` | papers/processing.py:280 | OK | Genutzt. |
| POST `/{id}/process-with-entities` | papers/processing.py:346 | TOT | Keine Referenz; zudem defekt: `result['content']` (417,451,466) existiert lt. eigenem Kommentar (385) nicht → KeyError. |
| POST `/{id}/progress-callback` | papers/processing.py:478 | OK | Von Marker/MinerU-Services aufgerufen. |
| POST `/{id}/process-with-mineru` | papers/processing.py:523 | OK | Genutzt. |
| processing_helpers (marker/mineru background) | papers/processing_helpers.py:19,233 | OK | BACKEND_PORT-Callback wie dokumentiert; Bild-URL-Rewrite (282). |
| GET `/{id}/analyses/task/{task_id}` | papers/analysis.py:25 | TOT | Kein Frontend-Aufruf; Async-Flow ungenutzt. |
| GET `/{id}/analyses/available` | papers/analysis.py:33 | OK | Dynamisch aus prompts_config.json. |
| GET `/{id}/analyses/saved` | papers/analysis.py:81 | OK | Genutzt. |
| POST `/{id}/analyses` | papers/analysis.py:124 | OK | Atomarer `$pull`+`$push`-Fix (284-298) wie dokumentiert. |
| POST `/{id}/analyses/generate` | papers/analysis_generation.py:177 | OK | Frontend nutzt ihn sequenziell (4 Dateien). |
| POST `/{id}/analyses/generate-multiple` | papers/analysis_generation.py:208 | TOT | Frontend auf sequenziell umgestellt (CLAUDE.md 4.1.26), 0 Treffer; Bug: `"\\n\\n"` erzeugt literale `\n` im Prompt (270,289). |
| POST `/{id}/analyses/async` | papers/analysis_generation.py:331 | TOT | 0 Treffer; Task-Status nur in-memory. |
| `run_analysis_in_background` | papers/analysis_generation.py:24 | TOT | Nur vom toten `/analyses/async` referenziert. |
| POST `/{id}/analyses/free` | papers/analysis_management.py:42 | OK | Genutzt; Hinweis: nicht-atomarer `$set` auf `free_analyses` (154-157). |
| GET/PUT/DELETE `/{id}/analyses/free[/{aid}]` | papers/analysis_management.py:164,184,218 | OK | Alle drei genutzt. |
| PUT `/{id}/analyses/generated/{type}` | papers/analysis_management.py:246 | OK | Genutzt. |
| DELETE `/{id}/analyses` | papers/analysis_management.py:298 | OK | Genutzt. |
| DELETE `/{id}/analyses/{type}` | papers/analysis_management.py:313 | OK | Atomarer `$pull`. |
| POST `/{id}/extract-entities` | papers/entities.py:19 | TOT | 0 Referenzen; abgelöst von `/{id}/entities/extract`. |
| POST `/{id}/entities/extract` | papers/entities.py:106 | OK | Genutzt; Content-Pflicht wie dokumentiert. |
| GET `/entities/schema` (unter /api/papers) | papers/entities.py:215 | TOT | Frontend ruft `/api/entities/schema` — Duplikat unreferenziert. |
| POST `/entities/extract` (Text, unter /api/papers) | papers/entities.py:262 | TOT | Duplikat von `/api/entities/extract`. |
| POST `/entities/review` (unter /api/papers) | papers/entities.py:403 | TOT | Duplikat; zudem Stub: accept/reject persistieren nichts (TODO 419). |
| GET `/{id}/tags/suggestions` | papers/tag_suggestions.py:16 | TOT | Als Route ungenutzt; nur interne Implementierung des POST-Wrappers (237). |
| POST `/{id}/tags/suggest` | papers/tag_suggestions.py:231 | FALSCH | Dokumentierte 400 „must be processed first" — HTTPException (90) liegt im try und wird von `except Exception` (219-223) geschluckt → 200 mit leeren Vorschlägen statt 400. |
| POST `/{id}/extract-affiliations` | papers/affiliations.py:19 | OK | LLM per Konfig; Makel: `model_used` gibt Config-Dict zurück (158). |
| PUT `/{id}/apply-affiliations` | papers/affiliations.py:167 | FALSCH | Schreibt Dict-Liste in `authors` (222-230) statt `authors_detailed` — verletzt dokumentiertes Schema; Institution-Facetten lesen `authors_detailed.affiliation` (facets.py:142) und sehen die Änderung nie. |
| POST `/{id}/entities/bulk-action` | papers/bulk_ops.py:17 | UNVOLLSTÄNDIG | `accept_all` legt Konzepte an, taggt das Paper aber nicht; `reject_all` No-op mit TODO (76); Parent-ID `c_et_*` (42) unverifiziert. |
| POST `/{id}/apply-concepts` | papers/concepts.py:23 | OK | Genutzt. |
| POST `/{id}/concepts` | papers/concepts.py:66 | OK | `slug` in Response (DEFECTS.md Resolved). |
| DELETE `/{id}/concepts/{cid}` | papers/concepts.py:100 | OK | Genutzt. |
| POST `/{id}/tags` | papers/concepts.py:121 | OK | Legacy-Wrapper delegiert; genutzt (usePaperAnnotations.ts:81). |
| DELETE `/{id}/tags/{tag}` | papers/concepts.py:133 | STUB | Selbstdeklarierter Stub (136-137), gibt immer Erfolg zurück ohne zu löschen — und wird aktiv aufgerufen (usePaperAnnotations.ts:126): Tag-Entfernen scheitert stillschweigend. |
| GET `/{id}/snippets` | papers/content.py:29 | OK | Genutzt. |
| POST `/{id}/snippets` | — (fehlt) | FEHLT | Frontend postet (usePaperActions.ts:103), Backend hat nur GET → 405; Artikel-Pendant existiert (articles/content.py:137). |
| GET/PUT `/{id}/sections[/{sid}]` | papers/content.py:58,87 | OK | Titel-Nummern-Bereinigung wie dokumentiert. |
| GET `/{id}/references` | papers/content.py:131 | OK | Genutzt. |
| GET `/{id}/tei` | papers/content.py:164 | OK | Fallback-Kette; genutzt. |
| GET `/{id}/pdf` | papers/content.py:273 | OK | Genutzt. |
| POST `/{id}/extract-sections` | papers/content.py:310 | OK | Prompt/Model aus Konfig. |
| GET `/{id}/images/{path}` | papers/content_media.py:23 | OK | Von generierten Bild-URLs referenziert; Hinweis: Converted-ID-Fallback O(n)-Scan (64-70). |
| POST `/{id}/grobid/process` | papers/grobid.py:28 | OK | Genutzt; Makel: `authors_detailed` kann String-Liste werden (90). |
| GET `/{id}/grobid/metadata` | papers/grobid.py:125 | OK | Genutzt. |
| utils.py | papers/utils.py:66-140 | OK | Überall genutzt. |
| POST `/api/papers/import-url` | direct_url_import.py:69 | UNVOLLSTÄNDIG | Import OK, aber `add_tags` schreibt tag_instances nur mit `tag`-Feld ohne `concept_id` (163-170) → unsichtbare Orphans. |
| GET `/api/papers/validate-url` | direct_url_import.py:199 | OK | Genutzt; Hinweis: blockierender requests.head in async (223). |
| GET `/api/pdf/article/{id}` | pdf_export.py:22 | OK | Genutzt. |
| POST `/api/pdf/articles/bulk` | pdf_export.py:64 | TOT | 0 Referenzen. |
| GET `/api/pdf/author/{id}` | pdf_export.py:99 | TOT | 0 Referenzen. |
| GET `/api/pdf/recent` | pdf_export.py:140 | TOT | 0 Referenzen. |
| GET `/api/pdf/tagged/{tag}` | pdf_export.py:186 | FALSCH | Query auf nicht existente Felder `source_type`/`source_id`/`tag_slug` (198-201) statt `content_type`/`content_id`/`concept_id` → immer leer; zudem 0 Referenzen. |
| GET `/api/references/` | references.py:19 | OK | Genutzt; Randfall: `has_doi=false` überschreibt Such-`$or` (35-48). |
| GET `/api/references/top-cited` | references.py:79 | OK | Genutzt. |
| GET `/api/references/importable` | references.py:109 | OK | Genutzt. |
| GET `/api/references/statistics` | references.py:143 | OK | Genutzt. |
| GET `/api/references/{rid}` | references.py:195 | TOT | 0 Referenzen; Bug: `paper_id` String vs. ObjectId-Suche (216-219) → paper_details nie gefunden. |
| POST `/api/references/{rid}/import` | references.py:241 | UNVOLLSTÄNDIG | ArXiv-Pfad OK und genutzt; DOI-Pfad explizit 501 (296-297, „Future Enhancements: CrossRef" — bewusste Lücke). |
| POST `/api/references/{rid}/generate-bibtex` | references.py:302 | OK | Genutzt. |
| GET `/api/references/paper/{pid}/citations` | references.py:374 | TOT | 0 Referenzen; `paper_citations`-Collection leer (live geprüft). |
| POST `/api/references/batch-import` | references.py:431 | STUB | „For now, just mark as would-import" (456-457) — meldet Erfolg ohne Import; 0 Referenzen. |

### Details — Kernpunkte

**1. DELETE `/{id}/tags/{tag}` — STUB, aktiv genutzt (höchste Priorität)** (concepts.py:133-138): bedingungslos „Tag removed successfully", keine DB-Operation; Frontend ruft real auf (usePaperAnnotations.ts:126) → Nutzer sieht „entfernt", Tag bleibt. Korrektur: an remove_concept delegieren oder Frontend umstellen. Aufwand: klein.

**2. POST `/{id}/snippets` — FEHLT**: Frontend-POST → 405, im catch nur geloggt. Korrektur: POST/DELETE analog Artikel-Endpoint. Aufwand: klein.

**3. POST `/{id}/tags/suggest` — FALSCH** (tag_suggestions.py:90 vs. 219): 400-Anforderung wird von except geschluckt → 200 leer. Korrektur: Prüfung vor try oder `except HTTPException: raise`. Aufwand: klein.

**4. PUT `/{id}/apply-affiliations` — FALSCH** (affiliations.py:222-230): schreibt in `authors` statt `authors_detailed`; Facetten sehen nichts, String-Format bricht. Aufwand: klein–mittel.

**5. GET `/api/pdf/tagged/{tag}` — FALSCH+TOT** (pdf_export.py:198-206): falsches tag_instances-Schema → immer 404. Aufwand: klein.

**6. cancel-processing — UNVOLLSTÄNDIG** (processing.py:140): Background-Task prüft cancelled nie; Marker `/kill` existiert bereits für Timeouts (processing_helpers.py:204). Aufwand: mittel.

**7. PUT metadata — UNVOLLSTÄNDIG**: `flagged`/`rating` wirkungslos. Aufwand: klein.

**8. PUT content — UNVOLLSTÄNDIG**: matched_count prüfen; BSON-Datetime. Aufwand: klein.

**9. bulk-action — UNVOLLSTÄNDIG** (bulk_ops.py:45-76): accept ohne add_tag, reject No-op. Aufwand: mittel.

**10. direct_url_import add_tags — UNVOLLSTÄNDIG** (163-170): Roh-Insert ohne concept_id → concept_service.add_tag verwenden. Aufwand: klein.

**11. references DOI-Import 501** — bewusste Lücke (CrossRef geplant). Aufwand: groß.

**12-14. TOT-Block**: process-with-entities (defekt), generate-multiple (Literal-\n-Bug), analyses/async-Flow, extract-entities, entities-Duplikate unter /api/papers (review zudem Stub), tags/suggestions-Route, pdf_export bulk/author/recent, references/{rid} (Bug), citations (leere Collection), batch-import (Stub). Entfernen empfohlen. Aufwand: je klein.

### Statuszählung
**OK: 54, UNVOLLSTÄNDIG: 7, FALSCH: 3, STUB: 2, TOT: 14, FEHLT: 1, Intention unklar: 0** (81 Einträge)

Auffälligstes Muster: Modularisierung hat Kernpfade sauber erhalten (alle dokumentierten Fixes Jan–Mai 2026 nachweisbar), aber Legacy-Duplikate mitkopiert. Zwei nutzerwirksame Defekte: aktiver Tag-Lösch-Stub (concepts.py:133) und fehlender Snippet-POST (→405).
## Bereich: Books/Articles/Substack/Reddit-API

Basis: Router-Registrierung in `backend/app/main.py:178-207`. TOT-Prüfung per Grep in `frontend/src` + Backend; Shadowing-Befunde zusätzlich empirisch per `curl` gegen laufendes Backend (Port 8088) verifiziert.

### Tabelle

| Eintrag | Datei:Zeile | Status | Begründung (1 Satz) |
|---|---|---|---|
| **books/** | | | |
| GET /api/books/ | books/crud.py:43 | OK | Filter, Pagination, Konzept-Anreicherung vollständig; Frontend nutzt es. |
| GET /api/books/facets | books/facets.py:28 | **FALSCH** | Von GET `/{book_id}` (crud.py:244) verschattet, da crud-Router zuerst registriert (books/__init__.py:22-24) — empirisch 404, obwohl Frontend ihn aufruft. |
| GET /api/books/{book_id} | books/crud.py:244 | UNVOLLSTÄNDIG | `ObjectId(cid)` (crud.py:257) ohne try/except → 500 bei nicht-konformen concept_ids; verschattet zudem `/facets`. |
| POST /api/books/upload | books/crud.py:268 | OK | Dateityp-Validierung + Filename-Sanitization vorhanden. |
| PUT /api/books/{book_id} | books/crud.py:334 | TOT | Kein Frontend-Aufruf gefunden. |
| DELETE /api/books/{book_id} | books/crud.py:370 | TOT | unsicher: kein Frontend-Aufruf gefunden. |
| POST /{book_id}/concepts | books/concepts.py:24 | OK | Frontend nutzt es. |
| DELETE /{book_id}/concepts/{cid} | books/concepts.py:70 | OK | Frontend nutzt es (BookViewerOptimized.tsx:323). |
| GET /{book_id}/content | books/content.py:17 | OK | Frontend nutzt es; 404-Behandlung vorhanden. |
| GET /{book_id}/download | books/content.py:35 | TOT | unsicher: kein Frontend-Aufruf; Dateien via Static-Mount `/books` (main.py:221) ausgeliefert. |
| POST /{book_id}/process | books/processing.py:21 | OK | Queue-Insert mit Duplikat-Schutz; Worker existiert und ist dokumentiert. |
| POST /{book_id}/process-direct | books/processing.py:75 | OK | Entspricht CLAUDE.md-Doku (1-6h synchron). |
| query_builder-Funktionen | books/query_builder.py:17-123 | OK | Alle 5 Builder von crud.py:80-100 genutzt. |
| get_book_by_id | books/utils.py:74 | OK | Überall im Package genutzt. |
| class ProcessingStatus | books/utils.py:58 | TOT | Konstantenklasse nirgends referenziert. |
| readability_service | books/utils.py:49 | TOT | Instanziiert, aber in keinem books-Submodul verwendet. |
| **articles/** | | | |
| GET /api/articles/ | articles/browse.py:29 | OK | Funktioniert; Frontend nutzt es. |
| GET /faceted-search | articles/browse.py:78 | OK | Frontend nutzt es (3×). |
| GET /{id}/images/{filename} | articles/browse.py:171 | OK | Sicherheitscheck `filename.startswith(article_id)`. |
| DELETE /{article_id} | articles/browse.py:198 | UNVOLLSTÄNDIG | tag_instances-Cleanup (212-215) nutzt nur URL-Parameter — bei Löschung via `old_sqlite_id` bleiben Instanzen verwaist. |
| GET /{article_id} | articles/browse.py:219 | OK | Funktioniert; verschattet aber `/authors` und `/without-author`. |
| POST /{id}/concepts | articles/content.py:16 | OK | Frontend nutzt es; aktualisiert `concept_ids`. |
| DELETE /{id}/concepts/{cid} | articles/content.py:59 | OK | Frontend nutzt es. |
| DELETE /{id}/tags/{tag_name} | articles/content.py:89 | UNVOLLSTÄNDIG | `tag_name` ungeescaped in `$regex` (content.py:108). |
| POST /{id}/snippets | articles/content.py:137 | OK | Frontend nutzt es. |
| DELETE /{id}/snippets/{sid} | articles/content.py:168 | OK | Frontend nutzt es. |
| PATCH /{article_id} | articles/content.py:191 | OK | Feld-Whitelist, Datums-Parsing. |
| GET /without-author | articles/content.py:250 | **FALSCH** | (a) von GET `/{article_id}` verschattet → empirisch 404; (b) Frontend ruft zudem falschen Pfad `/api/articles/articles/without-author`. |
| GET /authors/all | articles/authors.py:13 | OK | Empirisch 200, Frontend nutzt es (2×). |
| GET /authors | articles/authors.py:47 | **FALSCH** | Von GET `/{article_id}` verschattet → 404 trotz Frontend-Aufruf; zudem 1:1-Duplikat von `/authors/all`. |
| POST /authors | articles/authors.py:86 | OK | Existenz-Check + Insert. |
| PUT /authors/{author_id} | articles/authors.py:117 | OK | Frontend nutzt es; propagiert Namensänderung. |
| DELETE /authors/{author_id} | articles/authors.py:171 | OK | Frontend nutzt es. |
| PUT /{article_id}/author | articles/authors.py:205 | OK | Frontend nutzt es. |
| POST /authors/{id}/assign-articles | articles/authors.py:298 | OK | Frontend nutzt es. |
| POST /{id}/extract-metadata | articles/content_processing.py:15 | OK | LLM via LLMManager (kein Hardcoding). |
| POST /{id}/tags/suggest | articles/content_processing.py:109 | OK | Frontend nutzt es. |
| POST /{id}/apply-concepts | articles/content_processing.py:312 | UNVOLLSTÄNDIG | Aktualisiert nicht `articles.concept_ids` — `concept_id`-Filter in GET `/` (browse.py:47) findet so getaggte Artikel nicht. |
| POST /{id}/summarize | articles/content_processing.py:356 | OK | Caching, differenzierte Fehlercodes. |
| POST /{id}/recollect | articles/content_processing.py:464 | OK | Auth-/ImportError-Pfade behandelt. |
| browse_helpers-Funktionen | articles/browse_helpers.py:10-409 | OK | Alle Helper genutzt; Batch-Lookups gegen N+1. |
| **article_import/** (Prefix /api/v2/articles) | | | |
| POST /import-url | article_import/url_import.py:168 | OK | Smart-Dispatch wie im Docstring; Frontend nutzt es. |
| POST /enhanced-import | article_import/url_import.py:352 | OK | Intern von beiden Cookie-Wrappern genutzt. |
| POST /enhanced/check-paywall | article_import/url_import.py:529 | UNVOLLSTÄNDIG | Grobe Heuristik; Bedingung `'paywall' in x-frame-options` (539) kann nie zutreffen. |
| POST /enhanced/import-basic | article_import/url_import.py:545 | TOT | Reiner Alias für `/import-url`; nirgends referenziert. |
| POST /enhanced/import-with-cookie-string | article_import/url_import.py:550 | OK | Frontend nutzt es. |
| POST /enhanced/import-with-cookies | article_import/url_import.py:569 | OK | Frontend nutzt es (2×). |
| POST /import-batch | article_import/url_import.py:581 | OK | Frontend nutzt es; per-URL-Fehlerisolierung. |
| GET /test | article_import/url_import.py:603 | STUB | Hardcodierter Diagnose-Endpoint, nirgends referenziert. |
| GET /auth-sites | article_import/conversion.py:32 | OK | Frontend nutzt es. |
| GET /auth-status/{site} | article_import/conversion.py:71 | TOT | Kein Frontend-Aufruf — Status via `/auth-sites`. |
| POST /start-auth/{site} | article_import/conversion.py:110 | OK | Frontend nutzt es (2×). |
| DELETE /auth/{site} | article_import/conversion.py:160 | OK | Frontend nutzt es. |
| POST /import-url-playwright | article_import/conversion.py:256 | OK | Frontend nutzt es; 503 bei fehlendem Playwright. |
| service_import_url_playwright | article_import/conversion.py:184 | OK | Von Endpoint und Smart-Dispatch (url_import.py:218) genutzt. |
| **article_preview.py** | | | |
| POST /regenerate/{article_id} | article_preview.py:118 | OK | Frontend nutzt es. |
| POST /beautify/{article_id} | article_preview.py:187 | OK | Frontend nutzt es; mdformat vorhanden. |
| GET /check/{article_id} | article_preview.py:256 | TOT | Kein Frontend-Aufruf gefunden. |
| generate_preview / beautify_markdown | article_preview.py:39 / 16 | OK | Beide von aktiven Endpoints genutzt. |
| **article_clustering_mongodb.py** | | | |
| GET /cluster/kmeans | article_clustering_mongodb.py:52 | UNVOLLSTÄNDIG | `min_tags`-Filter (74-75) NACH `n_clusters`-Mindestcheck (64) → kann Datensatz unter n_clusters drücken und crashen. |
| GET /cluster/hierarchical | article_clustering_mongodb.py:96 | OK | Frontend nutzt es. |
| GET /cluster/dbscan | article_clustering_mongodb.py:142 | OK | Frontend nutzt es. |
| GET /similar/{article_id} | article_clustering_mongodb.py:182 | OK | Frontend nutzt es. |
| GET /tag-cooccurrence | article_clustering_mongodb.py:233 | OK | Frontend nutzt es. |
| GET /summary | article_clustering_mongodb.py:262 | OK | Frontend nutzt es. |
| GET /visualization-data | article_clustering_mongodb.py:290 | OK | Frontend nutzt es. |
| **substack_mongodb.py** | | | |
| GET /trends | substack_mongodb.py:21 | UNVOLLSTÄNDIG | `snippet_insights`/`tag_relationships` hardcodiert leer (162-169); Scope-Bug `stop_words` (76 vs. 96) → NameError-Risiko; naive/aware-Datumsvergleich (136). |
| GET /health | substack_mongodb.py:177 | OK | Empirisch 200. |
| Dokumentierte Substack-Endpoints (/articles, /summarize, /snippets, /authors) | CLAUDE.md „API Endpoints (Extended)" | **FEHLT** | In substack_mongodb.py nicht vorhanden; Funktionalität lebt unter /api/articles — CLAUDE.md veraltet. |
| **reddit_mongodb.py** | | | |
| GET / | reddit_mongodb.py:28 | UNVOLLSTÄNDIG | `subreddit`/`author`/`text_search` ungeescaped in `$regex` (49, 53, 76-77). |
| GET /faceted-search | reddit_mongodb.py:145 | UNVOLLSTÄNDIG | Count-Query (178-202) lässt `concept_id`-Filter weg → falsche total/Pagination bei Konzeptfilter. |
| GET /facets | reddit_mongodb.py:217 | OK | Frontend nutzt es. |
| GET /{post_id} | reddit_mongodb.py:269 | TOT | Dokumentiert, aber kein Frontend-Aufruf. |
| POST /{post_id}/tags | reddit_mongodb.py:300 | TOT | Frontend taggt via `/api/concepts/suggestions/reddit/...`. |
| DELETE /{post_id}/tags/{cid} | reddit_mongodb.py:341 | TOT | Kein Frontend-Aufruf. |
| GET /stats/collection | reddit_mongodb.py:372 | TOT | Kein Frontend-Aufruf trotz Doku. |
| POST /collect | reddit_mongodb.py:389 | TOT | CLAUDE.md verspricht UI-Trigger — kein Frontend-Aufruf → UI-Feature fehlt. |
| GET /subreddits/config | reddit_mongodb.py:406 | TOT | Kein Aufruf; CWD-abhängiger Pfad `'reddit_config.json'` (411). |
| GET /search/suggest | reddit_mongodb.py:418 | TOT | Kein Aufruf; Duplicate-Dict-Key-Bug (428-431: zweimal `"author"`). |

### Details (alles nicht-OK) — Kernpunkte

**1. GET /api/books/facets — FALSCH** (books/facets.py:28): Route nie erreichbar — `crud_router` mit `GET /{book_id}` vor `facets_router` registriert (books/__init__.py:22-23); curl → 404; Frontend-Aufruf FacetedBooksDashboard.tsx:155 läuft ins Leere → Books-Facetten funktionslos. Korrektur: Routerreihenfolge. Aufwand: klein.

**2. GET /api/articles/authors — FALSCH** (authors.py:47): Verschattet durch `GET /{article_id}` (Reihenfolge articles/__init__.py:9-12) → 404; zudem Duplikat von `/authors/all` mit identischem Funktionsnamen. Korrektur: Reihenfolge + Duplikat entfernen. Aufwand: klein.

**3. GET /api/articles/without-author — FALSCH** (content.py:250): Verschattet → 404; Frontend ruft zudem falschen Pfad `/api/articles/articles/without-author` → beidseitig kaputt. Aufwand: klein.

**4. Reddit-TOT-Block** (reddit_mongodb.py:269-431): CLAUDE.md dokumentiert alle Endpoints inkl. UI-Collect-Trigger; Frontend nutzt nur `/faceted-search` + `/facets`. `/search/suggest` mit Duplicate-Key-Bug, `/subreddits/config` mit CWD-Pfad. Korrektur: UI anbinden oder entfernen. Aufwand: mittel (entfernen: klein).

**5. Reddit faceted-search Count ohne concept_id-Filter** (145-202): total/pages falsch bei Konzeptfilter. Aufwand: klein.

**6. Reddit GET / Regex-Injection** (49, 53, 76-77): `re.escape()` fehlt. Aufwand: klein.

**7. Substack /trends** (21): Teilstub (leere Felder „Would need complex analysis"), stop_words-Scope-Bug (76/96), tz-naive Fallback (136). Aufwand: mittel (Bugfixes: klein).

**8. Substack-Doku-Endpoints FEHLT**: CLAUDE.md nennt /articles etc. — migriert nach /api/articles, Doku nicht nachgezogen. Aufwand: klein (nur Doku).

**9. apply-concepts UNVOLLSTÄNDIG** (content_processing.py:312): `$addToSet: {concept_ids}` fehlt im Gegensatz zu content.py:41-44. Aufwand: klein.

**10. DELETE Artikel** (browse.py:198): verwaiste tag_instances bei old_sqlite_id-Zugriff. Aufwand: klein.

**11. DELETE tags/{tag_name}** (content.py:108): re.escape fehlt. Aufwand: klein.

**12. GET books/{book_id}** (crud.py:257): ObjectId ohne Guard → 500-Risiko; Listen-Endpoint macht es defensiv vor (141-148). Aufwand: klein.

**13. Kleinere TOT/STUB**: books PUT/DELETE/download (unsicher, evtl. geplant); ProcessingStatus + readability_service (books/utils.py); import-basic-Alias; /test-Stub; auth-status redundant; article-preview/check; check-paywall tote Bedingung; kmeans min_tags-Reihenfolge. Alle Aufwand klein.

### Statuszählung
(über 64 bewertete Einträge)
**OK: 40, UNVOLLSTÄNDIG: 9, FALSCH: 3, STUB: 1, TOT: 13, FEHLT: 1, Intention unklar: 0** (3 TOT als „unsicher": books PUT/DELETE/download)

Auffälligste Befunde: Drei durch Router-Reihenfolge verschattete, vom Frontend aktiv aufgerufene Endpoints (`/api/books/facets`, `/api/articles/authors`, `/api/articles/without-author`) liefern empirisch 404 — die Books-Facetten im Dashboard sind funktionslos. Reddit-API zu ~70 % ohne Frontend-Anbindung.
## Bereich: Trends/Analytics/Statistics-API

**Soll-Zustand:** CLAUDE.md dokumentiert das Trend Detection Dashboard (at-a-glance, cooccurrence, animated-timeline, heatmap, bubble-chart, network — alle als "implementiert, waren stubbed") + AI Summarization mit `paper_date_type` und Limits. Hinweis: CLAUDE.md nennt Pfade `/api/trends/...`, real `/api/analytics/trends/...` (main.py:188); Frontend nutzt den echten Pfad. Live-Verifikation gegen Backend (8088) und MongoDB durchgeführt.

### Tabelle

| Eintrag | Datei:Zeile | Status | Begründung (1 Satz) |
|---|---|---|---|
| GET /api/trends/analysis | trends_mongodb.py:94 | OK | Echte Daten, Batch-Queries; genutzt (TrendAnalysisModern.tsx:86); 368 Legacy-Artikel-Instanzen mit numerischer ID still ignoriert. |
| GET /api/trends/predictions | trends_mongodb.py:317 | TOT | Voll implementiert (Regression), kein Aufrufer; Intention unklar. |
| GET /api/user-trends/per-user | user_trends_mongodb.py:27 | OK | Genutzt (UserTrendAnalysisModern.tsx:54). |
| GET /api/user-trends/user/{username} | user_trends_mongodb.py:217 | OK | Genutzt (UserTrendAnalysisModern.tsx:70). |
| GET /api/user-trends/compare-users | user_trends_mongodb.py:435 | TOT | Implementiert (impl.py:17), kein Frontend-Aufruf. |
| GET /api/user-trends/influencers | user_trends_mongodb.py:445 | TOT | Implementiert (impl.py:187), kein Aufruf. |
| GET /api/user-trends/activity-heatmap | user_trends_mongodb.py:455 | TOT | Implementiert (impl.py:386), kein Aufruf. |
| GET /api/user-trends/engagement-metrics | user_trends_mongodb.py:464 | TOT | Implementiert (impl.py:491), kein Aufruf. |
| user_trends_mongodb_impl.py (4 Fn) | user_trends_mongodb_impl.py:17-680 | TOT | Nur von den 4 toten Routen aufgerufen. |
| GET /api/analytics/trends/tags | analytics_trends/visualizations.py:36 | OK | Genutzt (TrendVisualizationModern.tsx:125); kleinere N+1. |
| GET /api/analytics/trends/timeline | analytics_trends/visualizations.py:146 | OK | Genutzt (TrendVisualizationModern.tsx:119). |
| GET /api/analytics/trends/sankey | analytics_trends/visualizations.py:273 | STUB | Hartkodiert 3 Nodes, links: [], total_flow: 0 (live verifiziert); kein Aufruf. |
| GET /api/analytics/trends/wordcloud | analytics_trends/visualizations.py:296 | TOT | `days`-Parameter wirkungslos; kein Frontend-Aufruf. |
| GET /api/analytics/trends/treemap | analytics_trends/visualizations.py:366 | TOT | Datumsparameter wirkungslos; kein Aufruf. |
| GET /api/analytics/trends/radar | analytics_trends/visualizations.py:453 | STUB | Immer current_values: [0,0,0,0,0,0] (live verifiziert); kein Aufruf. |
| GET /api/analytics/trends/sparklines | analytics_trends/visualizations.py:490 | STUB | Nur Null-Arrays, keine DB-Abfrage; kein Aufruf. |
| GET /api/analytics/trends/forecast | analytics_trends/analysis.py:39 | TOT | Echte Prognose, kein Aufruf; Intention unklar. |
| POST /api/analytics/trends/summarize | analytics_trends/analysis.py:184 | OK | Entspricht CLAUDE.md (paper_date_type 196, Limits 193-195, Datums-Prompt 452); genutzt (SummarizationModern.tsx:226, TweetDeckView.tsx:179); latenter Duplicate-Key `'$ne': None, '$ne': ''` (246-247). |
| GET /api/analytics/trends/at-a-glance | analytics_trends/analysis.py:551 | OK | Echte Daten; genutzt (useTrendData.ts:92) — massives N+1 (find_one pro Konzept×Content, 624-649). |
| GET /api/analytics/trends/heatmap | analytics_trends/heatmap_bubble.py:31 | UNVOLLSTÄNDIG | Echt, aber Content pro Konzept×Tag neu geladen + find_one je Item → O(top_n×days×content) Roundtrips. |
| GET /api/analytics/trends/bubble-chart | analytics_trends/heatmap_bubble.py:138 | FALSCH | X-Achse ignoriert Tweets: safe_object_id (184) verwirft Twitter-String-IDs → first_seen für tweet-dominierte Konzepte = now (DB-verifiziert). |
| GET /api/analytics/trends/network | analytics_trends/network_correlation.py:19 | UNVOLLSTÄNDIG | Nodes/Links echt, aber "clusters" = 5 aktivste Einzelknoten (89-95), keine Clustererkennung. |
| GET /api/analytics/trends/cooccurrence | analytics_trends/cooccurrence.py:17 | OK | Batch-optimiert; genutzt (useTrendData.ts:127). |
| GET /api/analytics/trends/animated-timeline | analytics_trends/timeline_animation.py:24 | OK | Echte kumulative Frames; genutzt (useTrendData.ts:152). |
| GET /api/trends/analysis/top-concepts | trend_analysis_mongodb.py:21 | OK | Genutzt (TrendAnalysisOverview.tsx:53). |
| GET /api/trends/analysis/velocity-leaders | trend_analysis_mongodb.py:92 | OK | Genutzt. |
| GET /api/trends/analysis/rising | trend_analysis_mongodb.py:192 | OK | Genutzt. |
| GET /api/trends/analysis/declining | trend_analysis_mongodb.py:296 | OK | Genutzt. |
| GET /api/trends/analysis/timeline | trend_analysis_mongodb.py:401 | OK | Genutzt. |
| GET /api/trends/analysis/overview | trend_analysis_mongodb.py:550 | OK | Genutzt. |
| GET /api/topics/frequency | topic_explorer.py:77 | UNVOLLSTÄNDIG | Ohne start/end-Parameter → HTTP 500 (live verifiziert; naive/aware-Vergleich 186); Frontend sendet immer Daten → im UI funktionsfähig. |
| GET /api/topics/correlation | topic_explorer.py:225 | FALSCH | start/end geparst (242f), aber nie angewandt — Zukunftsfenster liefert volle Daten (live verifiziert). |
| GET /api/topics/popular | topic_explorer.py:353 | FALSCH | `days`-cutoff (367) geht nie in Pipeline ein — days=1 == days=3650 (live verifiziert). |
| GET /api/statistics/overview | statistics/overview.py:36 | TOT | Kein Frontend-Aufruf; `processed` nutzt nicht existentes `is_processed`. |
| GET /api/statistics/search/statistics | statistics/overview.py:153 | STUB | Expliziter Platzhalter ("For now, return placeholder", 164f). |
| GET /api/statistics/quality/metrics | statistics/overview.py:177 | TOT | avg_length hartkodiert 0 (187), is_processed-Feldfehler; kein Aufruf. |
| GET /api/statistics/export/summary | statistics/overview.py:216 | TOT | Kein Aufruf; Intention unklar. |
| GET /api/statistics/concepts/detailed | statistics/content_stats.py:17 | UNVOLLSTÄNDIG | Genutzt (SummarizationModern.tsx:173, ohne days); `days`-Zweig doppelt kaputt (kein Datumsfilter 84-87; String-ID vs. ObjectId 98-106); stark N+1. |
| GET /api/statistics/authors/detailed | statistics/content_stats.py:135 | TOT | Kein Aufruf; author_id nur bei 41/555 Artikeln. |
| GET /api/statistics/trends/detailed | statistics/collection_stats.py:17 | TOT | Kein Aufruf; is_processed (69) → immer 0. |
| GET /api/statistics/activity/heatmap | statistics/collection_stats.py:157 | TOT | Kein Aufruf. |
| GET /api/system/statistics/overview | system_stats/overview_and_content.py:20 | TOT | Route ohne Aufrufer; Funktion intern von /summary genutzt. |
| GET /api/system/statistics/content | system_stats/overview_and_content.py:61 | UNVOLLSTÄNDIG | Genutzt (StatisticsDashboard.tsx:133), aber `with_marker` (marker_processed existiert nicht) und Artikel-`with_tags` (leeres tags-Feld) → immer 0 im Dashboard. |
| GET /api/system/statistics/authors | system_stats/overview_and_content.py:135 | OK | Genutzt; 209/555 Artikel ohne author-Feld = Datenlücke. |
| GET /api/system/statistics/tags | system_stats/analytics.py:20 | TOT | Route ohne Aufruf; intern von /summary genutzt. |
| GET /api/system/statistics/trends | system_stats/analytics.py:83 | FALSCH | Genutzt (StatisticsDashboard.tsx:135), aber growth_rate positionsbasiert simuliert (157f), trend hartkodiert "up" (149), articles_per_week TODO-leer (215). |
| GET /api/system/statistics/cross-source | system_stats/analytics.py:226 | OK | Genutzt; teuer (Full-Scans, O(n²)-Autorenvergleich 336-352). |
| GET /api/system/statistics/system | system_stats/system_and_llm.py:22 | TOT | Route ohne Aufruf; unprocessed_papers zählt via grobid_/marker_processed fast alle 358 Papers als unverarbeitet (356 sind processed=true, DB-verifiziert) — fließt via /summary weiter. |
| GET /api/system/statistics/llm | system_stats/system_and_llm.py:145 | OK | Genutzt; echte Daten aus llm_usage (34.146 Docs). |
| GET /api/system/statistics/summary | system_stats/system_and_llm.py:240 | FALSCH | Genutzt; `authors`-Block liest `top_twitter_authors`/`top_substack_authors` (334f), die zu `twitter_authors`/`article_authors` umbenannt wurden → immer leer; toter locals()-Check (339). |
| GET /api/system/llm/circuit-breaker | system_stats/system_and_llm.py:374 | TOT | Kein Aufruf; unsicher: evtl. bewusster Ops-Endpunkt. |
| POST /api/system/llm/circuit-breaker/{provider}/reset | system_stats/system_and_llm.py:386 | TOT | Wie oben. |

### Details — Kernpunkte

- **Bubble-Chart FALSCH** (heatmap_bubble.py:138/184/190): tweets._id sind Twitter-ID-Strings, safe_object_id verwirft sie → X-Wert ≈ 0. Korrektur: String-ID für tweets direkt verwenden. Aufwand: klein.
- **Topic Explorer**: /frequency 500 ohne Datumsparameter (naive/aware, 117f vs. 186; Aufwand klein); /correlation Datumsfilter nie angewandt (251; Aufwand mittel); /popular cutoff nie verwendet (367; Aufwand klein — `match_criteria['created_at'] = {'$gte': cutoff}`).
- **system_stats**: /content-Nullfelder (marker_processed/tags → auf processor_used/tag_instances umstellen; klein); /trends simulierte Metriken als echt verkauft (mittel); /system falsches processed-Feld (klein); /summary Schlüssel-Mismatch → leere Autorenlisten (klein).
- **statistics/-Paket**: 7 von 8 Endpunkten ohne Aufrufer, /search/statistics expliziter Stub, mehrfach nicht existentes `is_processed`. Eindampfen oder fixen+anbinden. Aufwand: mittel.
- **Tote Visualisierungen**: sankey/radar/sparklines (Stubs), wordcloud/treemap (days wirkungslos), forecast, predictions, 4 user-trends-Endpunkte + impl (~680 LOC). Entfernen oder anbinden. Aufwand: klein–mittel.
- **summarize**: Duplicate-Key-Muster `{'$ne': None, '$ne': ''}` (246-247) gegen MEMORY-Regel `$nin` (praktisch neutralisiert). Aufwand: klein.
- **at-a-glance/heatmap**: massive N+1-Muster. Aufwand: mittel.

### Statuszählung
OK: 18, UNVOLLSTÄNDIG: 5, FALSCH: 5, STUB: 4, TOT: 20, FEHLT: 0, Intention unklar: 11 (Sekundärlabel bei TOT/STUB ohne dokumentierte Absicht)
## Bereich: Tags/Ontologie/Konzepte/RAG-API

**Vorbemerkung (DB-Fakten, live verifiziert):** Tweets speichern die Twitter-ID als `_id`, kein `id`-Feld (tweet_collector_service.py:571; countDocuments({id:{$exists:true}}) = 0). `tag_instances.concept_id`: 126.759 ObjectId vs. 322 String — String-Abfragen liefern 0 Treffer (verifiziert: gleiche ID als ObjectId → 9512, als String → 0). `tag_instances` hat weder `tag_text` noch `tag_name`. `ConceptOnlyTagService` besitzt `get_all_tags_with_counts`, `get_orphan_tags`, `update_tag_concept_links` NICHT (nur in mongodb_tag_service.py:224/320/371).

### Tabelle

| Eintrag | Datei:Zeile | Status | Begründung (1 Satz) |
|---|---|---|---|
| **tags_mongodb.py — /api/tags** | | | |
| GET / | tags_mongodb.py:32 | TOT | Kein Frontend-Aufruf. |
| GET /tweet/{id} | tags_mongodb.py:37 | TOT | Kein Aufruf. |
| POST /tweet/{id} | tags_mongodb.py:43 | FALSCH | `find_one({"id":...})` (51) trifft nie (Tweets nutzen `_id`) → immer 404; zudem TOT. |
| DELETE /tweet/{id}/{tag} | tags_mongodb.py:100 | TOT | Kein Aufruf. |
| GET /popular | tags_mongodb.py:114 | FALSCH | `get_all_tags_with_counts()` (117) existiert auf ConceptOnlyTagService nicht → 500. |
| POST /suggest/{id} | tags_mongodb.py:122 | FALSCH | Tweet-Lookup falsch (126); `search_similar_tags` (162) existiert nicht auf TagVectorStore; TOT. |
| GET /orphans | tags_mongodb.py:231 | FALSCH | `get_orphan_tags()` (234) existiert nicht → 500; Frontend ruft zudem nicht existente `/orphans/preview`+`/assign`. |
| POST /update-concept-links | tags_mongodb.py:240 | FALSCH | Methode existiert nicht → 500; TOT. |
| **tag_ontology/ — /api/ontology** | | | |
| GET /tree | concepts.py:21 | UNVOLLSTÄNDIG | Genutzt; Synonyme fast immer leer: Alias-Map keyed by str(ObjectId) (37), Lookup mit `c.get("id")`="c_XXXX" (47,75). |
| GET /hierarchy | concepts.py:102 | TOT | Kein Aufruf; würde zudem 500 werfen (ObjectId nicht serialisiert, 134-138). |
| GET /concepts | concepts.py:141 | UNVOLLSTÄNDIG | Genutzt; N+1-Alias-Query pro Konzept (174) über 25k Konzepte. |
| GET /concept/{id} | concepts.py:192 | FALSCH | Genutzt; usage_stats zählt mit String-concept_id (336-348) gegen ObjectId-Daten → immer 0. |
| POST /concept | concepts.py:360 | UNVOLLSTÄNDIG | `_id`="c_{count+1}" (366-372) kollidiert nach Löschungen, bricht ObjectId-Schema. |
| PUT /concept/{id} | concepts.py:406 | UNVOLLSTÄNDIG | Überschreibt display_name/description mit None (412-417); Lookup nur `{"id":...}`. |
| DELETE /concept/{id} | concepts.py:429 | UNVOLLSTÄNDIG | Parent-Bereinigung via id-Feld (452), parents enthalten ObjectIds → Referenzen bleiben. |
| POST /concepts | concepts_ontology.py:20 | UNVOLLSTÄNDIG | Nachträgliche `id`="c_{count}" (67) kann duplizieren. |
| PUT /concepts/{id} | concepts_ontology.py:79 | OK | ObjectId- und Custom-IDs korrekt. |
| DELETE /concepts/{id} | concepts_ontology.py:135 | UNVOLLSTÄNDIG | Kinder-parents-Arrays und tag_instances bleiben verwaist. |
| POST /concept/{id}/alias | aliases_and_search.py:21 | TOT | Frontend ruft `/synonym` (404); speichert concept_id als String entgegen Bestand. |
| DELETE /alias/{text} | aliases_and_search.py:50 | TOT | Kein Aufruf. |
| GET /search | aliases_and_search.py:66 | TOT | Kein Aufruf; Alias-Zweig kaputt (113). |
| GET /find-by-name/{tag} | aliases_and_search.py:140 | UNVOLLSTÄNDIG | Alias-Fallback fragt Feld `"alias"` ab (160), Kollektion nutzt `alias_text`. |
| POST /rebuild-mappings | tools.py:21 | FALSCH | Genutzt (TagOntologyModern.tsx:288); `orphan["tag_text"]` (45) existiert in 0 Instanzen → KeyError/500. |
| GET /stats | tools.py:71 | OK | Genutzt. |
| GET /graph | tools.py:100 | UNVOLLSTÄNDIG | usage_count via String (121) → immer 0; N+1 über 25k. |
| GET /export | tools.py:211 | OK | Genutzt; korrekt serialisiert. |
| **ontology_graph.py — /api/ontology-graph** | | | |
| GET /data | ontology_graph.py:19 | UNVOLLSTÄNDIG | Genutzt; Usage-Counts via String (45-47) → immer 0 (Knotengrößen/min_usage defekt), N+1. |
| GET /search | ontology_graph.py:194 | TOT | Kein Aufruf; gleicher Bug (212). |
| GET /neighbors/{id} | ontology_graph.py:232 | TOT | Kein Aufruf; Alias-Abfrage per String (276) → leer. |
| **concept_organization.py — /api/concepts/organization** | | | |
| GET /unorganized | concept_organization.py:44 | UNVOLLSTÄNDIG | Genutzt; usage_count mit String-_id (60-63) → immer 0. |
| POST /organize | concept_organization.py:75 | OK | Genutzt; Service existiert. |
| POST /organize-batch | concept_organization.py:123 | OK | Genutzt. |
| POST /apply-organization/{id} | concept_organization.py:167 | OK | Genutzt. |
| GET /stats | concept_organization.py:193 | OK | Genutzt. |
| **concepts_suggestions_mongodb.py — /api/concepts/suggestions** | | | |
| POST /tweets/{id}/suggest | concepts_suggestions_mongodb.py:31 | OK | Genutzt; Lookup korrekt über `_id` (39). |
| POST /tweets/{id}/apply-concepts | :183 | OK | Genutzt. |
| POST /reddit/{id}/suggest | :224 | OK | Genutzt. |
| POST /reddit/{id}/apply-concepts | :359 | OK | Genutzt. |
| POST /papers/{id}/suggest | :400 | TOT | Kein Aufruf; new_suggestions fest leer (441). |
| GET /search-concepts | :446 | UNVOLLSTÄNDIG | Genutzt; trotz Docstring „semantic" nur Stringmatching (495 „for now"). |
| **entity_extraction.py — /api/entities** | | | |
| POST /extract | entity_extraction.py:49 | UNVOLLSTÄNDIG | Artikel-Pfad ok; Tweet-Zweig `{'id':...}` (82) → für Tweets immer 404. |
| GET /suggestions/{article_id} | :136 | TOT | Kein Aufruf; entgegen Docstring kein Caching (159-163). |
| POST /review | :171 | STUB | Aktiv genutzt (EntityAnnotationReviewModern.tsx:102/135); „accept" baut Mock-Entity mit Platzhalter „Entity Text" (183-188), reject/modify persistieren nichts (210-224). |
| POST /bulk-action | :229 | UNVOLLSTÄNDIG | Kernpfad ok; Fallback ohne entities zählt nur (342-343). |
| GET /schema | :358 | OK | Genutzt. |
| POST /validate/{id} | :386 | TOT | Kein Aufruf. |
| GET /stats | :414 | TOT | Kein Aufruf; avg_confidence=0.82, acceptance_rate=0.75 hardcodiert (457-458). |
| **rag_concepts.py — /api/rag** | | | |
| GET /stats | rag_concepts.py:40 | OK | Genutzt. |
| GET /sample-questions | :66 | OK | Genutzt. |
| POST /ask | :86 | FALSCH | Genutzt; Response (115-121) verwirft `is_trend_analysis`/`documents_analyzed`/`source_type`, die Service liefert und Frontend erwartet (RAGSearchModern.tsx:403-415) → Trend-UI-Badges erscheinen nie; `concept_filter` ignoriert. |
| POST /search | :127 | TOT | Kein Aufruf. |
| POST /rebuild | :159 | OK | Genutzt. |
| GET /concepts/top | :182 | TOT | Kein Aufruf; stale Loop-Variable (211). |
| GET /health | :228 | TOT | Kein Aufruf. |
| **tag_reorganization/ — /api/tags/reorganize** | | | |
| POST /start | routes.py:228 | FALSCH | Genutzt (TagReorganizerPersistent.tsx:180); `add_task(..., db)` (245) referenziert undefinierten Namen `db` → NameError/500 bei jedem Aufruf — gesamter persistenter Reorganizer funktionsunfähig. |
| GET /stream/{id} | routes.py:254 | OK | SSE korrekt (erreicht wegen /start-Bug nie einen Task). |
| GET /status/{id} | routes.py:292 | TOT | Kein Aufruf. |
| POST /cancel/{id} | routes.py:302 | UNVOLLSTÄNDIG | Im gpt5-Modus wird cancelled während LLM-Phase nie geprüft (nur comprehensive-Loop, 153). |
| GET /result/{id} | routes.py:327 | OK | Genutzt. |
| DELETE /task/{id} | routes.py:349 | TOT | Kein Aufruf. |
| GET /active | routes.py:371 | TOT | Kein Aufruf. |
| GET /history | routes.py:391 | OK | Genutzt; persistiert in MongoDB. |
| GET /debug/current-concepts | debug_and_recovery.py:17 | OK | Genutzt. |
| GET /debug/test-gpt5-config | debug_and_recovery.py:102 | TOT | Kein Aufruf; relative Pfade CWD-abhängig (118). |
| GET /debug/{task_id} | debug_and_recovery.py:208 | TOT | Kein Aufruf. |
| GET /recover/{id} | recovery_and_apply.py:18 | OK | Genutzt. |
| POST /apply-recovered/{id} | recovery_and_apply.py:69 | OK | Genutzt. |
| POST /apply/{id} | recovery_and_apply.py:113 | OK | Genutzt. |
| POST /apply-direct | recovery_and_apply.py:172 | TOT | Kein Aufruf; `tag.get("tag_name")` (286) existiert in 0 Instanzen → No-op. |
| POST /apply-comprehensive | recovery_and_apply.py:323 | TOT | Kein Aufruf; `distinct("tag_name")` (474) → []; `clear_existing` (346) würde alle 25k Konzepte löschen (ungeschützt). |
| **FEHLT (Frontend erwartet, Backend fehlt)** | | | |
| POST /api/ontology/concept/{id}/synonym | TagOntologyModern.tsx:185 | FEHLT | Backend bietet nur /alias → 404. |
| POST /api/ontology/import-existing-tags | TagOntologyModern.tsx:301 | FEHLT | Kein Handler. |
| /api/tags/orphans/preview + /assign | OrphanTagAssigner.tsx:66,90 | FEHLT | Orphan-Panel läuft auf 404. |
| /api/tags/io (3 Aufrufe) | TagOntologyModern.tsx:209,242,267 | FEHLT | Import/Export ohne Backend. |
| /api/ontology/ai/* (4 Endpunkte) | OntologyAISuggestions.tsx:46-195 | FEHLT | AI-Suggestions ohne Backend. |
| /api/concepts/{unorganized,organization-stats,suggest-organization,apply-organization,batch-reorganize} | useConceptManagement.ts:72-206 | FEHLT | ConceptManagementCenter ruft falsche Prefixe (real: /api/concepts/organization/…). |

### Details — Kernpunkte

**1. POST /reorganize/start — FALSCH** (routes.py:245): `db` nicht definiert (Import 15-19 enthält nur `mongo_db`) → NameError → 500 bei jedem Start; gesamte Reorganizer-UI unbenutzbar. Korrektur: `db` → `mongo_db` oder Parameter entfernen. Aufwand: klein.

**2. Systemischer Typ-Bug Usage-Statistiken**: praktisch alle Usage-Zählungen (concepts.py:336-348, tools.py:121, ontology_graph.py:45/212/276, concept_organization.py:60) zählen mit String-`concept_id` gegen ObjectId-Daten → immer 0 (live verifiziert: 9512 vs. 0). Kommentar concepts.py:335 („stores as string") ist falsch. Korrektur: ObjectId bzw. `$in: [oid, str(oid)]`. Aufwand: klein (mehrere Stellen).

**3. tags_mongodb.py Service-Regression**: /popular, /orphans, /update-concept-links rufen Methoden, die nur auf dem toten MongoDBTagService existieren → AttributeError/500; POST /tweet + /suggest nutzen falsches `id`-Feld und nicht existente Vector-Store-Methode (Fehler geschluckt). Korrektur: portieren oder Endpunkte entfernen (Frontend nutzt sie nicht). Aufwand: klein-mittel.

**4. POST /api/rag/ask — FALSCH** (115-121): Trend-Metadaten verworfen, concept_filter ignoriert → dokumentiertes Trend-UI-Feature nie sichtbar. Korrektur: `**result` mergen, Filter durchreichen. Aufwand: klein.

**5. POST /rebuild-mappings — FALSCH** (tools.py:45): KeyError `tag_text`. Korrektur: display_name verwenden, ObjectId normalisieren. Aufwand: klein.

**6. POST /entities/review — STUB, aktiv genutzt** (181-224): Mock-Entity „for demonstration", reject/modify ohne Persistenz. Korrektur: echte Daten aus Request, Persistenz. Aufwand: mittel.

**7. FEHLT-Gruppen (6)**: aktiv geroutete UI-Komponenten (TagOntologyModern Synonym/IO, OrphanTagAssigner, ConceptManagementCenter, OntologyAISuggestions) rufen nicht (mehr) existente Endpunkte — vermutlich Kollateralschaden von Commit 49b0c53d/8d2a92fe. Korrektur: Frontend auf existierende Pfade umbiegen oder Endpunkte nachrüsten. Aufwand: mittel.

**8. UNVOLLSTÄNDIG-Muster**: /tree-Synonyme leer (Key-Mismatch); N+1 über 25k Konzepte (concepts, graph, ontology-graph); PUT-None-Overwrites; DELETE-Referenzreste; count-basierte ID-Vergabe kollisionsanfällig; find-by-name falsches Feld; search-concepts nur Stringmatching; entities/extract Tweet-Zweig; reorganize/cancel wirkungslos in LLM-Phase. Aufwand: je klein bis mittel.

### Statuszählung
OK: 22, UNVOLLSTÄNDIG: 15, FALSCH: 9, STUB: 1, TOT: 23, FEHLT: 6 (Gruppen), Intention unklar: 0

**Wichtigste 3 Befunde:** (1) /reorganize/start crasht mit NameError — persistenter Reorganizer tot. (2) Systemischer String-vs-ObjectId-Bug: alle Usage-Statistiken liefern 0. (3) /api/rag/ask verwirft Trend-Metadaten — dokumentiertes Feature unsichtbar.
## Bereich: Import-APIs / LLM-Preferences / main.py

### Tabelle

| Eintrag | Datei:Zeile | Status | Begründung (1 Satz) |
|---|---|---|---|
| **main.py** | | | |
| MongoDB-Startvalidierung (CFG-005) | main.py:59-68 | OK | Ping + Count, Abbruch bei Fehler. |
| CORS (CFG-004) | main.py:120-135 | OK | Env + Defaults inkl. 3470. |
| Timing-Middleware (OBS-001) | main.py:139-147 | OK | Wie Memory-Doku. |
| Exception-Handler | main.py:151-170 | OK | 5xx sanitisiert. |
| Router-Registrierung | main.py:172-211 | OK | Alle Module existieren, Prefixe konsistent. |
| Statische Mounts | main.py:214-222 | OK | Bedingt gemountet. |
| /health, / | main.py:225-278 | OK | DB-Ping + Service-Probes mit Timeout. |
| startup_event Index-Erstellung | main.py:280-298 | FALSCH | Kollidiert mit PERF-002-Textindizes aus `_ensure_indexes` — kombinierte Textindizes existieren in Live-DB nachweislich nicht. |
| Deprecated-LLM-Check | main.py:300-318 | OK | find_deprecated_preferences + Migrationshinweis. |
| shutdown_event | main.py:320-324 | OK | Schließt Client. |
| **arxiv.py** | | | |
| POST /api/arxiv/import | arxiv.py:93-240 | OK | Jan-4-Fix umgesetzt (113); authors + authors_detailed schema-konform. |
| POST /api/arxiv/search | arxiv.py:242-269 | OK | Genutzt (ArxivImportModal.tsx:95). |
| GET /api/arxiv/validate/{id} | arxiv.py:271-311 | TOT | Kein Aufrufer. |
| POST /api/arxiv/batch-import | arxiv.py:313-355 | TOT | Kein Aufrufer. |
| Modul-Fn `validate_arxiv_id` + Patterns | arxiv.py:16-60 | TOT | Nirgends aufgerufen; Name ab 272 vom Endpoint überschrieben (Relikt des kaputten Alt-Validators). |
| **acl_anthology.py** | | | |
| POST /parse | acl_anthology.py:35-72 | OK | Genutzt (ACLAnthologyImportModal.tsx:52). |
| POST /import | acl_anthology.py:74-224 | UNVOLLSTÄNDIG | Duplikat-Check (99-104) vergleicht Seiten-URL mit pdf_url → greift nie; kein authors_detailed (nur authors_list, 164); import_url=pdf_url (141). |
| POST /batch-import | acl_anthology.py:226-293 | TOT | Kein Aufrufer. |
| GET /validate-url | acl_anthology.py:337-369 | TOT | Kein Aufrufer. |
| `process_pdf_background` | acl_anthology.py:295-335 | FALSCH | Ruft nicht existente `PDFProcessorService.process_paper` (312) und `PaperAnalysisService.analyze_paper` (327) → crasht bei jedem Import mit process_pdf=True (Default!). |
| **acm_import.py** | | | |
| POST /api/acm/import | acm_import.py:24-112 | UNVOLLSTÄNDIG | `process_pdf` (22) stillschweigend ignoriert; authors_detailed als Plain-String-Liste (52) statt Objekte. |
| GET /api/acm/validate-url | acm_import.py:114-145 | OK | Genutzt (ACMImportModal.tsx:42). |
| **openreview_import.py** | | | |
| POST /validate-url | openreview_import.py:36-58 | OK | Genutzt. |
| POST /import | openreview_import.py:60-207 | OK | Vollständiges Autoren-Schema, Duplikat-Check, kanonisches publication_date. |
| GET /metadata/{id} | openreview_import.py:209-224 | OK | Genutzt. |
| GET /bibtex/{id} | openreview_import.py:226-248 | TOT | Kein Aufrufer. |
| `process_pdf_background` | openreview_import.py:250-284 | FALSCH | Ruft `pdf_processor.process_pdf_async` — Methode existiert nur auf AsyncPDFProcessor → AttributeError bei jedem Import mit PDF. |
| **jair_import.py** | | | |
| POST /parse | jair_import.py:29-51 | OK | Genutzt (JAIRImportModal.tsx:51). |
| POST /import | jair_import.py:54-130 | UNVOLLSTÄNDIG | `published_date` als Roh-String (103) statt kanonisches `publication_date` — nur via Legacy-Fallback nutzbar. |
| **dblp_mongodb.py** | | | |
| GET /api/dblp/search | dblp_mongodb.py:26-43 | TOT | Frontend nutzt ausschließlich /api/papers/dblp/search. |
| GET /api/dblp/bibtex | dblp_mongodb.py:45-81 | OK | Genutzt (DBLPSearchModal.tsx:106). |
| GET /api/dblp/metadata/{key} | dblp_mongodb.py:83-103 | OK | Genutzt. |
| GET /api/papers/dblp/search | dblp_mongodb.py:106-123 | OK | Genutzt. |
| POST /attach-metadata/{id} | dblp_mongodb.py:124-242 | UNVOLLSTÄNDIG | `authors` als String-Liste (176-182), kein authors_detailed — Schema-Verstoß. |
| **authors_management.py** | | | |
| GET /api/authors/ | authors_management.py:62-116 | OK | Genutzt. |
| GET /{id} | authors_management.py:119-183 | UNVOLLSTÄNDIG | `except Exception` (182) wandelt eigene 404 in 400. |
| PUT /{id} | authors_management.py:186-231 | TOT | Kein Aufrufer; gleicher 404→400-Bug. |
| DELETE /{id} | authors_management.py:234-264 | TOT | Kein Aufrufer. |
| POST /find-similar | authors_management.py:267-302 | TOT | UI nie gebaut (AUTHOR_UI_DESIGN.md:282). |
| POST /merge | authors_management.py:305-347 | TOT | UI nie gebaut. |
| GET /analytics/overview | authors_management.py:350-439 | TOT | Kein Aufrufer. |
| **llm_preferences.py** | | | |
| GET /api/llm/status | llm_preferences.py:15-68 | OK | Genutzt (ApiKeyStatusBanner). |
| GET /models | llm_preferences.py:100-132 | UNVOLLSTÄNDIG | Deprecated Gemini-3-Preview-IDs korrekt entfernt, aber `gpt-4o`, `gpt-4o-mini`, `grok-2-latest` weiter wählbar (litellm_config.yaml:314-322, 414-416; models.ts:178-198) — unsicher: möglicher Verstoß gegen „veraltete Modelle in keiner Auswahl". |
| GET /tasks | llm_preferences.py:135-158 | TOT | Nur Einzel-Route genutzt. |
| GET /tasks/{task} | llm_preferences.py:161-192 | OK | Genutzt (UnifiedModelSelector.tsx:95). |
| GET /preferences | llm_preferences.py:195-217 | OK | Genutzt. |
| POST /preferences | llm_preferences.py:220-287 | UNVOLLSTÄNDIG | `model_name` nicht gegen get_valid_model_names() validiert (261-267) — veraltete IDs speicherbar. |
| PUT /preferences/batch | llm_preferences.py:290-371 | TOT | Kein Aufrufer; gleiches Validierungsloch. |
| DELETE /preferences/{task} | llm_preferences.py:374-415 | OK | Genutzt. |
| GET /preferences/health | llm_preferences.py:418-454 | OK | Genutzt (DeprecatedPreferencesBanner.tsx:26). |
| POST /preferences/migrate | llm_preferences.py:457-476 | OK | Genutzt. |
| DELETE /preferences | llm_preferences.py:479-521 | OK | Genutzt. |
| **user_settings.py** | | | |
| GET /{key} | user_settings.py:45-57 | OK | Genutzt (TweetDeckView.tsx:593). |
| PUT /{key} | user_settings.py:60-79 | OK | Genutzt; Upsert + Unique-Index. |
| DELETE /{key} | user_settings.py:82-85 | TOT | Kein Aufrufer (CRUD-Vervollständigung). |

## Details — Kernpunkte

**1. main.py Index-Erstellung — FALSCH** (280-298): legt Single-Field-Textindizes an (papers.title, articles.title, 289-290); MongoDB erlaubt nur einen Textindex pro Collection → kombinierte PERF-002-Indizes (`papers_text_search` etc., mongodb.py:217-224) scheitern bei jedem Start still (Live-DB verifiziert: nur title_text/text_text vorhanden). Korrektur: Textindex-Zeilen aus startup_event entfernen, Alt-Indizes droppen, Indexpflege `_ensure_indexes` überlassen. Aufwand: klein.

**2. ACL `process_pdf_background` — FALSCH** (295-335): nicht existente Methoden `process_paper` (312) / `analyze_paper` (327) → AttributeError bei jedem Import mit process_pdf=True (Default). Korrektur: `processor.process_pdf(pdf_path, mongo_paper_id=...)`, Analyse-Aufruf entfernen. Aufwand: mittel.

**3. OpenReview `process_pdf_background` — FALSCH** (250-284): `process_pdf_async` existiert nicht auf PDFProcessorService. Korrektur: get_async_pdf_processor() oder process_pdf(...). Aufwand: klein.

**4. ACL /import — UNVOLLSTÄNDIG**: Duplikat-Check wirkungslos (Seiten-URL vs. pdf_url); kein authors_detailed; import_url falsch. Aufwand: klein.

**5. ACM /import — UNVOLLSTÄNDIG**: process_pdf ignoriert; authors_detailed als Strings (Facets-Crash-Typ). Aufwand: klein.

**6. JAIR /import — UNVOLLSTÄNDIG**: published_date-Roh-String statt publication_date-datetime. Aufwand: klein.

**7. DBLP attach-metadata — UNVOLLSTÄNDIG**: authors als Liste, kein authors_detailed. Aufwand: klein.

**8. authors_management 404→400-Bug** (182, 230): `except HTTPException: raise` fehlt. Aufwand: klein.

**9. llm_preferences POST — UNVOLLSTÄNDIG**: model_name-Validierung fehlt (Deprecated-Maschinerie soll genau das verhindern). Korrektur: gegen get_valid_model_names() prüfen, sonst 422. Aufwand: klein.

**10. Modell-Auswahllisten — UNVOLLSTÄNDIG (unsicher)**: gpt-4o/gpt-4o-mini/grok-2-latest weiter wählbar; Regel „veraltete Modelle in keiner Auswahl" (User-Vorgabe). Korrektur: entscheiden + aus yaml/models.ts entfernen + MODEL_MIGRATION_MAP. Aufwand: klein.

**11. TOT-Block**: arxiv validate/batch-import + Alt-Validator, acl batch-import/validate-url, openreview bibtex, dblp /api/dblp/search, llm tasks-Liste, preferences/batch, user-settings DELETE, authors_management PUT/DELETE/find-similar/merge/analytics (UI aus AUTHOR_UI_DESIGN.md nie gebaut). Entfernen oder UI nachziehen. Aufwand: je klein.

### Statuszählung
OK: 31, UNVOLLSTÄNDIG: 7, FALSCH: 3, STUB: 0, TOT: 15, FEHLT: 0, Intention unklar: 0 (1 Regel-Fundstelle „unsicher")

**Wichtigste Befunde:** (1) Beide Hintergrund-PDF-Verarbeitungen (ACL, OpenReview) rufen nicht existente Methoden auf und schlagen seit jeher still fehl (Default aktiv). (2) PERF-002-Volltextindizes werden wegen Altindex-Konflikt nie angelegt (Live-DB verifiziert). (3) ACL-Duplikat-Check wirkungslos.
## Bereich: Services — LLM/RAG/Embeddings

Alle Pfade relativ zu `backend/app/services/` (sofern nicht anders angegeben).

### Tabelle

| Eintrag | Datei:Zeile | Status | Begründung (1 Satz) |
|---|---|---|---|
| `LLMManager` (LiteLLM Router, Prefs, Migration) | llm_manager.py:104 | OK | Konfig-getrieben über litellm_config.yaml, MongoDB-Usage-Logging, Preference-Migration; breit genutzt (≥19 Importstellen, u. a. main.py:304, rag/__init__.py:7) |
| `custom_mongodb_callback` / `_failure_callback` | llm_manager.py:19/68 | OK | Manuell in completion()/completion_sync() aufgerufen (llm_manager.py:430, 500) — dokumentierte Absicht (Kommentar Z. 193) |
| `LLMService` (get_completion, generate_completion) | llm_service.py:40 | UNVOLLSTÄNDIG | Kernpfade OK und genutzt (papers/analysis_generation.py:65 u. a.), aber `suggest_tags`/`_fallback_tag_extraction` sind intern tote Methoden und die dokumentierte spaCy-Fallback-Stufe fehlt |
| `CircuitBreakerManager`, `classify_error`, `build_model_config` | llm_helpers.py:60/12/47 | OK | Sauber aus llm_service.py extrahiert und dort genutzt (llm_service.py:27-32) |
| `LangChainLLMService` | langchain_llm_service.py:15 | TOT | Kein einziger Import im Backend; enthält zudem hardcodierte Modell-Fallbacks (Z. 136-139) und Inline-Default-Prompts (Z. 335-336) |
| `ConceptBasedRAGService` (Fassade) | rag/__init__.py:27 | OK | Delegiert an rag/-Module; via Shim von api/rag_concepts.py:11 genutzt, Router in main.py:191 registriert |
| `search` + `_blend_results` (Proportional Blending) | rag/search.py:7/139 | OK | Implementiert das in CLAUDE.md dokumentierte Proportional Blending korrekt |
| `rebuild_index`, `get_embedding(_batch)`, `load_index` | rag/index_manager.py:61/278/42 | FALSCH | Embedding-Modelle hart codiert (`models/text-embedding-004` Z. 300/340, `text-embedding-ada-002` Z. 308) entgegen CLAUDE.md-Regel; widerspricht llm.json `semantic_search` = `text-embedding-3-small` (llm.json:95) |
| `is_trend_query`, `analyze_trends`, `ask` | rag/trend_analysis.py:17/31/181 | UNVOLLSTÄNDIG | Funktional und genutzt, aber cwd-abhängige Config-Loads (Z. 117/272, 144/300) statt absolutem Pfad (CFG-006-Muster), plus tote Variablen `trend_model_config`/`rag_model_config` (Z. 147/303) |
| `rag_service_concepts.py` (Shim) | rag_service_concepts.py:4 | OK | Absichtlicher Rückwärtskompatibilitäts-Shim, genutzt von api/rag_concepts.py:11 und rebuild_rag_index.py:9 |
| `rag_helpers.py` (Index-/Doc-/Search-Utilities) | rag_helpers.py:33-377 | TOT | Von keinem Modul importiert; früherer Konsument `rag_simple.py` existiert nicht mehr |
| `rag_embedding_helpers.py` | rag_embedding_helpers.py:12-123 | TOT | Einziger Importeur ist das selbst tote rag_helpers.py:21 → transitiv tot |
| `EmbeddingsService` | embeddings_service.py:15 | TOT | Kein Import im Backend; zusätzlich hardcodiertes Embedding-Modell (Z. 28) und cwd-abhängiges `open('llm.json')` (Z. 19) |
| `TagVectorStore` | vector_store_mongodb.py:19 | FALSCH | Einziger Konsument ruft `search_similar_tags(...)` auf (api/tags_mongodb.py:162), Klasse bietet nur `search_similar(...)` (Z. 187) → AttributeError, still geschluckt; `build_from_mongodb` (Z. 94) hat keine Aufrufer |
| `SpacyTagger` | spacy_tagger.py:16 | TOT | Kein Import im Backend — obwohl CLAUDE.md die Fallback-Kette GPT→spaCy→Keywords als aktiv dokumentiert |
| spaCy-Fallback-Stufe in aktiver Tag-Suggestion | — (Soll: llm_service.py / tag_suggestion_service.py) | FEHLT | CLAUDE.md verspricht spaCy als 2. Stufe; llm_service.py:410 fällt direkt auf Keyword-Extraktion zurück, tag_suggestion_service.py:103 gibt bei Fehler `[]` zurück |
| `TagSuggestionService.suggest_tags` | tag_suggestion_service.py:41 | FALSCH | Template-Format mit falschen kwargs (Z. 73-77) vs. Platzhalter `{text}`/`{author}` → KeyError bei jedem Aufruf, abgefangen Z. 101-104 → liefert IMMER `[]` |
| `EntityExtractionService` + `EntityExtraction` | entity_extraction_service.py:48/16 | OK | Konfig-getrieben, genutzt von api/entity_extraction.py:10 und api/papers/entities.py:140/219 |

### Details (alles nicht-OK)

**1. langchain_llm_service.py — TOT**
- Intendiert: LangChain-basierter Multi-Provider-LLM-Zugang mit Gemini-Support (Docstring Z. 1-3).
- Tatsächlich: Von nichts mehr importiert; Funktionalität doppelt vorhanden. Regelverstöße: hardcodierte Modell-IDs `gemini-2.0-flash-exp`/`gpt-4o-mini` (Z. 113, 136-139), hardcodierter Default-Prompt (Z. 335).
- Nachweis: grep = 0 Treffer außerhalb der Datei.
- Korrektur: Datei löschen. Aufwand: klein.

**2. rag_helpers.py + rag_embedding_helpers.py — TOT (Paar)**
- Intendiert: RAG-Utilities für den früheren `rag_simple.py`-Service (Docstring rag_helpers.py:1-12).
- Tatsächlich: rag/-Package hat eigene Implementierungen; rag_helpers nirgends importiert, rag_embedding_helpers nur von rag_helpers.
- Korrektur: Beide löschen. Aufwand: klein.

**3. embeddings_service.py — TOT**
- Kein Import; Funktion heute von vector_store_mongodb.py bzw. rag/index_manager.py abgedeckt.
- Korrektur: Löschen. Aufwand: klein.

**4. spacy_tagger.py — TOT + Fallback-Stufe FEHLT**
- Intendiert: 2. Stufe der dokumentierten Fallback-Kette GPT→spaCy→Keywords (CLAUDE.md).
- Tatsächlich: Nirgends importiert. llm_service.py:410 springt direkt zu Keyword-Extraktion (Z. 412-426); tag_suggestion_service.py:103 verzichtet auf jeden Fallback.
- Korrektur: (a) spaCy in aktiven Pfad einhängen oder (b) löschen + CLAUDE.md korrigieren. Empfehlung: (b). Aufwand: klein (b) / mittel (a).

**5. tag_suggestion_service.py — FALSCH (aktiver Bug)**
- Intendiert: LLM-Tag-Vorschläge für Tweets über LLM Manager mit Prompts aus prompts_config.json.
- Tatsächlich: `suggest_tags` formatiert Template mit kwargs `tweet_text`, `author`, `max_tags` (Z. 73-77), Template nutzt `{text}`/`{author}` → `KeyError: 'text'` bei jedem Aufruf; Exception geschluckt (Z. 101-104) → immer `[]`. Aufrufer api/tags_mongodb.py:191 bekommt nie LLM-Tags.
- Nachweis: Format-Test reproduziert KeyError; Template-Platzhalter per Regex extrahiert.
- Korrektur: `.replace('{text}', ...)` analog llm_service.py:376-378 oder Platzhalter angleichen; Fehler nicht schlucken. Aufwand: klein.

**6. vector_store_mongodb.py — FALSCH (Interface-Mismatch, toter Build-Pfad)**
- Intendiert: FAISS-Vektorindex über Tag-Konzepte für „Existing Tags"-Vorschläge.
- Tatsächlich: (a) api/tags_mongodb.py:162 ruft `search_similar_tags(query_text=…, k=…, min_similarity=…)` und entpackt Tupel; Klasse bietet nur `search_similar(query, k, threshold) -> List[Dict]` (Z. 187) → AttributeError bei jedem Aufruf → „Existing Tags"-Vorschläge faktisch tot. (b) `build_from_mongodb` (Z. 94) ohne Aufrufer; `build_vector_store.py` existiert nicht mehr → Index aus der App nicht neu baubar. (c) Embedding-Modell hart codiert (Z. 82).
- Korrektur: Adapter-Methode ergänzen oder Aufrufer umstellen; Rebuild-Pfad wiederherstellen; Modell aus llm.json. Aufwand: mittel.

**7. rag/index_manager.py — FALSCH (Regelverstoß Hardcoding)**
- Embedding-Modelle hart codiert: `models/text-embedding-004` (Z. 300, 340), OpenAI-Fallback `text-embedding-ada-002` (Z. 308) — weicht von llm.json ab. Dimensionen 768/1536 hardcodiert (Z. 197, 321). `get_embedding` liefert bei API-Fehler stillschweigend Nullvektor (Z. 320-322) → Index kann unbemerkt korrumpieren.
- Korrektur: Modelle aus llm.json; Fehler nicht als Nullvektor maskieren. Aufwand: mittel.

**8. rag/trend_analysis.py — UNVOLLSTÄNDIG**
- (a) Config-Dateien per relativem Pfad geöffnet (Z. 117/272, 144/300) — bricht wenn cwd nicht `backend/`; (b) `trend_model_config` (Z. 147) und `rag_model_config` (Z. 303) geladen aber nie verwendet; (c) hardcodierte Fallback-Prompts (Z. 131-141, 288-296), nur aktiv wenn Config-Keys fehlen.
- Korrektur: Pfade über `Path(__file__)`, tote Loads entfernen. Aufwand: klein.

**9. llm_service.py — UNVOLLSTÄNDIG (tote Methoden, Doku-Drift)**
- `suggest_tags` (Z. 347) und `_fallback_tag_extraction` (Z. 412) ohne Aufrufer; spaCy-Stufe fehlt. `'o1' in model`-Substring-Check (Z. 152) fragil.
- Korrektur: Tote Methoden entfernen oder konsolidieren; CLAUDE.md aktualisieren. Aufwand: klein.

**Randnotizen:**
- llm_manager.py:227 hardcodiert `gpt-4o-mini` im Not-Fallback bei fehlender litellm_config.yaml — defensiv vertretbar, Regelgrauzone.
- CLAUDE.md verweist für Proportional Blending noch auf `rag_service_concepts.py:312-402`; Code lebt jetzt in `rag/search.py:139-178` (Doku veraltet).
- entity_extraction_service.py lädt `llm.json` (Z. 69-70) in `self.llm_config`, nutzt es nie; Config-Loads cwd-abhängig (Z. 69-76).
- unsicher: Ob die Tag-Suggestion (Befunde 5+6) je funktioniert hat, ist ohne Git-Archäologie nicht feststellbar; beide Fehlerpfade werden still geschluckt.

### Statuszählung
OK: 8, UNVOLLSTÄNDIG: 3, FALSCH: 3, STUB: 0, TOT: 5, FEHLT: 1, Intention unklar: 0
## Bereich: Services — Tags/Konzepte/Trends/Analytics

### Tabelle

| Eintrag | Datei:Zeile | Status | Begründung (1 Satz) |
|---|---|---|---|
| `concept_tag/` Package (`ConceptOnlyTagService` + Lookup-/Tagging-Mixins) | `backend/app/services/concept_tag/service.py:10`, `lookup.py:10`, `tagging.py:9` | OK | Zentraler, aktiv genutzter Tag-Service (~20 Importstellen via Shim, u.a. `app/api/tags_mongodb.py:11`, `app/repositories/__init__.py:20`). |
| `concept_only_tag_service.py` (Shim) | `backend/app/services/concept_only_tag_service.py:6` | OK | Dokumentierter Backwards-Compat-Shim, re-exportiert `ConceptOnlyTagService` aus `concept_tag/`, breit importiert. |
| `mongodb_tag_service.py` — `MongoDBTagService` | `backend/app/services/mongodb_tag_service.py:28` | TOT | Im eigenen Docstring (Z.1–18) explizit als DEPRECATED markiert („preserved for reference only"), 0 Importe im gesamten Backend. |
| `tag_service_mongodb.py` — `TagServiceMongoDB` | `backend/app/services/tag_service_mongodb.py:15` | TOT (zusätzlich kaputt) | 0 Importe; importiert zudem `get_mongodb` aus `app.database.mongodb` (Z.7), das dort nicht existiert (nur `get_client:163`/`get_database:178`) → ImportError. |
| `unified_tag_service.py` — `UnifiedTagService` | `backend/app/services/unified_tag_service.py:32` | TOT (zusätzlich FALSCH/kaputt) | Als DEPRECATED markiert (Z.1–18), 0 Importe, syntaktisch defekt: verwaister Importblock Z.23–27 → `IndentationError`, nicht parsebar (per `ast.parse` verifiziert). |
| `paper_tag_service.py` — `PaperTagService` | `backend/app/services/paper_tag_service.py:13` | TOT (zusätzlich kaputt) | 0 Importe; nutzt SQLAlchemy-Annotation `db: Session` (Z.29,150,170,197) ohne `Session`-Import → NameError beim Import. |
| `orphan_tag_assigner.py` — `OrphanTagAssigner` | `backend/app/services/orphan_tag_assigner.py:15` | TOT (zusätzlich kaputt) | 0 Importe; importiert `app.models.tag_instance` (Z.10), das nicht existiert → ImportError. |
| `slug_normalizer.py` — `SlugNormalizer` | `backend/app/services/slug_normalizer.py:8` | TOT (transitiv) | Einziger Importeur ist das tote/kaputte `unified_tag_service.py:28`; produktiv zwei unabhängige Duplikate der Logik (`concept_tag/lookup.py:59`, `tag_reorganizer_helpers.py:74`). |
| `tag_reorganizer.py` — `TagReorganizer`, `ComprehensiveStrategy`, `LLMStrategy` | `backend/app/services/tag_reorganizer.py:508,49,257` | OK | Genutzt von `app/api/tag_reorganization/utils.py:16-17` und `debug_and_recovery.py:171`; Gemini-Fallback (`_try_gemini_fallback:401`) entspricht CLAUDE.md-Vorgabe. |
| `tag_reorganizer_helpers.py` | `backend/app/services/tag_reorganizer_helpers.py:74ff` | OK | Reine Helper, genutzt von `tag_reorganizer.py:18`. |
| `tag_reorganization_apply_service.py` — `TagReorganizationApplyService` | `backend/app/services/tag_reorganization_apply_service.py:13` | OK | Genutzt von `app/api/tag_reorganization/recovery_and_apply.py:87,142`. |
| `concept_organization_service.py` — `ConceptOrganizationService` | `backend/app/services/concept_organization_service.py:19` | OK (Anmerkung) | Genutzt von `app/api/concept_organization.py:11`; Schönheitsfehler: Test-Funktion `test_organization()` (Z.364) in Produktionsdatei. |
| `anomaly_detection.py` — `AnomalyDetector`, `get_concept_cooccurrence`, `get_concept_activity_by_day` | `backend/app/services/anomaly_detection.py:17,381,503` | OK | In CLAUDE.md dokumentiert und aktiv genutzt (`app/api/analytics_trends/analysis.py:565`, `cooccurrence.py:27`, `network_correlation.py:28`). |
| `trend_analysis/` Package — `TrendAnalysisService`, `VisualizationMixin`, `calculations` | `backend/app/services/trend_analysis/analyzer.py:37`, `visualizations.py:29`, `calculations.py:44ff` | TOT | Keine der `compute_*`-Methoden wird außerhalb des Pakets/Shims importiert; die Dashboard-Endpoints leben parallel in `app/api/analytics_trends/` und nutzen `anomaly_detection` direkt. |
| `trend_analysis_service.py` (Shim) | `backend/app/services/trend_analysis_service.py:6` | TOT | Shim aufs tote Package; keine externen Importe. |
| `analytics/` Package | `backend/app/services/analytics/__init__.py:7ff` | OK | Kohärente Helper-Sammlung; genutzt via Shim von `app/api/analytics_trends/utils.py:48` und `anomaly_detection.py:399`. |
| `analytics_helpers.py` (Shim) | `backend/app/services/analytics_helpers.py:8-46` | OK | Reiner Re-Export-Shim mit dokumentierter Absicht, aktiv genutzt. |
| `article_clustering_service.py` — `ArticleClusteringService` | `backend/app/services/article_clustering_service.py:17` | OK (Anmerkung) | Genutzt von `app/api/article_clustering_mongodb.py:10`; Typannotation `article_id: int` (Z.264) falsch — API übergibt `str`, funktioniert aber. |
| `article_summarizer.py` — `ArticleSummarizer` | `backend/app/services/article_summarizer.py:13` | OK | Genutzt von `app/api/articles/content_processing.py:394` und `summarize_articles.py:14`; LLM via `llm_manager` (regelkonform). |
| `author_service.py` — `AuthorService` | `backend/app/services/author_service.py:15` | OK | Genutzt von `app/api/articles/utils.py:16`, `app/api/article_import/url_import.py:16`, `app/api/authors_management.py:21`. |

### Details (alles nicht-OK)

**1. `mongodb_tag_service.py` — TOT**: 399 Zeilen nirgends importierter Code; überlappt vollständig mit `ConceptOnlyTagService`. Korrektur: Löschen. Aufwand: klein.

**2. `tag_service_mongodb.py` — TOT (+ ImportError)**: 0 Importeure; würde beim Import crashen (`get_mongodb` existiert nicht in `app/database/mongodb.py:163,178`); nutzt falsche Collection `self.mongo.concepts` statt `tag_concepts_v2`. Intention teils unklar. Korrektur: Löschen. Aufwand: klein.

**3. `unified_tag_service.py` — TOT + defekt**: Nicht parsebar — verwaister Importblock Z.23–27 → `IndentationError` (per `ast.parse` verifiziert); 0 Importeure. CLAUDE.md-Abschnitt „UnifiedTagService" beschreibt nicht mehr existenten Ist-Zustand. Korrektur: Löschen + CLAUDE.md als historisch markieren. Aufwand: klein.

**4. `paper_tag_service.py` — TOT (+ NameError)**: SQLite-Ära-Code, `db: Session` ohne Import (Z.29,150,170,197); 0 Importeure. Korrektur: Löschen. Aufwand: klein.

**5. `orphan_tag_assigner.py` — TOT (+ ImportError)**: Importiert nicht existentes `app.models.tag_instance` (Z.10); Orphan-Konzept laut `concept_tag/service.py:3` abgeschafft. Korrektur: Löschen. Aufwand: klein.

**6. `slug_normalizer.py` — TOT (transitiv)**: Nur vom defekten `unified_tag_service.py:28` importiert; produktiv zwei Duplikate der Logik. Korrektur: löschen oder als einzige Slug-Quelle konsolidieren. Aufwand: klein/mittel.

**7. `trend_analysis/` Package + Shim — TOT**: Exakt die in CLAUDE.md beschriebenen Dashboard-Berechnungen als Refactor-Extrakt, aber die realen Endpoints in `app/api/analytics_trends/` rufen `anomaly_detection` direkt → Fachlogik doppelt. unsicher: welche Implementierung die „gewollte" ist, ist nirgends dokumentiert. Korrektur: löschen ODER API darauf umstellen. Aufwand: klein (löschen) / groß (Umstellung).

**Anmerkungen zu OK-Einträgen:**
- `article_clustering_service.py:264`: falsche Typannotation; unsicher: API liest embedded `articles.tags` (`article_clustering_mongodb.py:47-49`) statt `tag_instances` — Datenbasis des Clusterings evtl. leer/veraltet.
- `concept_organization_service.py:364`: Ad-hoc-Test in Produktionsdatei.

### Statuszählung
OK: 12, UNVOLLSTÄNDIG: 0, FALSCH: 0, STUB: 0, TOT: 8, FEHLT: 0, Intention unklar: 2 (in TOT enthalten)

**Kernbefund:** Fünf Tag-Service-Implementierungen, nur `concept_tag/` (+ Shim) lebt. Vier tote plus `orphan_tag_assigner`, `slug_normalizer` und `trend_analysis/`-Paket (~2.400 LOC) gefahrlos löschbar — vier davon würden beim Import crashen.
## Bereich: Services — Paper/PDF/Book-Pipeline & Import/Konverter

### Tabelle

| Eintrag | Datei:Zeile | Status | Begründung (1 Satz) |
|---|---|---|---|
| PDFProcessorService | pdf_processor_service.py:45 | OK | Zentraler Dispatcher (Marker/MinerU/CLI/Fallback), breit genutzt. |
| AsyncPDFProcessor | async_pdf_processor.py:22 | OK | Genutzt von pdf_processor_service.py:11+383; unsicher: `process_pdf_async` (49) ohne externen Aufrufer. |
| pdf_extraction_helpers | pdf_extraction_helpers.py:16-274 | OK | Alle 7 Funktionen dispatcht; MinerU-Callback nutzt BACKEND_PORT (49-50). |
| PDFExportService | pdf_export_service.py:26 | OK | 5 Aufrufstellen in api/pdf_export.py. |
| BookProcessorService | book_processor_service.py:21 | OK | Timeouts 21600s/18000s = dokumentierte 6h/5h; EPUB-Pfad vorhanden (243). |
| GROBIDService | grobid_service.py:22 | OK | Externe HF-URL wie CLAUDE.md. |
| GROBIDService._process_citations | grobid_service.py:177 | STUB | Dokumentierter Platzhalter („just return a placeholder here", 181) — absichtlich. |
| grobid_helpers | grobid_helpers.py:19-371 | OK | Vollständig delegiert genutzt. |
| ImageManager | image_manager.py:20 | OK | Genutzt (pdf_processor, marker_server, mineru_server). |
| ACLAnthologyService | acl_anthology_service.py:16 | OK | `_parse_publication_date` (422) passt zur published_date-Standardisierung. |
| ACMService | acm_service.py:17 | OK | 403/401-Behandlung (379-386) wie dokumentiert. |
| ArXivImportService | arxiv_import_service.py:18 | OK | `extract_arxiv_id` (40) ist der dokumentierte Fix. |
| DBLPService + dblp_helpers | dblp_service.py:27 | OK | Genutzt. |
| JAIRService | jair_service.py:18 | OK | Genutzt. |
| OpenReviewService | openreview_service.py:16 | OK | Inkl. Scrape-Fallback (199). |
| ReadabilityService | readability_service.py:23 | OK | Genutzt (papers/utils.py:38, books/utils.py:36). |
| AggressiveHTMLCleaner | aggressive_html_cleaner.py:10 | OK | Genutzt (substack_parser, substack_content_cleaners). |
| ForwardedEmailCleaner | forwarded_email_cleaner.py:10 | OK | Klasse aktiv genutzt; nur Modulfunktion `clean_forwarded_email` (273) ohne Aufrufer. |
| TwitterLookupService | twitter_lookup_service.py:26 | OK | Genutzt. |
| PaperAnalysisService | paper_analysis_service.py:15 | FALSCH | Einziger Aufrufer ruft nicht existente Methode `analyze_paper` auf (acl_anthology.py:327); DB-Methoden nutzen SQLAlchemy auf gelöschten Models (282, 327). |
| PaperService | paper_service.py:16 | TOT | Keine Importe; `import PyPDF2` (10) → ModuleNotFoundError — Vor-Marker-Pipeline. |
| PaperRepositoryService | paper_repository_service.py:25 | TOT | `from ..models.papers import` (15) → ModuleNotFoundError; keine Importeure. |
| PaperAuthorExtractionService | paper_author_extraction_service.py:13 | TOT | Nirgends importiert; Funktionalität inline in api/papers/affiliations.py:84-134 dupliziert. |
| document_converter/ (Package) | document_converter/converter.py:63 | TOT | Einziger App-Aufrufer ist `clean_forwarded_email()` (289), das selbst keine Aufrufer hat. |
| DocumentConverter.markdown_to_pdf (ReportLab) | document_converter/converter.py:437 | STUB | `raise NotImplementedError`. |
| PlaywrightConverter | playwright_converter.py:14 | TOT | Nur vom toten document_converter importiert; eingebettetes „Readability.js" (97) ist verstümmelter Stub → parse() liefert nie Artikel. |
| PlaywrightSubstackConverter (v2) | playwright_converter_v2.py:14 | TOT | Null Importe — Verlierer des Duplikat-Paars. |
| ImagePreservingConverter / HybridConverter | image_preserving_converter.py:11/141 | TOT | Null Importe. |
| ExportService | export_service.py:12 | TOT | `db: Session` (15) ohne Import → NameError; durch PDFExportService ersetzt. |
| URLArticleImporter | url_article_importer.py:13 | TOT | Nur migrations/completed/; `markdownify` fehlt (10), SQLAlchemy-Typen undefiniert (16, 415). |
| AuthenticatedURLImporter | url_article_importer_auth.py:13 | TOT | Nahezu vollständige Kopie von url_article_importer; gleicher Import-Bruch — beide Seiten des Duplikat-Paars tot. |
| curl_parser | curl_parser.py:8 | TOT | Null Importe. |
| SubstackAuthService | substack_auth_service.py:12 | TOT | Nur migrations/completed/-Einmal-Skripte. |

### Details — Kernpunkte

**PaperAnalysisService — FALSCH**: `generate_analysis` (71) nur mit übergebenem Content nutzbar; DB-Fallback `db.query(Paper)` mit nicht importiertem `Paper` → NameError (~107); `save_analysis_to_db` (282)/`get_saved_analyses` (327) importieren nicht existentes `app.models.papers`. Einziger Aufrufer acl_anthology.py:325-327 ruft nicht existente Methode `analyze_paper` — AttributeError vom try/except (329-330) geschluckt → ACL-Nachbearbeitungs-Analyse läuft nie. Korrektur: toten Aufruf entfernen + Service löschen oder portieren. Aufwand: klein/mittel.

**PaperService, PaperRepositoryService, ExportService, URLArticleImporter(+_auth), curl_parser, SubstackAuthService, image_preserving_converter, playwright_converter_v2 — TOT**: teils nicht importierbar (fehlende Pakete/Models). Korrektur: löschen. Aufwand: je klein.

**PaperAuthorExtractionService — TOT (Duplikat)**: produktiver Endpoint implementiert Extraktion inline (affiliations.py:84-134). Korrektur: löschen oder Endpoint darauf umstellen (Feature-Policy). Aufwand: klein.

**document_converter/ + PlaywrightConverter — TOT (faktisch)**: einziger App-Pfad über ungenutzte `clean_forwarded_email()`; substack_parser nutzt bewusst html2text direkt (435-447); Trafilatura nicht installiert; ReportLab-Zweig NotImplementedError. PlaywrightConverter hat zudem defektes eingebettetes Readability.js (97, 164-179). Korrektur: Kettenlöschung oder bewusst als Bibliothek dokumentieren. Aufwand: klein-mittel.

**GROBID _process_citations — STUB (dokumentiert, kein Handlungsbedarf)**.

**Randnotiz:** `forwarded_email_cleaner.clean_forwarded_email` (273) ungenutzt — bei Aufräumen mit entfernen. `async_pdf_processor.process_pdf_async` (49) ohne gefundenen Aufrufer (unsicher).

### Statuszählung
OK: 19 · UNVOLLSTÄNDIG: 0 · FALSCH: 1 · STUB: 2 · TOT: 12 · FEHLT: 0 · Intention unklar: 0

**Kernbefunde:** (1) Zwölf Dateien (~150 KB) toter Code, sechs nicht importierbar. (2) Laufzeit-Bug: acl_anthology.py:327 ruft nicht existente Methode — automatische Analyse nach ACL-Import läuft ins Leere. (3) Duplikat-Paare aufgelöst: playwright_converter v1 referenziert (über tote Kette), v2 komplett tot; url_article_importer + _auth beide tot und kaputt.
## Bereich: Collectors, CLI-Skripte, Marker/MinerU-Services

### Tabelle

| Eintrag | Datei:Zeile | Status | Begründung (1 Satz) |
|---|---|---|---|
| `authenticate_gmail()` | collectors/gmail_auth.py:14 | OK | Von GmailSubstackCollector genutzt; relative Default-Pfade CWD-abhängig, aber funktional. |
| `GmailSubstackCollector` + CLI | collectors/gmail_substack_collector.py:20,312 | OK | Dokumentierter CLI-Collector; Footer-Removal (218, 281) und Forwarded-Handling wie dokumentiert. |
| `SelectiveGmailCollector` + CLI | collectors/selective_gmail_collector.py:14,141 | TOT | Nur von migrations/completed/ referenziert; Funktionalität durch `--forwarded` abgedeckt. |
| Playwright-CLI | collectors/playwright_article_collector.py:312 | OK | Vollständige CLI über dem aktiv genutzten Package. |
| `playwright_collector/` Package | collectors/playwright_collector/__init__.py:14-17 | OK | Aktiv genutzt von articles/content_processing.py:490 und article_import/conversion.py:91,129,193. |
| `RedditCollector` + Standalone | collectors/reddit_collector.py:17,286 | OK | Aktiv über API; Schönheitsfehler: relativer Config-Pfad (52) CWD-abhängig. |
| `remove_substack_footer` (2 Kopien) | collectors/substack_content_cleaners.py:18 vs. clean_substack_footers.py:16 | UNVOLLSTÄNDIG | Zwei divergierende Implementierungen: Batch-Skript hat Adress-Heuristik (78-81) + Trailing-Cleanup (91-96), die der Collector-Pfad bei Neuimporten nicht anwendet. |
| `SubstackParser` | collectors/substack_parser.py:25 | OK | Kern des Gmail-Collectors; DEF-007 als Known Issue dokumentiert. |
| `TwitterCollector` | collectors/twitter_collector.py:18 | TOT | SQLAlchemy-Leiche: `Session` nicht importiert → NameError (19); Importkette (smart_startup_collector → background_tasks → scheduler) selbst nirgends eingebunden. |
| `TwitterCollectorWithRetweets` | collectors/twitter_collector_with_retweets.py:13 | TOT | Nirgends importiert; gleiche SQLAlchemy-Defekte (14, 192, 228). |
| `TwscrapeCollector` | collectors/twscrape_collector.py:19 | TOT | Nirgends importiert, `twscrape` fehlt in requirements.txt; zusätzlich kaputt (25, 91, 226). |
| `tweet_collector_service.py` | tweet_collector_service.py:1086 | OK | Der aktive Collector (start_stt.sh:451); Basic Account Mode (175-197), Retweet-Fix (674-676, 705-719), `--check-rate-limit` (1189) wie dokumentiert. |
| `book_processing_worker.py` | book_processing_worker.py:24 | UNVOLLSTÄNDIG | Implementierung vollständig, aber kein Startskript startet den Worker (grep start_stt.sh/scripts leer) → via /api/books/{id}/process enqueued Jobs bleiben liegen. |
| `check_collection_state.py` | check_collection_state.py:15 | OK | Essentielles MongoDB-Skript (DEBT-001). |
| `check_tag_consistency.py` | check_tag_consistency.py:218 | OK | CLI entspricht Doku, arbeitet auf v2-Collections. |
| `clean_substack_footers.py` | clean_substack_footers.py:237 | OK | Dokumentiertes CLI; Duplikat-Drift siehe oben. |
| `fix_previews.py` | fix_previews.py:77 | OK | DEF-006-Fix; Einschränkung: Autorenliste hartkodiert (82) statt aus forwarded_authors.json. |
| `migrate_tag_instances_dates.py` | migrate_tag_instances_dates.py:17 | TOT | Erledigtes One-off (MEMORY.md 2026-03-07); Kandidat für migrations/completed/. |
| `monitor_collection.py` | monitor_collection.py:148 | UNVOLLSTÄNDIG | CLAUDE.md verspricht „Updates every 5 seconds", tatsächlich einmalige Ausführung ohne Loop. |
| `rebuild_rag_index.py` | rebuild_rag_index.py:50 | FALSCH | `db.close()` auf nie definierter Variable → NameError am Ende jedes Laufs; async Build (27) gefährdet. |
| `update_rag_index.py` | update_rag_index.py:17,20,64 | FALSCH | Port 8000 hartkodiert (= Honcho-Docker seit 8088-Migration); Fallback `build_rag_index.py` (45) existiert nicht; `update_via_api` gibt bei non-200 `True` zurück (29-36). |
| `run.py` | run.py:6 | FALSCH | `API_PORT` Default 8000 (app/config.py:42) — Honcho-Kollision; Banner bewirbt tote Features. |
| `summarize_articles.py` | summarize_articles.py:192 | OK | Dokumentiertes CLI; Bulk-Writes korrekt. |
| `marker_server.py` (grob) | marker_service/marker_server.py:84,592 | OK | Alle dokumentierten Features vorhanden: TQDM-Parsing (181-254), PTY-Streaming (255), psutil-Health (134), Heartbeat/Throttling (275-331), /kill. |
| `mineru_server.py` /health, /convert (grob) | mineru_service/mineru_server.py:112,127 | OK | Basiskonvertierung mit Timeout, Callback, Bildbehandlung. |
| MinerU Progress-Feature (PTY/psutil/TQDM) | mineru_service/mineru_server.py:199-238 | FEHLT | CLAUDE.md (28.01.2026) behauptet `_strip_ansi`, `_get_process_health`, `_parse_mineru_progress`, `_cli_run_streaming` implementiert — keine existiert; nur Keyword-Matching ohne PTY/psutil/Prozente/Heartbeat. |
| `/convert_advanced` | mineru_service/mineru_server.py:512 | STUB | Redirect auf /convert (534), ignoriert Optionen, verliert callback_url/paper_id; kein Aufrufer. |

### Details — Kernpunkte

**SelectiveGmailCollector — TOT**: nur archiviertes Migrationsskript; Filterlogik doppelt in gmail_substack_collector.py:377-420. Löschen/archivieren. Aufwand: klein.

**twitter_collector / _with_retweets / twscrape — TOT (+kaputt)**: SQLAlchemy-Ära, nicht importierbar; tote Import-Kette `app/smart_startup_collector.py` → `app/background_tasks.py` → `app/scheduler.py` (+ async_startup_collector.py, startup_collector.py, ~600 LOC) hängt nur an twitter_collector und ist nirgends eingebunden (kein Einstiegspunkt von main.py). Alle entfernen. Aufwand: klein.

**remove_substack_footer Duplikat-Drift — UNVOLLSTÄNDIG**: neu gesammelte Artikel schwächer bereinigt als nachträglich. Korrektur: Skript auf substack_content_cleaners umstellen + Heuristik einpflegen. Aufwand: klein.

**book_processing_worker — UNVOLLSTÄNDIG**: korrekt implementiert (atomarer Job-Claim 59-71), aber kein Startmechanismus in start_stt.sh/scripts/CLAUDE.md → Queue ohne Konsument. Korrektur: in start/stop_stt.sh aufnehmen oder Endpoint auf BackgroundTasks. Aufwand: mittel.

**monitor_collection — UNVOLLSTÄNDIG**: Einmal-Snapshot statt 5s-Loop. Aufwand: klein.

**rebuild_rag_index — FALSCH**: NameError `db.close()` (50) bei jedem Lauf; Index wird vermutlich nie fertig gebaut. Aufwand: klein.

**update_rag_index — FALSCH**: Port 8000 → trifft Honcho; Fallback-Skript fehlt; Rückgabewert-Bug. Löschen oder fixen. Aufwand: klein.

**run.py — FALSCH**: Port 8000 (Honcho-Kollision, exakt das dokumentierte Migrationsproblem); nur von backend/clean_start.sh:54 genutzt. Aufwand: klein.

**MinerU Progress — FEHLT**: dokumentiertes Feature („COMPLETE") nicht implementiert — UI erhält keine CPU/RAM/Prozent-Werte von MinerU. Korrektur: Marker-Implementierung portieren oder Doku korrigieren. Aufwand: mittel.

**/convert_advanced — STUB**: entfernen. Aufwand: klein.

### Statuszählung
**OK: 14, UNVOLLSTÄNDIG: 3, FALSCH: 3, STUB: 1, TOT: 5, FEHLT: 1, Intention unklar: 0** (28 Einträge)

Zusatzbefund: tote Import-Kette app/smart_startup_collector.py → app/background_tasks.py → app/scheduler.py (+ async_startup_collector.py, startup_collector.py, ~600 LOC) sollte mit entfernt werden.
## Bereich: Frontend

Analysebasis: Import-Reachability ab `frontend/src/main.tsx` (267 TS/TSX-Dateien, 249 erreichbar), Endpunkt-Abgleich gegen `backend/app/main.py:173-209`.

### View-Routing-Tabelle (ModernApp.tsx:39-146, ViewTypes ModernNavigation.tsx:37-80)

| View-Type | Komponente | Status |
|---|---|---|
| dashboard | DashboardHome (:42) | OK |
| statistics | StatisticsDashboard (:44) | OK |
| rag-search | RAGSearchModern (:46) | OK |
| twitter-faceted | FacetedTweetsDashboardModern (:49) | OK |
| twitter-deck | TweetDeckView (:51) | OK |
| twitter-media | TwitterMediaGalleryModern (:53) | OK |
| twitter-trends | TrendAnalysisOverview (:55) | OK |
| twitter-users | UserTrendAnalysisModern (:57) | OK |
| twitter-charts | TrendVisualizationModern (:59) | OK |
| twitter-summary | SummarizationModern (:61) | OK |
| twitter-accounts | TwitterAccountManager (:63) | OK |
| articles-faceted | FacetedArticlesDashboardModern (:66) | UNVOLLSTÄNDIG (DEF-001) |
| articles-trends | SubstackTrendsModern (:73) | OK |
| articles-charts | TrendVisualizationModern (:77) | OK |
| articles-clustering | ArticleClusteringDashboard (:79) | OK |
| author-management | AuthorManagementModern (:82) | OK (unsicher: „placeholder"-Modal) |
| author-analytics | inline „Coming Soon" (:84) | STUB |
| author-merge | inline „Coming Soon" (:86) | STUB |
| reddit-faceted | FacetedRedditDashboardModern (:89) | OK |
| reddit-trends | inline „Coming soon" (:90-103) | STUB |
| papers-dashboard | FacetedPapersDashboard (:106) | OK |
| papers-references | ReferenceManager (:108) | OK |
| reviews-dashboard | FacetedPapersDashboard paperType="review" (:110) | OK |
| books-dashboard | FacetedBooksDashboard (:113) | OK |
| books-analysis | inline „Coming soon" + TODO (:114-122) | STUB |
| analysis-unified / trend-dashboard | TrendDashboardMain (:124-126) | UNVOLLSTÄNDIG (onConceptClick nur console.log, :126) |
| analysis-compare | TrendVisualizationModern (:128) | OK |
| analysis-clustering | TrendAnalysisModern (:130) | OK |
| topic-explorer | TopicExplorerModern (:132) | OK |
| concept-management | ConceptManagementCenter (:135) | FALSCH (5 tote Endpunkte) |
| concept-graph | ConceptGraph (:137) | OK |
| tags-organisation (Legacy) | TagOntologyModern (:140) | FALSCH (mehrere tote Endpunkte) |
| concept-organizer (Legacy) | ConceptOrganizer (:142) | OK (nutzt korrekt /api/concepts/organization/*) |

### Tabelle auffälliger Komponenten
(~209 von 226 Komponentendateien (ohne ui/) erreichbar und ohne Befund)

| Eintrag | Datei:Zeile | Status | Begründung |
|---|---|---|---|
| ConceptManagementCenter Organize/Batch | concept-management/useConceptManagement.ts:72,83,102,171,206 | FALSCH | 5 Aufrufe auf `/api/concepts/{unorganized,organization-stats,suggest-organization,apply-organization,batch-reorganize}` — Backend-Datei in 49b0c53d gelöscht; heutige Routen unter `/api/concepts/organization/*` → 404. |
| TagOntologyModern Import/Export/Validate | tag-ontology/TagOntologyModern.tsx:209,242,267 | FALSCH | `/api/tags/io/*` existiert nicht mehr (entfernt in 8d2a92fe). |
| TagOntologyModern Synonym | TagOntologyModern.tsx:185 | FALSCH | POST `/concept/{id}/synonym` — Backend-Route heißt `/alias`. |
| TagOntologyModern Tag-Import | TagOntologyModern.tsx:301 | FEHLT | `/api/ontology/import-existing-tags` existiert nicht. |
| OntologyAISuggestions | OntologyAISuggestions.tsx:46,58,73,95,195 | FALSCH | Alle 4 `/api/ontology/ai/*`-Endpunkte entfernt (8d2a92fe). |
| DEF-001 Optimistic UI | Dispatch: article-viewer/ArticleViewerModern.tsx:179; Listener nur in TOTER substack/FacetedSubstackDashboardModern.tsx:109 | FALSCH | Live-Dashboard articles/FacetedArticlesDashboardModern.tsx registriert keinen Listener — Event läuft ins Leere; erklärt DEF-001. |
| Paper-Viewer Such-Tab | PaperViewer/PaperTabsContent.tsx:365-379 | STUB | Suchfeld ohne Handler, „Search functionality coming soon". |
| UnifiedImportDialog DBLP | UnifiedImportDialog.tsx:74 | UNVOLLSTÄNDIG | DBLP als comingSoon deaktiviert, obwohl DBLPSearchModal + Backend existieren. |
| 4 Stub-Views | ModernApp.tsx:84,86,90-103,114-122 | STUB | author-analytics, author-merge, reddit-trends, books-analysis nur „Coming Soon". |
| AuthorManagementModern Detail-Modal | AuthorManagementModern.tsx:402 | Intention unklar | Kommentar „(placeholder)", rendert aber echte Daten. |
| components/ArticleViewerModern.tsx | ganze Datei | TOT | Live-Version ist article-viewer/ArticleViewerModern.tsx. |
| components/TagReorganizer.tsx | ganze Datei | TOT | Ersetzt durch TagReorganizerPersistent.tsx. |
| components/substack/* (5 Dateien) | — | TOT | Kompletter Ordner unerreichbar; enthält den einzigen DEF-001-Listener. |
| Barrel-Dateien PaperViewer/books/tweets index.ts | — | TOT | Nirgends importiert. |
| hooks/useTagConcepts.ts | :15 | TOT | Unerreichbar; zeigt auf nie gemountetes `/api/tags-concept`. |
| hooks/useDraggable.tsx | — | TOT | Nirgends importiert. |
| pages/OntologyGraphPage.tsx | — | TOT | Kein Router bindet pages/ ein. |
| types/tagConcept.ts, types/tagConceptV2.ts | — | TOT | Nur von toten Dateien referenziert. |

### Details — Kernpunkte

**1. ConceptManagementCenter — FALSCH**: 5 der 12 HTTP-Aufrufe treffen in 49b0c53d gelöschte Pfade; aktuelle Routen `/api/concepts/organization/{unorganized,stats,organize,apply-organization/{id},organize-batch}` (concept_organization.py:44-193); Legacy-ConceptOrganizer.tsx:80-196 macht es richtig. Korrektur: Pfade umstellen. Aufwand: klein.

**2. TagOntologyModern + OntologyAISuggestions — FALSCH/FEHLT**: io/ai-Endpunkte entfernt, synonym→alias, import-existing-tags fehlt. Da View als „Legacy (to be removed)" markiert (ModernApp.tsx:138): entfernen oder konsolidieren. Aufwand: mittel.

**3. DEF-001 — FALSCH, Ursache gefunden**: Event `articleViewerClosed` wird dispatcht (article-viewer/ArticleViewerModern.tsx:179), einziger Listener liegt in toter substack/-Datei (:109); Live-Dashboard hat keinen Listener. Korrektur: Listener in articles/FacetedArticlesDashboardModern.tsx registrieren (oder onClose-Prop), toten substack/-Ordner löschen. Aufwand: klein.

**4. 4 Stub-Views** in Navigation beworben (ModernNavigation.tsx:207-217,230-235,272-277), rendern „Coming Soon". Implementieren (groß) oder Navigationspunkte entfernen (klein).

**5. Paper-Such-Tab STUB** (PaperTabsContent.tsx:365-379). Aufwand: mittel.

**6. UnifiedImportDialog DBLP UNVOLLSTÄNDIG** (:74): aktivieren. Aufwand: klein.

**7. Trend-Dashboard onConceptClick** nur console.log (ModernApp.tsx:126). Aufwand: klein.

**Abgleich Defekte:** DEF-001 bestätigt offen (Ursache identifiziert). DEF-002 tatsächlich behoben (TopicFiltersPanel.tsx:74-75,150) — CLAUDE.md-Angabe „temporarily disabled" veraltet. ReactMarkdown v9: keine inline-Prop-Reste — OK.

### Statuszählung
OK: ~209 Dateien ohne Befund · UNVOLLSTÄNDIG: 3 · FALSCH: 4 · STUB: 5 · TOT: 15 Dateien · FEHLT: 1 · Intention unklar: 1
