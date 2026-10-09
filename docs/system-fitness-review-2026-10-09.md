# System-Fitness-Review SmartTrendTracer — 2026-10-09

Prüfung des gesamten Systems auf Zweck, Funktion, Umsetzung, Plausibilität, Bedienung und
Zusammenspiel. Sechs Bereiche, je geprüft an Code, Daten (MongoDB, nur lesend) und laufendem
Betrieb (GET-Endpunkte, Logs, Tests). Das Trend Detection Dashboard wurde am 2026-10-08/09
separat geprüft und auf `app/services/trend_core.py` umgebaut; hier nur Restpunkte.

**Status-Kennzeichnung:** ✅ bestätigt (reproduziert oder in Code + Daten belegt) ·
🟡 begründete Vermutung · ❓ offene Frage. **Schwere:** K kritisch · H hoch · M mittel · N niedrig.

**Annahme zum Zweck** (nicht ausdrücklich dokumentiert, aus CLAUDE.md und Nutzung abgeleitet):
STT ist das persönliche Beobachtungsinstrument eines KI-Professors für *seine* Informationsblase
(Accounts, Newsletter, eigene Paper). Es soll (1) zuverlässig sammeln, (2) Inhalte über ein
gemeinsames Konzeptsystem erschliessen, (3) zeigen, was neu ist, wächst oder verschwindet, und
(4) Paper lesbar, durchsuchbar und befragbar machen. Daran wird der Nutzen jedes Elements gemessen.

---

## 1. Gesamtbewertung

| Bereich | Urteil | Kernaussage |
|---|---|---|
| Plattform / Betrieb | gut, mit Lücken | Tests, Architektur-Guard, Start-Skript, Scheduler solide; aber im LAN offen, kein Backup, Logs werden bei jedem Start gelöscht |
| Twitter/X | braucht Arbeit | Sammeln und Speichern sauber; **Volltextsuche liefert 0 Treffer**, Zeiten 2 h falsch, Engagement-Zahlen unbrauchbar, lange Posts abgeschnitten |
| Artikel / Newsletter / Autoren | braucht Arbeit | Browse, Viewer, PDF-Export gut; 2 von 4 Artikel-Menüpunkten leer/kaputt, Autorenzählung dreifach verschieden, Gmail-Sammlung läuft nicht |
| Papers / Bücher | braucht Arbeit, Bücher schlecht | Lese-API schnell, Analysen stark genutzt; Datenqualität (Datum, Duplikate, Platzhalter-Abstracts), Feed endet vor der Verarbeitung, **Bücher nie verarbeitet** |
| Konzepte / Ontologie / RAG | Datenqualität schlecht, Werkzeuge mittel | RAG gesund; aber **Aliase greifen beim Taggen nie**, ~900 Dubletten-Gruppen, 92 % Konzepte ohne Eltern, Personen als „topic“ |
| Analyse-Ansichten / Navigation | Konsolidierung nötig | Trend Dashboard, Digest, Article Trends tragfähig; daneben 4 alte Trend-Implementierungen mit den alten Fehlern; Statistik zeigt falsche/leere Werte; Menü führt mehrfach auf dieselbe Ansicht |

**Gesamturteil: im Alltag nutzbar, aber nicht verlässlich.** Die Infrastruktur (Sammeln,
Speichern, Verarbeiten, Scheduler, RAG, Tests) ist besser als bei persönlichen Werkzeugen
üblich. Die Schwächen liegen fast alle an drei Stellen:

1. **Parallele Implementierungen** derselben Frage (Trends ×5, Autorenzählung ×3, Slug-Regeln ×3,
   Verarbeitungspfade je Importer, zwei Tweet-Browse-Module). Jede hat eigene Fehler; die
   Zahlen widersprechen sich zwischen Ansichten.
2. **Datenqualität an den Eingängen**: Konzept-Dubletten, uneinheitliche Datums- und Id-Formate
   bei Papers, mehrfach gespeicherte Autorenfelder. Alles, was darauf aufbaut (Trends, Facetten,
   RAG-Filter), erbt die Fehler.
3. **Abgerissene Ketten**: Feed → Import → *(keine Verarbeitung)*; DOI-Import ohne PDF →
   *(kein Weg, PDF nachzureichen)*; GROBID → *(läuft nie automatisch)*; Gmail → *(läuft nicht)*.

---

## 2. Priorisierte Massnahmen

