import React, { useEffect, useState } from 'react'
import { AlertTriangle, X } from 'lucide-react'
import axios from 'axios'

interface ApiKeyStatus {
  status: string
  configured_count: number
  total_providers: number
  all_configured: boolean
  missing: Array<{ provider: string; env_var: string }>
  message: string
}

export default function ApiKeyStatusBanner() {
  const [status, setStatus] = useState<ApiKeyStatus | null>(null)
  const [dismissed, setDismissed] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/llm/status')
        setStatus(response.data)
        setError(null)
      } catch (err) {
        if (axios.isAxiosError(err) && err.code === 'ERR_NETWORK') {
          setError('Backend server not running')
        } else {
          setError('Failed to check API key status')
        }
      }
    }

    checkStatus()
  }, [])

  // Don't show if dismissed or all keys are configured
  if (dismissed) return null

  // Show error banner if backend is not running
  if (error) {
    return (
      <div className="bg-red-600 text-white px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          <span className="text-sm font-medium">{error}</span>
          <span className="text-sm opacity-80">- Start with ./start_stt.sh</span>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="hover:bg-red-700 p-1 rounded"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    )
  }

  // Still loading
  if (!status) return null

  // All configured - show green success briefly or not at all
  if (status.all_configured) {
    return null // Don't show anything if all good
  }

  // Show warning for missing keys
  return (
    <div className="bg-amber-500 text-white px-4 py-2 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4" />
        <span className="text-sm font-medium">
          Missing API Keys ({status.total_providers - status.configured_count}/{status.total_providers}):
        </span>
        <span className="text-sm">
          {status.missing.map(m => m.provider).join(', ')}
        </span>
        <span className="text-sm opacity-80">- Add to ~/.env</span>
      </div>
      <button
        onClick={() => setDismissed(true)}
        className="hover:bg-amber-600 p-1 rounded"
        title="Dismiss warning"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}
