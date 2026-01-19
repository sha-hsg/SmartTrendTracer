# Defects: Optimistic UI Updates

## Status: In Progress (Paused)

## Problem Summary
Nach Aktionen im Article Viewer (Annotations, Summary) wird die Liste nicht aktualisiert ohne manuellen Refresh.

---

## Defect 1: onClose Callback funktioniert nicht

**Symptom:**
- `onClose` wird in ArticleViewerModern aufgerufen (`🔵 X-Button clicked`)
- `onClose completed` erscheint
- Aber der Parent-Handler in FacetedSubstackDashboardModern wird NIE ausgeführt (`🔴` Log erscheint nicht)

**Getestete Lösungen:**
- [x] Async onClose mit await - funktioniert nicht
- [x] Try/catch um onClose - kein Error
- [x] Hard Refresh (Ctrl+Shift+R) - keine Änderung

**Vermutung:**
- Möglicherweise React/Radix Dialog Problem mit async callbacks
- Oder Component Lifecycle Issue

---

## Defect 2: Custom Event kommt nicht an

**Symptom:**
- Event wird dispatched (`🔵 X-Button clicked, dispatching articleViewerClosed event`)
- Event Listener in Parent empfängt das Event NICHT (`🟠` Log erscheint nicht)

**Code in ArticleViewerModern.tsx (Zeile ~1038):**
```typescript
window.dispatchEvent(new CustomEvent('articleViewerClosed', {
  detail: { articleId: article.id }
}))
```

**Code in FacetedSubstackDashboardModern.tsx (Zeile ~148):**
```typescript
useEffect(() => {
  const handleViewerClosed = async (event: CustomEvent) => {
    console.log('🟠 articleViewerClosed event received for:', articleId)
    // ... fetch and update
  }
  window.addEventListener('articleViewerClosed', handleViewerClosed as EventListener)
  return () => window.removeEventListener(...)
}, [])
```

**Vermutung:**
- Event wird dispatched aber Listener ist nicht registriert?
- Oder Component ist unmounted bevor Event ankommt?
- Portal/ErrorBoundary Issue?

---

## Was funktioniert (Referenz)

**Papers Dashboard:** Custom Event `paperTagsUpdated` funktioniert korrekt
- Event wird in PaperViewerOptimized dispatched
- FacetedPapersDashboard empfängt und aktualisiert State

**Unterschied zu Articles:**
- Papers verwendet keinen ErrorBoundary wrapper
- Papers Dialog-Struktur ist anders

---

## Nächste Schritte

1. [ ] Prüfen ob ErrorBoundary das Event blockiert
2. [ ] Prüfen ob Component-Mount-Timing ein Problem ist
3. [ ] Console.log im useEffect hinzufügen um zu prüfen ob Listener registriert wird
4. [ ] Alternative: Polling/Refetch bei Component-Focus

---

## Betroffene Dateien

- `frontend/src/components/ArticleViewerModern.tsx`
- `frontend/src/components/FacetedSubstackDashboardModern.tsx`
- `frontend/src/components/ArticleViewerErrorBoundary.tsx` (möglicherweise)

---

## Temporärer Workaround

User muss manuell "Refresh" Button klicken nach Änderungen im Article Viewer.

---

*Erstellt: 2025-12-30*
*Zuletzt bearbeitet: 2025-12-30*