### P1 — sofort (Fehlfunktion oder Risiko, kleiner Aufwand) — ✔ alle 10 umgesetzt am 2026-10-09

| # | Element | Problem | Auswirkung | Massnahme | Status |
|---|---|---|---|---|---|
| 1 | Tweet-Volltextsuche | Textindex `tweets_text_search` liegt auf `full_text`; Startup löscht den alten Index auf `text` | Suche „agent“ → 0 Treffer (selbst geprüft) | Index auf `text` (+ `full_text`) | ✅ K |
| 2 | Netzwerk-Bindung | Backend, Marker, MinerU auf `0.0.0.0` | 277 Routen inkl. 25 DELETE und kostenpflichtigem RAG-Rebuild im WLAN erreichbar, ohne Auth | `--host 127.0.0.1` | ✅ (Lauschen), 🟡 (Erreichbarkeit von Fremdgerät) H |
| 3 | Datensicherung | Kein geplanter `mongodump`; letzter Dump 2026-09-06 (Linux-Zeit), Time Machine nicht erreichbar | Ein Platten-/DB-Fehler löscht 148k Tags, Analysen, Notizen | Wöchentlicher Scheduler-Job `mongodump --db smarttrendtracer` mit Aufbewahrung | ✅ H |
| 4 | Backend-Log | `start_stt.sh` schreibt mit `>` in dieselbe Datei wie der RotatingFileHandler | Jeder Start löscht die Historie; der RAG-Hänger vom 2026-10-06 ist nicht mehr nachvollziehbar | stdout in eigene Datei mit `>>`, Rotation dem Handler überlassen | ✅ H |
| 5 | Alias-Auflösung beim Taggen | `add_tag` sucht Aliase im Feld `alias`, die Dokumente haben `alias_text` (selbst geprüft) | Die 330 Aliase wirken nie; jede Schreibvariante wird ein neues Konzept | Lookup auf `alias_text`, normalisiert, eine gemeinsame Funktion | ✅ H |
| 6 | Trend-Kern `data_through` | Seit das Tagging aktuell ist, steht das Datenende auf *heute* | Ein angebrochener Tag zählt in die Trendfenster (24-h-Fenster = halber Tag) | Auf den letzten *vollständigen* Tag begrenzen | ✅ M (eigener Fehler von gestern) |
| 7 | Scheduler-Robustheit | Kein Backoff nach Fehler; `paper_feed` meldet ok trotz 3/5 gescheiterter Feeds; laufender Scheduler wird bei Start nicht neu gestartet | 10 Fehlversuche à 30 min blockierten am 06.10. alle Jobs 6 h; neue Jobs erst nach manuellem Neustart aktiv | Backoff, „partial“-Status, Scheduler beim Start neu starten | ✅ H |
| 8 | Gefährliche Alt-Skripte | `clean_start.sh`, `emergency_stop.sh` töten per `kill -9` alles auf Port 8000 (Honcho) und jedes uvicorn | Ein Fehlgriff legt Honcho, Scriptorium, Samanta lahm | Löschen (mit `start_api.sh`, `restart_server.sh`, `RESTART_BACKEND.sh`, `sync-*.sh`) | ✅ M |
| 9 | Zeitstempel im UI | API liefert Zeiten ohne Zone, Browser liest sie als Lokalzeit | Alle Tweet- und Medienzeiten 2 h zu früh (CEST) | UTC mit Zone ausliefern | ✅ H |
| 10 | Statistik-Seite | Zählt leere/nicht existierende Felder; Frontend liest Felder, die die API nicht liefert | Tweets „178 getaggt“ statt 31 627, Abdeckung 0,56 % statt ~100 %, viele Kacheln 0, „Manual collection only“ falsch | Über `tag_instances` zählen, Felder angleichen | ✅ H |

### P2 — bald (falsche Aussagen, Doppelungen, abgerissene Ketten) — ✔ umgesetzt am 2026-10-09 (offen: Gmail-Login durch Nutzer, GROBID-Server extern down)

