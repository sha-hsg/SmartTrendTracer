# SmartTrendTracer - Defects & Known Issues

*Zuletzt aktualisiert: 2026-07-24*

---

## Critical / In Progress

*Keine offenen Einträge — DEF-001 wurde am 2026-07-24 gelöst (siehe Resolved).*

---

## Medium Priority

### DEF-003: Twitter Media URLs - 404 Errors
**Status:** By Design (API Limitation)
**Priorität:** Medium
**Bereich:** Backend - Twitter

**Problem:**
Twitter Media URLs (Bilder, Videos) geben 404 Fehler nach einiger Zeit.

**Ursache:**
Twitter API liefert temporäre URLs die nach einer gewissen Zeit ablaufen.

**Aktuelle Behandlung:**
- Frontend zeigt Placeholder für fehlgeschlagene Bilder
- Media-Section versteckt sich wenn alle Bilder broken sind

**Workaround:** Tweets neu collecten um frische Media URLs zu bekommen
```bash
cd backend
python tweet_collector_service.py   # (collect_tweets.py wurde entfernt)
```

---

### DEF-004: @sama Tweets - "Already in database" Meldung
**Status:** Resolved (2026-08-16 — Fehldiagnose, Symptom stammt vom Alt-Collector)
**Priorität:** Medium
**Bereich:** Backend - Tweet Collection

**Problem:**
@sama Tweets zeigen "already in database" obwohl sie neu sind.

**Analyse 2026-08-16:** DB-Prüfung (28.528 Tweets, 1.236 von sama): 0 ID-Duplikate,
`created_at` durchgehend BSON-Datetime, keine Naive/Aware-Mischung. Die Meldung kam
vom Vor-Rewrite-Collector (Log 2025-08-11), dessen State nicht fortschritt; der
heutige since_id-Fluss hat das Problem nicht. Ein Timezone-Fix-Script existiert
nicht und ist nicht nötig.

Was real existierte und behoben wurde: Pagination sortierte nur nach `created_at`
(973 Timestamp-Kollisionen) → Tweets konnten auf Folgeseiten doppelt ERSCHEINEN.
Fix: Tie-Break `(created_at, _id)` in browse.py. Zusätzlich wurden 89 Alt-Tweets
(Idiap_ch) mit ObjectId-`_id` auf Twitter-ID-String migriert, damit sie die
Duplikaterkennung nicht umgehen.

---

## Low Priority

### DEF-005: React Key Prop Warning (Development Only)
**Status:** Won't Fix
**Priorität:** Low
**Bereich:** Frontend - Development

**Problem:**
"Each child in a list should have a unique 'key' prop" Warning in `PaperViewerOptimized`

**Ursache:**
React Strict Mode Development Checks - False Positive

**Impact:** Keiner - Build funktioniert, Production nicht betroffen

---

### DEF-006: Forwarded Substack Articles - HTML in Previews
**Status:** Resolved (2026-08-16 — Root Cause behoben + Backfill)
**Priorität:** Low
**Bereich:** Backend - Substack

**Problem:**
Weitergeleitete Substack Artikel haben HTML-Artefakte in den Previews.

**Root Cause & Fix (2026-08-16):** Fünf Stellen (substack_parser 2x,
url_import 2x, playwright markdown_converter) erzeugten Previews als rohen
`markdown[:500]`-Slice — jede Collection erzeugte den Schmutz neu; das frühere
Rezept `clean_substack_footers.py` entfernte nur Footer, nicht die Artefakte.
Alle Stellen nutzen jetzt den gemeinsamen Cleaner
`app/services/preview_utils.generate_preview` (inkl. Empty-Label-Autolinks
`[](<url>)` und verschachtelter Bild-in-Link-Reste). 329 Alt-Previews per
Backfill regeneriert; 0 verbleibende Artefakte in der DB.

---

### DEF-007: Gary Marcus Artikel - Falsche Autor-Zuordnung
**Status:** Fixed in Code (2026-08-16 — latent, Gmail-Pfad aktuell ohne DB-Daten)
**Priorität:** Low
**Bereich:** Backend - Gmail Collector

**Problem:**
Gary Marcus Artikel werden manchmal Ethan Mollick zugeordnet.

**Root Cause & Fix (2026-08-16):** Die Attribution matchte Autor-Namen als
Substring im gesamten Mail-Body (Newsletter zitieren einander!) mit
First-Match nach Config-Reihenfolge, und der Sender-Header war nur letzter
Fallback. Neue Präzedenz in substack_parser.parse_author_from_sender:
1) kanonische Artikel-URL (<subdomain>.substack.com/p/...), 2) Sender-Header,
3) Body-Match mit frühester Fundstelle statt Config-Reihenfolge, ohne den
zu breiten E-Mail-Localpart-Indikator. Ethan Mollick ist jetzt explizit in
forwarded_authors.json konfiguriert.

---

### DEF-008: Twitter API Rate Limiting
**Status:** Has Workaround
**Priorität:** Low
**Bereich:** Backend - Twitter API

