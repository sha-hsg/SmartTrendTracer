import { useEffect, useState, useCallback } from 'react'
import { AlertTriangle, X, Wand2, Loader2 } from 'lucide-react'
import http from '@/services/http'

interface DeprecatedEntry {
  task_type: string
  current_model: string
  suggested_model: string | null
  suggestion_source: 'migration_map' | 'task_default' | 'none'
}

interface HealthResponse {
  user_id: string
  deprecated_count: number
  deprecated: DeprecatedEntry[]
}

export default function DeprecatedPreferencesBanner() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [dismissed, setDismissed] = useState(false)
  const [migrating, setMigrating] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const fetchHealth = useCallback(async () => {
    try {
      const res = await http.get<HealthResponse>('/api/llm/preferences/health')
      setHealth(res.data)
    } catch {
      // Silent — ApiKeyStatusBanner already warns when the backend is down.
    }
  }, [])

  useEffect(() => {
    fetchHealth()
  }, [fetchHealth])

  const migrate = async () => {
    setMigrating(true)
    try {
      await http.post('/api/llm/preferences/migrate')
      await fetchHealth()
    } finally {
      setMigrating(false)
    }
  }

  if (dismissed) return null
  if (!health || health.deprecated_count === 0) return null

  const migratable = health.deprecated.filter(d => d.suggested_model !== null).length
  const orphan = health.deprecated_count - migratable

  return (
    <div className="bg-amber-500 text-white px-4 py-2">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0 flex-wrap">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          <span className="text-sm font-medium">
            {health.deprecated_count} saved model preference{health.deprecated_count > 1 ? 's' : ''} reference deprecated model{health.deprecated_count > 1 ? 's' : ''}.
          </span>
          {migratable > 0 && (
            <span className="text-sm opacity-90">
              {migratable} can be migrated automatically{orphan > 0 ? `, ${orphan} need manual attention` : ''}.
            </span>
          )}
          <button
            onClick={() => setExpanded(e => !e)}
            className="text-sm underline opacity-90 hover:opacity-100"
          >
            {expanded ? 'hide details' : 'show details'}
          </button>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {migratable > 0 && (
            <button
              onClick={migrate}
              disabled={migrating}
              className="flex items-center gap-1.5 bg-white text-amber-700 hover:bg-amber-50 disabled:opacity-50 disabled:cursor-not-allowed px-3 py-1 rounded text-sm font-medium"
            >
              {migrating ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Wand2 className="h-3.5 w-3.5" />
              )}
              Migrate {migratable}
            </button>
          )}
          <button
            onClick={() => setDismissed(true)}
            className="hover:bg-amber-600 p-1 rounded"
            title="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
      {expanded && (
        <div className="mt-2 text-xs space-y-1 max-h-40 overflow-y-auto">
          {health.deprecated.map((d, i) => (
            <div key={i} className="flex items-center gap-2 bg-amber-600/40 rounded px-2 py-1">
              <span className="font-mono">{d.task_type}</span>
              <span className="opacity-75">{d.current_model}</span>
              <span>→</span>
              {d.suggested_model ? (
                <>
                  <span className="font-mono">{d.suggested_model}</span>
                  <span className="opacity-60">
                    ({d.suggestion_source === 'migration_map' ? 'known rename' : 'task default'})
                  </span>
                </>
              ) : (
                <span className="italic opacity-75">no suggestion — pick manually</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