| # | Element | Problem | Auswirkung | Massnahme | Status |
|---|---|---|---|---|---|
| 11 | Alte Trend-Ansichten | „Trending Topics“, „Analysis › Topic Clustering“, „Compare Sources“, Twitter „Visualizations“, „Article Analytics“ nutzen Importdatum, Tag-Erstellungsdatum, „% zur Vorperiode“, keinen Hub-Filter | Zeigen den Import-Batch „IMP“ als +2700 %, 1→0 als −100 %, Tagging-Läufe als Spitzen; widersprechen dem Trend Dashboard | Löschen bzw. auf `trend_core` umstellen; Menü bereinigen | ✅ H |
| 12 | Konzept-Dubletten | 79 Gruppen nur Gross/Klein, 873 Gruppen (913 Extra-Konzepte) nur Akzent/Plural/Satzzeichen (Clément/Clement, HuggingFace/Hugging Face, LLM/LLMs); drei verschiedene Slug-Regeln | Zählungen, Trends, RAG-Filter auf Varianten verteilt | Eine Slug-Funktion; einmaliger Merge mit Trockenlauf; normalisierter Schlüssel vor Neuanlage | ✅ H |
| 13 | Konzept-Feld `id` | String-Sortierung „c_9999“ > „c_10000“ + Zähler pro Prozess → 627 Id-Werte von 10 726 Konzepten geteilt | `find_concept_by_any_id` und RAG-`concept_ids` können falsche Konzepte treffen | `c_`-Ids abschaffen, nur `_id` | ✅ Daten, 🟡 falsche RAG-Treffer H |
| 14 | Autorendaten | Autor in bis zu 5 Feldern; drei Zählungen (Pascal Biese 141 / 148 / 11; Gary Marcus 15 / 5 / 5) | Autoren-Ansichten widersprechen sich; „without-author“ meldet 569/610 | `primary_author_id` nachfüllen, eine Zählfunktion; Autor-UIs zusammenlegen | ✅ H |
| 15 | Paper-Datumsfeld | 184 von 441 ohne Datum, drei Speicherformate; Jahr-Facette fällt auf Importjahr zurück | `years=2026` liefert Paper von 2010/2014/2019 | Migration auf ein Format, Nachfüllen aus Crossref/arXiv | ✅ H |
| 16 | Paper-Dubletten | arXiv-Ids in drei Formaten, Upload ohne Dublettenprüfung | 7 arXiv-Gruppen, 1 DOI-Dublette, 1 PDF doppelt | Ids normalisieren, md5/DOI prüfen, zusammenführen | ✅ M |
| 17 | Feed → Verarbeitung | Feed-Import legt Paper mit leerem Inhalt an, kein Marker-Lauf, kein Link zum Paper | Kette endet vor Verarbeitung/Tagging/RAG; 156 Kandidaten ungesichtet | Marker automatisch einreihen, Link + Status im Feed | ✅ H |
| 18 | DOI-Import ohne PDF | UI sagt „PDF hochladen“, es gibt keinen Weg, ein PDF an ein bestehendes Paper zu hängen | Befolgen erzeugt eine Dublette | `PUT /{id}/pdf` + Badge/Filter „PDF fehlt“ | ✅ H |
| 19 | Bücher | 0 von 4 je verarbeitet; 2 „failed“ (Marker 422), 2 seit 2025-09 „pending“ ohne Job; Worker sendet Optionen, die Marker nicht kennt | Bereich funktioniert nicht | 422 klären, Waisen neu einreihen, Schein-Optionen entfernen — oder Bücher stilllegen | ✅ H |
| 20 | Twitter-Sammelrhythmus | Tier-Logik existiert nur in UI und Doku; jeder Zyklus fragt alle 24 Accounts ab und wartet 900 s | Tatsächlich ~32 min statt 15; „check every 30 min / 2 h / 6 h“ im Formular falsch | Tiers umsetzen oder aus UI/Doku entfernen | ✅ M |
| 21 | Lange Tweets | `note_tweet` nie angefragt | ~947 Posts (60 Tage) bei 280 Zeichen + t.co abgeschnitten; Tagging/RAG sehen nur den Anfang | `note_tweet` anfragen und speichern | ✅ M |
| 22 | Engagement-Zahlen | Likes/Retweets einmalig beim Sammeln; Retweets dem Retweeter gutgeschrieben | Sortierung nach Engagement und `engagement_rate` sind Rauschen | Retweets ausschliessen, nach 48 h auffrischen oder „bei Erfassung“ kennzeichnen | ✅ M |
| 23 | Menü / Startseite | „Unified Trends“ = Trend Dashboard; „Compare Sources“ = Twitter „Visualizations“; zwei verschiedene „Topic Clustering“; 4 „Coming soon“; Paper Feed, Digest, Q&A ohne Startseiten-Karte | Nutzer landen mehrfach in derselben oder einer leeren Ansicht | Menü konsolidieren (siehe Abschnitt 4) | ✅ M |
| 24 | Inline-Prompts | `tweets/annotation.py` (6-stündlicher Tagging-Job!), `concepts_suggestions`, Artikel-Verarbeitung, Paper-Analyse, Tag-Reorganizer, Summarization; 14 ungenutzte Keys in `prompts_config.json` | Verstösst gegen §3.8; Prompt-Änderungen in der Konfiguration wirken nicht | Auf `llm.get_prompt()` umstellen, tote Keys löschen | ✅ M |
| 25 | `llm.json` | Wird nur für `rag_embedding` gelesen; 4 Tasks widersprechen dem Router; CLAUDE.md beschreibt es falsch | Irreführende Konfiguration | Auf `rag_embedding` reduzieren, Doku korrigieren | ✅ M |
| 26 | Artikel-Clustering | Liest leeres Feld `articles.tags` | Ansicht komplett tot (0 Artikel, 400/500) | Löschen (Associations deckt die Frage ab) oder auf `tag_instances` umstellen | ✅ K |
| 27 | Newsletter-Sammlung | Kein Artikel mit `source: 'email'`, kein geplanter Collector, kein UI-Auslöser; Gary Marcus zuletzt 2025-08 | Sammlung rein manuell; CLAUDE.md beschreibt eine Gmail-Pipeline, die nicht läuft | Entscheiden: Gmail-Job einplanen oder Doku korrigieren | ✅ Daten, 🟡 Ursache H |
| 28 | Referenzen / GROBID | Letzter Schreibvorgang 2025-09-01; 11 von 227 neuen Papern mit Referenzen | Reference Manager zeigt veralteten 11-%-Ausschnitt | GROBID nach Verarbeitung laufen lassen oder als Teilmenge kennzeichnen | ✅ M |
| 29 | Paper-Tagging | 210 von 441 Papern getaggt; Scheduler taggt nur Tweets | Paper fehlen in Konzeptsuche und Trends | Tagging-Job für Paper und Artikel (gleicher Mechanismus wie `tag_tweets`) | ✅ M |
| 30 | Smoke-Check | LLM-Check prüft nur Schlüssel; Scheduler-Check ignoriert Teilausfälle/Alter; keine Prüfung auf Tweet-Aktualität, Book-Worker, Plattenplatz | Abgelaufene Keys, X-402, hängende Feeds bleiben grün | Alters- und Teilausfall-Prüfung, „neuester Tweet > 1 Tag“ | ✅ M |