**Problem:**
Zu viele Requests in 15-Minuten Window führen zu Rate Limit Errors.

**Lösung:**
`tweet_collector_service.py` benutzen - hat eingebautes Rate Limiting

---

## Architecture / Technical Debt

*Keine offenen Einträge.*

---

## Resolved (Reference)

### [RESOLVED] DEF-001: Article Viewer - Optimistic UI Updates funktionieren nicht
**Gelöst:** 2026-07-24

**Problem:** Nach Aktionen im Article Viewer (Annotations, Summary hinzufügen) wurde die Artikel-Liste nicht aktualisiert; das Custom Event `articleViewerClosed` wurde dispatched, aber vom Parent nie empfangen.

**Ursache:** Der `articleViewerClosed`-Listener lag ausschließlich in der toten Datei `components/substack/FacetedSubstackDashboardModern.tsx` — das live gerenderte Articles-Dashboard hatte keinen Listener (Befund der Funktionsinventur, `docs/funktionsinventur.md`).

**Fix:** `onClose`-Callback + Event-Listener im aktiven `frontend/src/components/articles/FacetedArticlesDashboardModern.tsx` implementiert; der tote `components/substack/`-Ordner wurde gelöscht.

---

### [RESOLVED] DEBT-002: Debug Logs im Production Code
**Gelöst:** 2026-07-24

**Problem:** Debug console.logs (🔵, 🟠, 🔴) für DEF-001-Debugging im Code.

**Lösung:** Mit dem DEF-001-Fix erledigt — die betroffenen Dateien (alte `ArticleViewerModern.tsx` top-level, `components/substack/FacetedSubstackDashboardModern.tsx`) wurden in der Inventur-Bereinigung gelöscht. Verifikation: repo-weiter Grep nach 🔵/🟠/🔴 in `frontend/src/` ohne Treffer.

---

### [RESOLVED] DEBT-001: Legacy SQLite Scripts
**Gelöst:** 2026-01-21

**Problem:** Utility-Scripts nutzten alte SQLite-Imports obwohl das System vollständig auf MongoDB migriert war.

**Lösung:**
- 459 Backend-Scripts auf 11 essentielle Scripts reduziert
- Alle verbleibenden Scripts auf MongoDB/PyMongo migriert:
  - `clean_substack_footers.py` - Artikel Footer Bereinigung
  - `summarize_articles.py` - Artikel Zusammenfassungen
  - `check_collection_state.py` - Tweet Collection Status
  - `check_tag_consistency.py` - Tag System Konsistenz
  - `fix_previews.py` - Artikel Preview Fixes
  - `monitor_collection.py` - Collection Monitoring
- ~60+ One-Time Scripts nach `migrations/completed/` archiviert
- ~168 Test-Scripts und ~18 Debug-Scripts gelöscht

**Verifikation:** `grep -l "from app.models import" backend/*.py` gibt keine Ergebnisse mehr

---

### [RESOLVED] DEF-002: Topic Explorer - Keyboard Navigation
**Gelöst:** 2025-12-31

**Problem:** Keyboard-Navigation (Pfeiltasten) im Topic Explorer Dropdown funktionierte nicht nach Umstellung von cmdk auf native HTML.

**Lösung:**
- `highlightedIndex` State für aktuelle Auswahl
- `handleTopicSearchKeyDown` Handler für ↑↓ Enter Escape
- `useEffect` zum Reset bei Suchänderung
- Highlight-Klasse für visuelles Feedback

**Betroffene Datei:** `frontend/src/components/TopicExplorerModern.tsx`

---

### [RESOLVED] Gemini 3 Models - Infinite Loop
**Gelöst:** 2025-12-30

**Problem:** Gemini 3 Models mit temperature < 1.0 verursachten infinite loops

**Lösung:** `litellm_config.yaml` - temperature=1.0 für gemini-3-*-preview Models

---

### [RESOLVED] ANTHROPIC_API_KEY Error
**Gelöst:** 2025-12-30

**Problem:** Hardcoded API Key Check in articles_mongodb.py

**Lösung:** Check entfernt, LLM Manager handhabt Keys zentral

---

### [RESOLVED] Papers Endpoint - Missing slug Field
**Gelöst:** 2025-12-30

**Problem:** POST /api/papers/{id}/concepts gab kein `slug` Feld zurück

**Lösung:** `slug` Feld zur Response hinzugefügt in papers_mongodb.py

---

## Defect Template

```markdown
### DEF-XXX: [Kurze Beschreibung]
**Status:** [New | In Progress | Has Workaround | Won't Fix | Resolved]
**Priorität:** [Critical | High | Medium | Low]
**Bereich:** [Frontend | Backend | Database | API]

**Problem:**
[Beschreibung des Problems]

**Ursache:**
[Root Cause wenn bekannt]

**Betroffene Dateien:**
- `path/to/file.tsx`

**Workaround:** [Falls vorhanden]

**Lösung:** [Falls bekannt]
```
