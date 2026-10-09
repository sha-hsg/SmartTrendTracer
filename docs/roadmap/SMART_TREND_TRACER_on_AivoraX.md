**Zusammenfassung:** Um SmartTrendTracer als FlowScript-/AivoraX-Lösung zu betreiben, müssen Dateningest, Trend-Analyse und Multi-Channel-UX als lose gekoppelte Building Blocks abgebildet werden. Diese Roadmap identifiziert wiederverwendbare AivoraX-Komponenten, notwendige Erweiterungen und einen Phasenplan, um Social- und Langform-Content-Tracing innerhalb der Plattform zu realisieren – nach Einsteins Maxime: so einfach wie möglich, aber nicht einfacher.
**Inhalt:**
- Zielbild & Kontext
- Mapping bestehender AivoraX-Bausteine
- Lücken bei Tools & Adaptern (Composable Erweiterungen)
- Notwendige FlowScript-Erweiterungen
- Infrastruktur & Philosophie-Erweiterungen
- UX/UI-Anforderungen
- Roadmap (Phasen 0–3)
- Risiken
- Nächste Schritte

# Zielbild & Kontext
SmartTrendTracer vereint Twitter/X, Substack, Paper- und Buchquellen, normalisiert Inhalte, reichert sie mit Konzept-Tags an und stellt Trends in einer interaktiven UI dar. In AivoraX sollen diese Funktionen als FlowScript-Flows, modularisierte Adapter und Auditable Artefakte umgesetzt werden. Das Ergebnis: wiederholbare Pipelines (Ingest → Analyse → Publikation), observierbar über AivoraX Traces, steuerbar via Approvals und konsumierbar im AGUI.

# Mapping bestehender AivoraX-Bausteine
| Bedarf aus SmartTrendTracer | Wiederverwendbare AivoraX-Komponenten | Bemerkung |
| --- | --- | --- |
| HTTP/Social API Calls | `http` Adapter, `function` Runner, `json_schema_validate` Guard | Für einfache REST-Aufrufe (z. B. Twitter API v2) nutzbar, Rate-Limits via Flow-Guards steuerbar |
| Newsletter/Gmail Intake | `gmail` Adapter, `load_secret`, `structured_scrape` | Forwarding + Parsing kann auf bestehenden Mail/HTML-Funktionalitäten aufsetzen |
| LLM-basierte Zusammenfassungen | `llm`, `doc_qa`, `load_prompt` | Verwendung für Trendtexte, Newsletter-Highlights, Zusammenfassungen |
| PDF/EPUB Verarbeitung (Paper/Bücher) | `pdf_extract_tables`, `functions_examples` (Menü POC) als Vorlage | Grundlogik für Dokumentverarbeitung vorhanden, erweiterbar |
| Artefakt-Speicherung | `file_writer`, `s3` Adapter, Trace-Artefakte | Speicherung normalisierter Dokumente, Embeddings, JSON-Exports |
| Human-in-the-Loop QA | `approval` Adapter, `scripts/approvals.py`, AGUI Approvals | Freigaben für Tagging-Korrekturen oder veröffentlichte Trends |
| Reporting/Notification | `gmail`, `slack/email` Adapter, `load_prompt` | Versand von Trendreports oder Alerts |

