/**
 * Shared HTTP client — the single transport seam between UI and backend.
 *
 * Components import this instead of axios directly, so base URL, timeouts,
 * interceptors and error normalization live in one place. Domain-specific
 * API modules (see conceptService.ts) should be built on top of it.
 */
import axios from 'axios'
import { API_BASE_URL } from '@/config/api'

const instance = axios.create({ baseURL: API_BASE_URL })

const http = Object.assign(instance, {
  isAxiosError: axios.isAxiosError,
  isCancel: axios.isCancel,
})

/** Human-readable message from an API error (FastAPI {detail} aware). */
export function apiErrorMessage(error: unknown, fallback = 'Request failed'): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail
    if (typeof detail === 'string' && detail) return detail
    return error.message || fallback
  }
  return error instanceof Error ? error.message : fallback
}

export default http
