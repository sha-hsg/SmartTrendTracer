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

// The backend stores UTC and serialises many timestamps without a zone
// ("2026-10-09T04:28:23", from naive PyMongo datetimes). Browsers read such
// strings as *local* time, so every tweet time showed 2 h early in CEST.
// Mark zone-less ISO date-times as UTC once, here at the transport seam.
const NAIVE_ISO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/

export function markNaiveTimestampsUtc(value: unknown): unknown {
  if (typeof value === 'string') return NAIVE_ISO.test(value) ? `${value}Z` : value
  if (Array.isArray(value)) {
    for (let i = 0; i < value.length; i++) value[i] = markNaiveTimestampsUtc(value[i])
    return value
  }
  if (value && typeof value === 'object') {
    const obj = value as Record<string, unknown>
    for (const key of Object.keys(obj)) obj[key] = markNaiveTimestampsUtc(obj[key])
  }
  return value
}

instance.interceptors.response.use((response) => {
  if (response.data && typeof response.data === 'object') markNaiveTimestampsUtc(response.data)
  return response
})

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
