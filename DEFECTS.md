# SmartTrendTracer - Defects & Known Issues

*Zuletzt aktualisiert: 2025-12-31*

---

## Critical / In Progress

### DEF-001: Article Viewer - Optimistic UI Updates funktionieren nicht
**Status:** In Progress (Paused)
**Priorität:** High
**Bereich:** Frontend - Articles

**Problem:**
Nach Aktionen im Article Viewer (Annotations, Summary hinzufügen) wird die Artikel-Liste nicht aktualisiert. User muss manuell "Refresh" klicken.

**Symptome:**
- `onClose` Callback wird aufgerufen aber Parent-Handler läuft nicht
- Custom Event `articleViewerClosed` wird dispatched aber nicht empfangen
- Console zeigt `🔵 X-Button clicked` aber nicht `🟠 event received`

**Betroffene Dateien:**
- `frontend/src/components/ArticleViewerModern.tsx`
- `frontend/src/components/FacetedSubstackDashboardModern.tsx`
- `frontend/src/components/ArticleViewerErrorBoundary.tsx`

**Workaround:** Manuell "Refresh" Button klicken

**Details:** Siehe `DEFECTS_OPTIMISTIC_UI.md`

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
python collect_tweets.py
```

---

### DEF-004: @sama Tweets - "Already in database" Meldung
**Status:** Known Issue
**Priorität:** Medium
**Bereich:** Backend - Tweet Collection

**Problem:**
@sama Tweets zeigen "already in database" obwohl sie neu sind.

**Ursache:**
Timezone-Mismatch in datetime Objekten.

**Lösung:** Timezone-Fix Script ausführen (siehe Database Maintenance in CLAUDE.md)

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
**Status:** Has Workaround
**Priorität:** Low
**Bereich:** Backend - Substack

**Problem:**
Weitergeleitete Substack Artikel haben HTML-Artefakte in den Previews.

**Lösung:**
```bash
cd backend
python fix_previews.py
```

---

### DEF-007: Gary Marcus Articles - Falsche Author Attribution
**Status:** Known Issue
**Priorität:** Low
**Bereich:** Backend - Email Parsing

**Problem:**
Gary Marcus Artikel werden manchmal Ethan Mollick zugeordnet.

**Ursache:**
Email-Parsing Konfusion bei weitergeleiteten Inhalten.

**Workaround:** Manuell Author korrigieren in UI

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

### DEBT-001: Hybrid Database State
**Status:** Technical Debt
**Bereich:** Database Architecture

**Problem:**
Tag Ontology nutzt MongoDB, aber manche Tweet/Paper/Article Tag Operationen nutzen noch alte Patterns.

**Referenz:** Siehe `TAG_SYSTEM_ANALYSIS.md`

---

### DEBT-002: Debug Logs im Production Code
**Status:** Technical Debt
**Bereich:** Frontend

**Problem:**
Debug console.logs (🔵, 🟠, 🔴) sind noch im Code für Debugging von DEF-001.

**Betroffene Dateien:**
- `frontend/src/components/ArticleViewerModern.tsx`
- `frontend/src/components/FacetedSubstackDashboardModern.tsx`

**Aktion:** Entfernen wenn DEF-001 gefixt ist

---

## Resolved (Reference)

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
