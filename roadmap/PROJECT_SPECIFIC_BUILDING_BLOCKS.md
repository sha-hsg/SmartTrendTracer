**Zusammenfassung:** Gegenüberstellung der projekt-spezifischen Building Blocks aus den AivoraX-Roadmaps und Vorschläge, wie sie unter dem Composable-Prinzip („as simple as possible, but not simpler“) generalisiert werden können.
**Inhalt:**
- Überblick
- Projektbezogene Building Blocks & Composable Ableitungen
  - SwissMap
  - ImpactRating
  - CompanyCompetences
  - StatCoach
  - SmartTrendTracer
  - FinancialTouchstone
  - QuestionForge

# Überblick
Neben den projektübergreifenden Modulen gibt es Spezial-Adapter, die bislang nur in einer Roadmap auftauchen. Viele lassen sich in klar umrissene, wiederverwendbare Bausteine überführen, wenn wir sie konsequent auf Ein- und Ausgabe sowie Konfiguration reduzieren. Die folgende Analyse zeigt, wie diese Spezialschnittstellen zu Composable Building Blocks entwickelt werden können.

# Projektbezogene Building Blocks & Composable Ableitungen
## SwissMap
| Spezieller Block | Aktuelle Aufgabe | Composable Weiterentwicklung | Hinweise |
| --- | --- | --- | --- |
| `tag_filter_builder` | Erzeugt Kaskaden von Tag1/Tag2/Tag3 | Allgemeiner **`hierarchical_filter_builder`**: Eingabe = Records + Ebenen-Spezifikation; Ausgabe = Listen/Mapping. | Parametrische Definition der Ebenen; nutzbar für ImpactRating, CompanyCompetences. |
| `geojson_builder` | Wandelt Datensätze in GeoJSON um | **`geojson_builder`** als generischer Geospatial-Adapter, optional inklusive Marker-Styling-Metadaten. | Kombinierbar mit `geocode_batch`; für Trend-Heatmaps verwendbar. |
| `edit_store` | Persistiert manuelle Edits | Allgemeiner **`change_request_store`** mit Storage-Strategien (JSON, DB). | Einheitliche Schnittstelle für Approvals + Audit. |

## ImpactRating
| Spezieller Block | Aktuelle Aufgabe | Composable Weiterentwicklung | Hinweise |
| --- | --- | --- | --- |
| `comment_cleaner` | Bereinigt Freitext-Kommentare | **`text_cleaner`** mit konfigurierbaren Pipelines (Stopwörter, Regex, Normalisierung). | Für CompanyCompetences, QuestionForge nutzbar. |
| `sentiment_classifier` | Sentiment/Ton-Analyse | **`sentiment_classifier`** als generischer Adapter (LLM oder ML), Parameter für Domain. | Kann in Trend-Analysen/Feedback-Systemen eingesetzt werden. |
| `aggregation_builder` | Mehrstufige Aggregation | Generalisierung zu **`aggregation_builder`** (bereits als cross-project Block erkannt) → hier definida. |
| `report_generator` | Reports (Jinja/Pandoc) | Schon als gemeinsamer Block vorgesehen; ImpactRating liefert Domain-Templates. |

## CompanyCompetences
| Spezieller Block | Aktuelle Aufgabe | Composable Weiterentwicklung | Hinweise |
| --- | --- | --- | --- |
| `company_cleaner` | Datenbereinigung (Unternehmen) | **`entity_cleaner`**: Regelset + Normalisierung; Entities konfigurierbar (Unternehmen, Schulen, Kunden). |
| `taxonomy_loader` | Lädt Taxonomie | **`taxonomy_loader`** als generischer YAML/JSON-Loader mit Versionierung. |
| `company_tagger` | LLM-Tags + Confidence | Erweiterung des gemeinsamen **`concept_assigner`** um Entity-Kontext. |
| `taxonomy_extender` | Hierarchie-Erweiterung | **`taxonomy_extender`**: arbeitet mit Vorschlag + Approval-Flow; nutzbar für Trend- oder Lern-Taxonomien. |
| `cluster_builder` & `stats_aggregator` | Clustering/Statistik | Zu **`cluster_builder`** bzw. **`aggregation_builder`** generalisieren (konfigurierbar: Algorithmus, Feature-Sets). |