# Lücken bei Tools & Adaptern (Composable Erweiterungen)
| Kategorie | Neuer Building Block | Verantwortung & Schnittstelle | Hinweis zur Modularität |
| --- | --- | --- | --- |
| Social Media Ingest | `twitter_ingest` (function adapter) | Nimmt Query + Auth, liefert paginierte Tweet-Batches als JSON; optional Rate-Limit-Feedback im Result | Reine Datenerfassung, ohne Persistenz – kann auch für Mastodon/Bluesky wiederverwendet werden |
| Newsletter/Feed Fetch | `rss_fetcher`, `substack_parser` | HTTP + HTML → strukturierte Artikelobjekte, trennt network von parsing | Konsumiert generische RSS/Atom, Substack-spezifische Logik als eigenständiges Parsing-Modul |
| Research/Buch Verarbeitung | `document_ingest` (multi-format) + `epub_splitter`, `pdf_chunker` | Legt Artefakte (Text-Chunks, TOC) ab, gibt Metadaten zurück | Bausteine sollen Formate erkennen und spezielle Worker triggern |
| Concept Tagging | `concept_assigner` | Input: Text/Metadata; Output: Normalisierte Tags, Confidence Scores | Tag-Hierarchie per Konfiguration (`prompts/concepts.yaml`) |
| Trend Aggregation | `trend_aggregator` | Aggregiert Items nach Konzept, Zeitraum, Source; liefert Stats | Setzt nur auf übergebenen Daten, keine direkte DB |
| Embedding/RAG | `embedding_encoder`, `vector_store_writer` | Abstrakte Schnittstelle, Provider-agnostisch | Wiederverwendbar für andere Projekte mit Retrievalbedarf |
| Storage Integration | `mongodb_writer`, `mongodb_query` | CRUD-Adapter mit Schema-Validation | Für Projekte ohne DB → optional, aber hier nötig |

# Notwendige FlowScript-Erweiterungen
- **Event-Streams & Iterationen:** Mehrstufige Ingest-Flows benötigen komfortable `for item in collection`-Syntax sowie Batch-Verarbeitung mit Retry/Backoff. Bestehendes Backlog „Iteration über Collections“ priorisieren.
- **Cron/Scheduler Guards:** native `schedule { cron: "*/30 * * * *" }`-Angaben für Social-Poller inkl. Pause/Resume Hooks.
- **Artefakt-Metadaten:** Erweiterung von `emit`/`store` um Labels (z. B. Source, Model-Version) erleichtert Trend-Historisierung.
- **Structured Prompts Registry:** FlowScript-Hilfe für referenzierte Prompt-Bausteine (`prompt_id`) zur Wiederverwendung im Trend-Kontext.

# Infrastruktur & Philosophie-Erweiterungen
- **Datenhaltung:** Anbindung externer Datenbanken (MongoDB) via Secrets + RBAC; optional abstrahierte Persistence-Layer in Artefakt-Store.
- **Worker-Scaling:** Long-running Jobs (PDF/EPUB Processing) benötigen queue-basierte Worker (z. B. FlowScript → Celery/Arq Trigger) mit Trace-Verknüpfung.
- **Observability:** Token-/Cost-Metriken + Custom Metrics (Tweets pro Lauf, Dokumente pro Stunde) in Trace-Erweiterungen. Budget-Guards per Flow.
- **Compliance & Provenance:** Einbettung von Source-Metadaten (Tweet-ID, Newsletter-URL) in Traces, um Auditbarkeit sicherzustellen.
- **Einstein-Maxime:** Jede neue Erweiterung (Adapter/DB) strikt modular halten; Basiskomponenten klein, kombinierbar; keine monolithischen „do-everything“-Jobs.

# UX/UI-Anforderungen
- **AGUI Trend Dashboard:** Next.js Modul, das Artefakte aus Flows konsumiert (via `/artifacts/{id}`), Filter (Quelle, Zeitraum, Konzept) anbietet und Trend-Charts zeigt.
- **Content Viewer:** Reuse-Pattern aus SwissMap Roadmap (Leaflet adaptieren) für Dokument-Viewer: Virtualized Render, Tag-Hervorhebung, Approvals-Trigger.
- **Approvals & QA:** UI-Komponente für Tagging-Rezension, inklusive Diff-Ansicht (alter vs. neuer Tag-Satz) und Notizfeld.
- **Notifications:** Banner/Inbox für neue Trendpakete, inkl. Link zur Trace/Artefakt-Seite.