### P3 — Pflege (Kosmetik, Performance, Hygiene)

| # | Element | Problem | Massnahme | Status |
|---|---|---|---|---|
| 31 | Ontologie-Struktur | 92 % ohne Eltern, 68 % einmal benutzt; Organize-Liste unsortiert, 5,4 s | Nach echter Nutzung sortiert organisieren, eine Aggregation | ✅ |
| 32 | Entity-Typen | Personen als `topic`/`concept` (Karpathy, Altman, Mollick) | Typ beim Taggen setzen, Bestand umtypisieren | ✅ |
| 33 | Ontologie-Statistiken | Drei Definitionen von „unorganisiert“; `with_children` 26 427 statt 26 | Eine Definition, Abfrage korrigieren | ✅ |
| 34 | Tag-Reorganizer | Schickt alle 28k Konzepte (~570k Tokens) in einen LLM-Aufruf | Zerlegen oder zugunsten von Organize stilllegen | 🟡 |
| 35 | Grosse Payloads | Ontologie-Baum 7,4 MB, Konzeptgraph 9,2 MB, Paper-Liste bis 4 MB, Artikel-Liste 1,3 MB/Seite, Tweet-Hierarchie-Facetten 1 MB (nur 16 % der genutzten Konzepte) | Paging, Projektionen, nur genutzte Konzepte | ✅ |
| 36 | Dark Mode | Viele Komponenten mit festen `bg-white`/`text-gray-*` (Twitter, Account Manager, Media, Paper Viewer, Autoren-Modal, Trend-Overview, Summarization) | Theme-Tokens | ✅ Code, 🟡 Darstellung |
| 37 | Repo-Hygiene | 1,68 GB Daten-PDFs in git, `.git` 1,1 GB, 487 Debug-Läufe, 10 Syncthing-Konflikt-Dateien, 410 Start-Logs, ~30 alte Berichte im Wurzelverzeichnis | `.gitignore`, `git rm --cached`, Archiv | ✅ |
| 38 | MongoDB | Doppelte Indizes (DOI, arXiv, tag_instances); `llm_usage` 64 MB ohne TTL; leere Altsammlungen | Bereinigen, TTL | ✅ |
| 39 | ✔ `--reload` im Normalbetrieb | Jede `.py`-Änderung startet das Backend neu, laufende Annotationen gehen verloren | Aus `start_stt.sh` entfernen | ✅ |
| 40 | Kleinkram | `validate-url` immer 404 (Routenreihenfolge); falsche 500 bei ungültigem Jahr/Datum; stille Annahme falscher Parameter; tote Highlight-Aktion im Paper Viewer; `rag/stats` zeigt `total_concepts: 0`; RAG-„Rebuild“ (~30 min, Kosten) ohne Rückfrage; Reddit-Prozessprüfung in `start_stt.sh` kann nie greifen | Einzeln beheben | ✅ |
| 41 | Doku | CLAUDE.md: 114 Tests (real 134), ~266 Routen (277), ~360 Paper (446), ~25k Konzepte (28,7k) | Aktualisieren | ✅ |