## StatCoach
| Spezieller Block | Aktuelle Aufgabe | Composable Weiterentwicklung | Hinweise |
| --- | --- | --- | --- |
| `youtube_transcript_fetcher` | YouTube-Transkripte | **`video_transcript_fetcher`** mit Provider-Plug-ins (YouTube, Vimeo, lokale Dateien). |
| `video_clip_generator` | Clip-Erstellung | **`video_segmenter`**: generiert Clip-Referenzen/Highlights, optional Transkripte. |
| `stats_solver` | Statistische Berechnungen | **`math_solver`** mit Plugin-System (NumPy/SymPy). | Wiederverwendbar für Aufgaben-Generatoren, Benchmarks. |
| `plot_renderer` | Diagramme erzeugen | **`plot_renderer`** als universelles Chart-Modul (Matplotlib/Plotly). |
| `xp_engine`, `achievement_evaluator` | Gamification Logik | **`gamification_engine`** mit Regeldateien (YAML), einzelne Rules pro Flow-Call. |
| `pet_state_manager` | StatGotchi Zustände | **`virtual_pet_state`**: Zustandstransitionen per YAML + Approvals. |
| `lms_webhook_adapter` | LMS Sync | **`webhook_connector`** mit konfigurierbaren Endpoints, auch für andere Integrationen. |

## SmartTrendTracer
| Spezieller Block | Aktuelle Aufgabe | Composable Weiterentwicklung | Hinweise |
| --- | --- | --- | --- |
| `twitter_ingest` | Social-Media Pulls | **`social_feed_ingest`** mit Provider-Modulen (Twitter, Mastodon, LinkedIn). |
| `rss_fetcher`, `substack_parser` | Newsletter Intake | **`feed_ingest`** (RSS/Atom) + **`html_newsletter_parser`**. |
| `epub_splitter`, `pdf_chunker` | Format-spezifisches Chunking | Erweiterung von `document_ingest` mit Format-Strategien. |
| `trend_aggregator` | Trend-Kennzahlen | Spezialisierung von `aggregation_builder` mit Zeitachsen & Momentum-Metriken. |
| `embedding_encoder` | Embedding-Hülle | Allgemeiner Block (bereits cross-project). |
| `mongodb_writer/query` | Persistenz | Allgemeiner DB-Adapter Set (Mongo/Postgres). |

## FinancialTouchstone
| Spezieller Block | Aktuelle Aufgabe | Composable Weiterentwicklung | Hinweise |
| --- | --- | --- | --- |
| `multi_llm_runner` | Mehrere Modelle vergleichen | **`multi_llm_runner`** generisch halten: Liste von Modellen, orchestriert Requests & Fallbacks. |
| `financial_scorer` | Antwortbewertung | **`benchmark_scorer`** mit konfigurierbaren Kriterien, erweiterbar auf andere Fächer. |
| `metrics_aggregator` | Benchmark-Statistiken | Spezialisierung von `aggregation_builder` (Kennzahlen). |
| `benchmark_reporter` | Benchmark-Reports | Nutzt gemeinsamen `report_generator`, aber mit Score-Templates. |
| `config_validator` | Config-Prüfung | **`config_validator`** generisch: JSON/YAML Schema Validation + File Checks. |

## QuestionForge
| Spezieller Block | Aktuelle Aufgabe | Composable Weiterentwicklung | Hinweise |
| --- | --- | --- | --- |
| `goal_extractor` | Lernziele strukturieren | **`goal_extractor`** generisch für Bildungs-/Projektziele. |
| `question_generator` | Fragen erstellen | **`question_generator`** (LLM oder regelbasiert) – modular je Taxonomie. |
| `answer_generator` | Antwortvarianten | **`answer_generator`** mit konfigurierbaren Stilen (kurz, detail, Pareto). |
| `taxonomy_classifier` | Bloom-Level bestimmen | **`taxonomy_classifier`** generalisieren (auch für andere Taxonomien). |
| `citation_builder` | Quellenbelege | **`citation_builder`**: generisch für Text + Referenz-Indizes. |
| `latex_exporter` | LaTeX Dokumente | Allgemeiner Exporter (bereits in Cross-Block-Liste). |
| `question_validator` | Struktur-/Inhalt-Check | Generische Validatoren; schon als cross-project Block erwähnt. |

---

**Empfehlung:** Die oben skizzierten Spezialeinheiten als modulare, konfigurierbare Adapter (Input→Output) definieren und in `runtime/toolkit/` mit Tests/Schema-Doku platzieren. So lassen sich Roadmap-spezifische Anforderungen bedienen, ohne Einmal-Lösungen zu bauen.