# Roadmap (Phasen 0–3)
## Phase 0 – Analyse & Quick Prototype (bis Nov 2025)
- **Artefakt-Definition:** Dokumentiere Schema für Tweets, Newsletter, Paper-Chunks in `docs/standards/smarttrendtracer.md`.
- **PoC-Flows:** `ingest_tweets_basic.flow` (Twitter API Stub), `ingest_newsletter_basic.flow` (Gmail Parser). Artefakte in `runtime/data/artifacts/` ablegen.
- **Adapter Skeletons:** Implementiere `twitter_ingest`, `rss_fetcher`, `concept_assigner` als wrappers mit klaren Input/Output (Dict → Dict/List). Tests via pytest + Golden Samples.

## Phase 1 – Kernpipeline (Q1 2026)
- **Ingest Orchestrierung:** Zeitgesteuerte Flows (Scheduler) für Tweets/Substack/Papers. Verwende Guards für Rate-Limit & Error Handling. Artefakte im S3/MinIO-Store versionieren.
- **Tagging & Trend Aggregation:** Verkette `concept_assigner` → `trend_aggregator` → `embedding_encoder`. Speichere Ergebnisse als Artefakt + optional MongoDB (`mongodb_writer`).
- **Human QA:** Flows für Konzept-Review (`approval` + Diff). Approvals über AGUI/CLI.
- **Observability:** Trace-Felder erweitern (Docs/Flow Updates) um Source, Item-Count, Kosten.

## Phase 2 – Insights & UX (Q2 2026)
- **AGUI Dashboards:** Implementiere „Trend Explorer“ (Filters, Charts, Table), „Content Viewer“ (Doc, Highlights). Daten via `/artifacts` + optional `/queries` (Mongo).
- **Reporting Flows:** `publish_trend_digest.flow` generiert HTML/PDF-Reports (Jinja2) und versendet via `gmail/slack` Adapter.
- **RAG Endpoint:** Flow `build_trend_index.flow` erstellt Vektor-Index (via `vector_store_writer`), AGUI bietet Q&A (LLM Adapter mit retrieval).
- **Compliance Hooks:** GDPR-safe anonymization, Source-Consent Alerts (Guard, Approvals).

## Phase 3 – Skalierung & Integrationen (Q3 2026)
- **Multi-Source Expansion:** Wiederverwendbare Ingest-Adapter für Mastodon/LinkedIn; Parameterisierung via FlowContext.
- **Auto-Triage & Alerts:** Flows listen Anomalien (z. B. Trend-Sprünge) und triggern Approvals/Notifications.
- **Deployment Bundles:** Helm/Terraform Module für AivoraX + SmartTrendTracer Add-ons (Secrets, PV, Cronjobs).
- **Marketplace-Ready Modules:** Verpackung der neuen Adapter als wiederverwendbare Library mit Doku & Examples.

# Risiken
- **API-Limits & Credentials:** Twitter & Gmail erfordern stabile Keys; Rate-Limits können Flows blockieren → Retry/Backoff & Budget-Guards.
- **Datenvolumen:** Dokument-Processing teuer (LLM/Marker). Bedarf an Monitoring + Kosten-Grenzen.
- **Tagging-Drift:** Neue Konzepte oder geänderte Terminologie -> regelmäßige QA & hierarchische Pflege nötig.
- **UX-Complexity:** Dashboards und Viewer dürfen nicht überladen werden; modulare Komponenten erleichtern Wartung.

# Nächste Schritte
1. `docs/standards/smarttrendtracer.md` erzeugen und Datenstrukturen + KPIs festschreiben.
2. Adapter-Skelette (`twitter_ingest`, `rss_fetcher`, `concept_assigner`) im `runtime/toolkit/` anlegen inkl. pytest-Coverage.
3. PoC-Flow `ingest_tweets_basic.flow` schreiben, artefaktisieren und Trace überprüfen.
4. UX-Skizze für Trend Dashboard & QA-Sicht im AGUI-Team reviewen.