---

## 3. Befunde je Bereich (Kurzfassung, vollständige Liste in Abschnitt 2)

**Twitter/X.** Schema-Disziplin vorbildlich (String-`_id`, BSON-Daten, ein Speicherpfad).
Fehler: Suche (#1), Zeitzone (#9), Tiers (#20), `note_tweet` (#21), Engagement (#22),
Hierarchie-Facetten zeigen 16 % der Konzepte, Facetten ignorieren Jahr-/Annotationsfilter,
Account-„Total“ ist ein abgedrifteter Zähler (emollick 3 248 statt 5 021), `is_retweet` auch bei
Antworten/Zitaten (25 523 statt 12 418), zwei Browse-Module, zweiter Sammelpfad `POST /{id}/collect`,
LorenaRaichle (0 Tweets) und Idiap_ch (1 Jahr still) werden jede Runde abgefragt.

**Artikel/Newsletter/Autoren.** Browse, Facetten, Viewer (Ansicht/Bearbeiten), PDF-Export
schnell und korrekt. Clustering tot (#26), Article Analytics leer (#11), Autoren dreifach gezählt
(#14), Article Trends: Autor „Unknown“ für 6/22, „Top topics“ sind Stoppwort-Zählungen, Highlights
immer 0, Cluster-Tab immer leer; Hierarchie-Schalter ruft 404-Route; Suche nur im Titel
(35 statt 452 Treffer für „reasoning“); 83 Artikel mit „Audio playback is not supported…“-Resten.
DEF-007 (Gary Marcus) nicht mehr reproduzierbar.

**Papers/Bücher.** Analyse-Katalog stark genutzt (233 Paper), Tag-Konsistenz exakt, Review-Modus
korrekt ausgeschlossen, Q&A und Feed-Backend sauber. Probleme: #15–19, #28, Platzhalter-Abstract
bei 60 Papern (49 davon verarbeitet), 62 ohne Autoren, Review-Statistik zeigt Konzeptzahl der
Research-Paper, Facetten flackern (fehlender Tie-Break), alte Verarbeitungsfehler zeigen roten
Retry-Block bei fertigen Papern, jeder Importer mit eigener Verarbeitung.

**Konzepte/Ontologie/RAG.** RAG gesund (32 645 Einträge, deckungsgleich mit DB, inkrementell
täglich); keine Tag-Zeilen auf fehlende Konzepte; gemischte `concept_id`-Formen werden korrekt
aufgelöst. Probleme: #5, #12, #13, #31–34, Beschreibungen generischer Konzepte mit
Einzeldokument-Kontext überschrieben („LLM = … upon which AgentEvolver is built“), 176 hängende
Eltern-Verweise, Konzeptsuche ohne Wortgrenzen/Akzentfaltung („rag“ → Cloud Storage vor GraphRAG),
zwei Graph-APIs und zwei fast identische Entity-Karten, Bücher/Reddit ohne Tags und nicht im RAG.

**Analyse-Ansichten/Navigation.** Tweet-Gesamtzahlen stimmen zwischen `/health`, Statistik und DB
überein; Digest, Article Trends, User Analysis tragfähig. Probleme: #10, #11, #23; Topic Explorer
datiert Artikel/Paper nach Import und lässt leere Wochen aus (Linie springt über Lücken),
Korrelations-Tab plottet Anzahl gegen Anzahl (keine Assoziation); AI Summarization mit
Inline-Prompt, ungeprüfter Modellwahl und stillem Fallback; drei sich überlappende Digests
(26.09., 27.09., 01.10.); Reddit ohne Daten und ohne Zugangsdaten.

**Plattform/Betrieb.** Start-Skript erfüllt die Robustheitsregeln (SCRIPT_DIR, explizite venvs,
Validierung, Pins, 60-s-Timeout, Smoke-Check), Start ~30 s; 134 Tests grün, Frontend-Build grün,
1 tsc-Fehler; keine Secrets im Repo; CORS korrekt; Modell-Konfiguration konsistent (alle
Migrationsziele routbar). Probleme: #2–4, #7, #8, #24, #25, #30, #37–39.

---

## 4. Konsolidierungsvorschlag Navigation

| Behalten | Zusammenlegen | Entfernen |
|---|---|---|
| Trend Dashboard (6 Tabs), Weekly Digest, Paper Feed, Paper Q&A, Article Trends, User Analysis, Topic Explorer (nur Frequenz-Tab, korrigiert), Statistik (korrigiert), AI Summarization (korrigiert), Browse-Ansichten, Viewer, Concept Management | Twitter „Visualizations“ + „Compare Sources“ + „Article Analytics“ (eine Komponente hinter drei Menüpunkten) → in Trend Dashboard aufgehen lassen; Autoren-Seite + Autoren-Modal → eine Autoren-Ansicht | „Unified Trends“ (Dublette), „Trending Topics“ und „Analysis › Topic Clustering“ (alte Trendlogik), Artikel-Clustering (tot), 4 „Coming soon“, Reddit bis Collector läuft, Tag-Reorganizer (zugunsten Organize), Altansichten `tags-organisation`/`concept-organizer` |

Startseite: Karten für Paper Feed, Weekly Digest, Paper Q&A ergänzen; Platzhalter-Karten entfernen.

---

## 5. Was gut funktioniert und bleiben soll

- **Speicher-Disziplin bei Tweets**: String-`_id`, ein Speicherpfad, monotoner Sammelstand.
- **Architektur-Guard** mit Ratschen (0 DB-Aufrufe in Routern, ≤ 163 `_queries`-Funktionen, ≤ 52 rohe `fetch`) und 134 Regressionstests.
- **Start-Skript und Scheduler** mit Nachhol-Logik, Zustand in MongoDB, abschliessendem Smoke-Check.
- **RAG**: inkrementelles Update, Modellprüfung, Gewichtung über Inhaltstypen.
- **Trend-Kern** (`trend_core`) und **Topic-Map** (`topic_episodes`) als gemeinsame, getestete Basis für Trendfragen.
- **Paper-Analysen**, **Paper Q&A** mit Abschnittszitaten, **Paper Feed** mit Konzept-Zentroiden.
- **Artikel-Browse, Viewer (Ansicht/Bearbeiten), PDF-Export**.
- **Fehlerbehandlung**: saubere 404/422, bereinigte 500er, keine nackten `except`, keine Secrets im Repo, CORS eng.

---

## 6. Nicht geprüft

- Alle schreibenden Wege (POST/PUT/DELETE): Importe, Uploads, Marker/MinerU-Verarbeitung, GROBID, Entity-Extraktion, Tag-Vorschläge, Reorganisation, Autoren-Merge, Sammelauslöser, RAG-Rebuild.
- Qualität von LLM-Ausgaben (Analysen, Q&A-Antworten, Zusammenfassungen, `/api/rag/ask`).
- Darstellung im Browser für die meisten Ansichten (Dark Mode, Performance grosser Bäume/Graphen nur aus Code und Payload-Grössen erschlossen); das Trend Dashboard wurde am 2026-10-09 im Browser geprüft.
- Erreichbarkeit aus dem LAN von einem fremden Gerät (nur vom Mac selbst getestet).
- Ursache der Marker-422 bei Büchern und des RAG-Hängers vom 2026-10-06 (Log bereits überschrieben).
- Gültigkeit des Gmail-OAuth-Tokens; X-API-Kontingentabrechnung gegen das Developer-Portal.
- Time-Machine-Inhalt (Ziel nicht erreichbar).
