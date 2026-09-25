import { useState, useEffect, useCallback, useRef } from 'react'
import http from '@/services/http'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Input } from '@/components/ui/input'
import {
  Columns,
  Plus,
  X,
  Loader2,
  Search,
  User,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Sparkles,
  FileText,
} from 'lucide-react'
import TweetCardModern from './TweetCardModern'
import TagSuggestionModalModern from '../concept-management/TagSuggestionModalModern'
import BatchAnnotationPanel from './BatchAnnotationPanel'
import { useBatchAnnotation } from './useBatchAnnotation'
import type { TwitterAccount } from '../twitter/types'
import type { Tweet, Concept } from '@/types/concept'

const COLUMN_PAGE_SIZE = 20
const STORAGE_KEY = 'tweetDeckColumns'
const SETTINGS_KEY = 'tweetdeck_columns'

const SUMMARY_PERIODS = [
  { value: '3days', label: '3 days' },
  { value: 'week', label: '1 week' },
  { value: '14days', label: '2 weeks' },
  { value: '30days', label: '30 days' },
  { value: '60days', label: '60 days' },
  { value: '90days', label: '90 days' },
  { value: 'all', label: 'All time' },
]

// --- Tweet transformation (same as FacetedTweetsDashboardModern) ---
function transformTweet(tweet: Tweet): Tweet {
  return {
    ...tweet,
    metrics: tweet.metrics
      ? {
          likes: tweet.metrics.like_count || tweet.metrics.likes || 0,
          retweets: tweet.metrics.retweet_count || tweet.metrics.retweets || 0,
          replies: tweet.metrics.reply_count || tweet.metrics.replies || 0,
          quotes: tweet.metrics.quote_count || tweet.metrics.quotes || 0,
        }
      : { likes: 0, retweets: 0, replies: 0, quotes: 0 },
    tags: tweet.tags
      ? tweet.tags.map((tag: any) =>
          typeof tag === 'string' ? { tag, type: 'manual' } : tag
        )
      : [],
  }
}

// =============================================================================
// TweetDeckColumn — one scrollable column per account
// =============================================================================

interface TweetDeckColumnProps {
  username: string
  displayName: string
  profileImageUrl?: string | null
  onRemove: () => void
  onSuggestConcepts: (tweet: Tweet) => void
  onTweetsLoaded?: (username: string, tweetIds: string[]) => void
  /** Model id from the toolbar selector; used when generating summaries. */
  summaryModel?: string
}

function TweetDeckColumn({
  username,
  displayName,
  profileImageUrl,
  onRemove,
  onSuggestConcepts,
  onTweetsLoaded,
  summaryModel,
}: TweetDeckColumnProps) {
  const [tweets, setTweets] = useState<Tweet[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [initialLoad, setInitialLoad] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Summary state with localStorage cache (4h TTL)
  const [summaryOpen, setSummaryOpen] = useState(false)
  const [summaryPeriod, setSummaryPeriod] = useState('30days')
  const [summary, setSummary] = useState<string | null>(null)
  const [summaryStats, setSummaryStats] = useState<{ tweet_count?: number } | null>(null)
  const [summaryModelUsed, setSummaryModelUsed] = useState('')
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [summaryDiagnostic, setSummaryDiagnostic] = useState<{
    auto_extended: boolean
    original_period_days?: number
    most_recent_date?: string | null
    days_since_most_recent?: number | null
    total_in_db?: { tweets: number; articles: number; papers: number }
    message: string
  } | null>(null)

  const SUMMARY_CACHE_TTL_MS = 4 * 60 * 60 * 1000 // 4 hours
  // Include model in key — switching models should bypass stale cache.
  const summaryCacheKey = `tweetdeck_summary_${username}_${summaryPeriod}_${summaryModel || 'default'}`

  // Restore cached summary on mount / period change
  useEffect(() => {
    try {
      const cached = localStorage.getItem(summaryCacheKey)
      if (cached) {
        const parsed = JSON.parse(cached)
        const age = Date.now() - (parsed.timestamp || 0)
        if (age < SUMMARY_CACHE_TTL_MS) {
          setSummary(parsed.summary)
          setSummaryStats(parsed.stats)
          setSummaryModelUsed(parsed.model_used || '')
          setSummaryDiagnostic(parsed.diagnostic || null)
          return
        }
        localStorage.removeItem(summaryCacheKey)
      }
    } catch {
      // ignore
    }
    setSummary(null)
    setSummaryStats(null)
    setSummaryModelUsed('')
    setSummaryDiagnostic(null)
  }, [summaryCacheKey])

  const generateSummary = async (forceRefresh = false) => {
    // Use cache unless force refresh
    if (!forceRefresh) {
      try {
        const cached = localStorage.getItem(summaryCacheKey)
        if (cached) {
          const parsed = JSON.parse(cached)
          const age = Date.now() - (parsed.timestamp || 0)
          if (age < SUMMARY_CACHE_TTL_MS) {
            setSummary(parsed.summary)
            setSummaryStats(parsed.stats)
            setSummaryModelUsed(parsed.model_used || '')
            setSummaryDiagnostic(parsed.diagnostic || null)
            setSummaryOpen(true)
            return
          }
        }
      } catch {
        // ignore
      }
    }

    setSummaryLoading(true)
    setSummary(null)
    try {
      const params = new URLSearchParams({
        period: summaryPeriod,
        author: username,
        include_tweets: 'true',
        include_articles: 'false',
        include_papers: 'false',
        detail_level: 'brief',
        // The period drives the volume; cap is just a safety ceiling.
        max_tweets: '2000',
        full_content: 'true',
      })
      if (summaryModel) params.append('model', summaryModel)
      const response = await http.post(
        `/api/analytics/trends/summarize?${params}`,
        null,
        { timeout: 120000 }
      )
      const summaryText = response.data.summary
      const stats = response.data.stats
      const modelUsed = response.data.model_used || ''
      const diagnostic = response.data.diagnostic || null

      setSummary(summaryText)
      setSummaryStats(stats)
      setSummaryModelUsed(modelUsed)
      setSummaryDiagnostic(diagnostic)
      setSummaryOpen(true)

      // Cache to localStorage
      try {
        localStorage.setItem(summaryCacheKey, JSON.stringify({
          summary: summaryText,
          stats,
          model_used: modelUsed,
          diagnostic,
          timestamp: Date.now(),
        }))
      } catch {
        // localStorage full — ignore
      }
    } catch {
      setSummary('Failed to generate summary. Please try again.')
    } finally {
      setSummaryLoading(false)
    }
  }

  // Listen for tweet concept updates (from shared suggestion modal)
  useEffect(() => {
    const handler = (e: Event) => {
      const { tweetId, concepts } = (e as CustomEvent).detail || {}
      if (tweetId) {
        setTweets(prev =>
          prev.map(t => (t.id === tweetId ? { ...t, concepts } : t))
        )
      }
    }
    window.addEventListener('tweetdeck-tweet-updated', handler)
    return () => window.removeEventListener('tweetdeck-tweet-updated', handler)
  }, [])

  const fetchTweets = useCallback(
    async (pageNum: number, append = false) => {
      setLoading(true)
      try {
        const params = new URLSearchParams({
          page: pageNum.toString(),
          page_size: COLUMN_PAGE_SIZE.toString(),
        })
        params.append('authors', username)

        const response = await http.get(
          `/api/tweets/faceted-search?${params.toString()}`
        )

        const transformed = response.data.tweets.map(transformTweet)

        if (append) {
          setTweets(prev => [...prev, ...transformed])
        } else {
          setTweets(transformed)
        }
        setTotal(response.data.total)
      } catch (error) {
        console.error(`Error fetching tweets for @${username}:`, error)
      } finally {
        setLoading(false)
        setInitialLoad(false)
      }
    },
    [username]
  )

  // Report tweet IDs to parent whenever tweets change
  useEffect(() => {
    onTweetsLoaded?.(username, tweets.map(t => t.id))
  }, [tweets, username, onTweetsLoaded])

  // Listen for refresh-all events (after batch annotation)
  useEffect(() => {
    const handler = () => {
      setPage(1)
      fetchTweets(1)
    }
    window.addEventListener('tweetdeck-refresh-all', handler)
    return () => window.removeEventListener('tweetdeck-refresh-all', handler)
  }, [fetchTweets])

  useEffect(() => {
    setPage(1)
    setTweets([])
    setInitialLoad(true)
    fetchTweets(1)
  }, [username, fetchTweets])

  const loadMore = () => {
    const nextPage = page + 1
    setPage(nextPage)
    fetchTweets(nextPage, true)
  }

  const refresh = () => {
    setPage(1)
    fetchTweets(1)
    scrollRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleConceptAdded = (_tweetId: string, concept: Concept) => {
    setTweets(prev =>
      prev.map(t =>
        t.id === _tweetId
          ? { ...t, concepts: [...(t.concepts || []), concept] }
          : t
      )
    )
  }

  const handleConceptRemoved = (_tweetId: string, conceptId: string) => {
    setTweets(prev =>
      prev.map(t =>
        t.id === _tweetId
          ? { ...t, concepts: t.concepts?.filter(c => c.concept_id !== conceptId) }
          : t
      )
    )
  }

  const hasMore = tweets.length < total

  return (
    <div className="flex-shrink-0 w-[400px] flex flex-col bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm h-full">
      {/* Column Header */}
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 rounded-t-xl">
        <div className="flex items-center gap-2 min-w-0">
          {profileImageUrl ? (
            <img
              src={profileImageUrl}
              alt={username}
              className="w-7 h-7 rounded-full flex-shrink-0"
              onError={e => {
                ;(e.target as HTMLImageElement).style.display = 'none'
              }}
            />
          ) : (
            <div className="w-7 h-7 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
          )}
          <div className="min-w-0">
            <div className="text-sm font-semibold truncate">
              @{username}
            </div>
            {displayName !== username && (
              <div className="text-xs text-gray-500 truncate">{displayName}</div>
            )}
          </div>
          <Badge variant="secondary" className="ml-1 text-xs flex-shrink-0">
            {total}
          </Badge>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={refresh}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded transition-colors"
            title="Refresh column"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading && !initialLoad ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={onRemove}
            className="p-1 text-gray-400 hover:text-red-500 rounded transition-colors"
            title="Remove column"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Collapsible Summary Section */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        {/* Summary Header Bar */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50/50 dark:bg-gray-800/30">
          <button
            onClick={() => {
              if (summary) {
                setSummaryOpen(!summaryOpen)
              } else {
                generateSummary()
              }
            }}
            className="flex items-center gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors"
          >
            {summaryLoading ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : summaryOpen ? (
              <ChevronDown className="w-3 h-3" />
            ) : (
              <ChevronRight className="w-3 h-3" />
            )}
            <FileText className="w-3 h-3" />
            Summary
          </button>

          <select
            value={summaryPeriod}
            onChange={e => {
              setSummaryPeriod(e.target.value)
              setSummary(null)
              setSummaryOpen(false)
            }}
            className="text-xs bg-transparent border border-gray-200 dark:border-gray-600 rounded px-1.5 py-0.5 text-gray-600 dark:text-gray-400 focus:outline-none focus:ring-1 focus:ring-purple-400"
            onClick={e => e.stopPropagation()}
          >
            {SUMMARY_PERIODS.map(p => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>

          <button
            onClick={() => generateSummary(!!summary)}
            disabled={summaryLoading}
            className="ml-auto flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-900/60 transition-colors disabled:opacity-50"
          >
            <Sparkles className="w-3 h-3" />
            {summaryLoading ? 'Generating...' : summary ? 'Refresh' : 'Generate'}
          </button>
        </div>

        {/* Summary Content (expanded) */}
        {summaryOpen && summary && (
          <div className="px-3 py-2 bg-purple-50/50 dark:bg-purple-900/10 max-h-[260px] overflow-y-auto">
            {summaryDiagnostic && summaryDiagnostic.auto_extended && (
              <div className="mb-2 px-2 py-1.5 rounded border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20 text-[11px] text-amber-900 dark:text-amber-200 leading-snug">
                <span className="font-semibold">No recent activity:</span> {summaryDiagnostic.message}
              </div>
            )}
            {summaryDiagnostic && !summaryDiagnostic.auto_extended &&
              summaryDiagnostic.total_in_db &&
              (summaryDiagnostic.total_in_db.tweets +
                summaryDiagnostic.total_in_db.articles +
                summaryDiagnostic.total_in_db.papers) === 0 && (
              <div className="mb-2 px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/40 text-[11px] text-gray-700 dark:text-gray-300 leading-snug">
                {summaryDiagnostic.message}
              </div>
            )}
            <div className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
              {summary}
            </div>
            {summaryStats && (
              <div className="flex items-center gap-3 mt-2 pt-2 border-t border-purple-200/50 dark:border-purple-800/30">
                {summaryStats.tweet_count != null && (
                  <span className="text-[10px] text-purple-600 dark:text-purple-400">
                    {summaryStats.tweet_count} tweets analyzed
                  </span>
                )}
                {summaryModelUsed && (
                  <span className="text-[10px] text-gray-400">
                    {summaryModelUsed}
                  </span>
                )}
                {(() => {
                  try {
                    const cached = localStorage.getItem(summaryCacheKey)
                    if (cached) {
                      const age = Date.now() - JSON.parse(cached).timestamp
                      const hours = Math.floor(age / 3600000)
                      const mins = Math.floor((age % 3600000) / 60000)
                      return (
                        <span className="text-[10px] text-gray-400 ml-auto">
                          {hours > 0 ? `${hours}h ${mins}m ago` : `${mins}m ago`}
                        </span>
                      )
                    }
                  } catch { /* ignore */ }
                  return null
                })()}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Scrollable Tweet List */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-2 space-y-3">
        {initialLoad && loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          </div>
        ) : tweets.length === 0 ? (
          <div className="text-center py-12 text-gray-400 text-sm">
            No tweets found
          </div>
        ) : (
          <>
            {tweets.map(tweet => (
              <TweetCardModern
                key={tweet.id}
                tweet={tweet}
                onConceptAdded={handleConceptAdded}
                onConceptRemoved={handleConceptRemoved}
                onSuggestConcepts={t => onSuggestConcepts(t)}
              />
            ))}

            {hasMore && (
              <div className="py-3 text-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadMore}
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <ChevronDown className="w-4 h-4 mr-2" />
                  )}
                  Load More ({tweets.length}/{total})
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// TweetDeckView — main orchestrator
// =============================================================================

export default function TweetDeckView() {
  const [columns, setColumns] = useState<string[]>([])
  const [accounts, setAccounts] = useState<TwitterAccount[]>([])
  const [accountSearch, setAccountSearch] = useState('')
  const [selectorOpen, setSelectorOpen] = useState(false)
  // Guard against persisting before initial restore finishes — otherwise
  // an empty initial state would overwrite saved columns on first render.
  const restoredRef = useRef(false)

  // Shared suggestion modal state
  const [selectedTweet, setSelectedTweet] = useState<Tweet | null>(null)
  const [showSuggestionModal, setShowSuggestionModal] = useState(false)

  // Annotation status facets (for "Annotate All Unannotated" count)
  const [annotationFacets, setAnnotationFacets] = useState<any[]>([])

  const fetchAnnotationFacets = useCallback(async () => {
    try {
      const response = await http.get('/api/tweets/faceted-search?page=1&page_size=1')
      setAnnotationFacets(response.data.facets?.annotation_status || [])
    } catch {
      // ignore
    }
  }, [])

  // Batch annotation: collect tweet IDs from all columns
  const columnTweetIds = useRef<Map<string, string[]>>(new Map())

  const refreshAllColumns = useCallback(() => {
    window.dispatchEvent(new Event('tweetdeck-refresh-all'))
    // Also refresh annotation facets after batch operations
    setTimeout(fetchAnnotationFacets, 1000)
  }, [fetchAnnotationFacets])

  const batch = useBatchAnnotation(refreshAllColumns)

  const handleTweetsLoaded = useCallback((username: string, tweetIds: string[]) => {
    columnTweetIds.current.set(username, tweetIds)
  }, [])

  const getAllTweetIds = useCallback((): string[] => {
    const allIds: string[] = []
    columnTweetIds.current.forEach(ids => allIds.push(...ids))
    return allIds
  }, [])

  // Fetch annotation facets on mount and when columns change
  useEffect(() => {
    if (columns.length > 0) {
      fetchAnnotationFacets()
    }
  }, [columns.length, fetchAnnotationFacets])

  // Load accounts + restore columns (backend-first, localStorage fallback).
  // Persistence is gated by `restoredRef` so the initial empty state cannot
  // overwrite saved columns before the restore actually runs.
  useEffect(() => {
    let cancelled = false

    const restore = async () => {
      // 1. Fetch accounts (used both for the picker and for validation/logging).
      let accs: TwitterAccount[] = []
      try {
        const res = await http.get('/api/twitter-accounts/')
        accs = res.data.accounts || res.data || []
      } catch (err) {
        console.error('Error fetching accounts:', err)
      }
      if (cancelled) return
      setAccounts(accs)

      // 2. Try backend first (survives browser/origin/machine changes).
      let savedColumns: string[] | null = null
      try {
        const res = await http.get(`/api/user-settings/${SETTINGS_KEY}`)
        if (res.data?.exists && Array.isArray(res.data.value)) {
          savedColumns = res.data.value as string[]
        }
      } catch (err) {
        console.warn('Backend column restore failed, falling back to localStorage:', err)
      }
      if (cancelled) return

      // 3. Fallback to localStorage if backend had nothing.
      if (!savedColumns) {
        const local = localStorage.getItem(STORAGE_KEY)
        if (local) {
          try {
            const parsed = JSON.parse(local)
            if (Array.isArray(parsed)) savedColumns = parsed as string[]
          } catch {
            // malformed localStorage — ignore
          }
        }
      }

      // 4. Apply. Do NOT silently filter columns out when accounts are empty
      //    or when a username temporarily doesn't appear in /api/twitter-accounts
      //    (e.g. after a DB sync hiccup) — that's exactly how the previous
      //    bug wiped the whole layout. Only filter once we're confident the
      //    account list is real.
      if (savedColumns && savedColumns.length > 0) {
        if (accs.length > 0) {
          const validUsernames = new Set(accs.map(a => a.username))
          const kept = savedColumns.filter(u => validUsernames.has(u))
          const dropped = savedColumns.filter(u => !validUsernames.has(u))
          if (dropped.length > 0) {
            console.warn(
              `TweetDeck: ${dropped.length} saved column(s) not found in /api/twitter-accounts: ${dropped.join(', ')}. Keeping them anyway so they reappear when the account does.`
            )
          }
          // Keep the unknowns too — if the account comes back, the column is restored.
          setColumns([...kept, ...dropped])
        } else {
          // Account list empty/failed — restore as-is, don't wipe.
          setColumns(savedColumns)
        }
      }

      restoredRef.current = true
    }

    restore()
    return () => {
      cancelled = true
    }
  }, [])

  // Persist columns to BOTH localStorage and backend, but only after restore.
  useEffect(() => {
    if (!restoredRef.current) return
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(columns))
    } catch {
      // localStorage full — ignore
    }
    http
      .put(`/api/user-settings/${SETTINGS_KEY}`, { value: columns })
      .catch(err => console.warn('Failed to persist TweetDeck columns to backend:', err))
  }, [columns])

  const addColumn = (username: string) => {
    if (!columns.includes(username)) {
      setColumns(prev => [...prev, username])
    }
  }

  const removeColumn = (username: string) => {
    setColumns(prev => prev.filter(u => u !== username))
  }

  const handleSuggestConcepts = (tweet: Tweet) => {
    setSelectedTweet(tweet)
    setShowSuggestionModal(true)
  }

  const handleTagsUpdated = async () => {
    // Refresh the tweet in the specific column
    if (selectedTweet) {
      try {
        const response = await http.get(`/api/tweets/${selectedTweet.id}`)
        const updatedTweet = transformTweet(response.data)
        // Dispatch a custom event that the column can listen to
        window.dispatchEvent(
          new CustomEvent('tweetdeck-tweet-updated', {
            detail: { tweetId: selectedTweet.id, concepts: updatedTweet.concepts },
          })
        )
      } catch (error) {
        console.error('Error fetching updated tweet:', error)
      }
    }
    setShowSuggestionModal(false)
    setSelectedTweet(null)
  }

  const normalizedSearch = accountSearch.trim().replace(/^@/, '').toLowerCase()
  const filteredAccounts = accounts.filter(
    a =>
      a.username.toLowerCase().includes(normalizedSearch) ||
      a.display_name.toLowerCase().includes(normalizedSearch)
  )

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 flex-shrink-0">
        <div className="flex items-center gap-3">
          <Columns className="w-5 h-5 text-blue-600" />
          <h1 className="text-lg font-semibold">TweetDeck</h1>
          {columns.length > 0 && (
            <Badge variant="secondary">{columns.length} columns</Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Refresh All Button */}
          {columns.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                refreshAllColumns()
                fetchAnnotationFacets()
              }}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh All
            </Button>
          )}

          {/* Account Selector */}
          <Popover open={selectorOpen} onOpenChange={setSelectorOpen}>
            <PopoverTrigger asChild>
            <Button variant="outline" size="sm">
              <Plus className="w-4 h-4 mr-2" />
              Add Column
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-72 p-0" align="end">
            <div className="p-2 border-b">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search accounts..."
                  value={accountSearch}
                  onChange={e => setAccountSearch(e.target.value)}
                  className="pl-8 h-9"
                />
              </div>
            </div>
            <div className="max-h-64 overflow-y-auto p-1">
              {filteredAccounts.length === 0 ? (
                <div className="text-center py-4 text-sm text-gray-400">
                  No accounts found
                </div>
              ) : (
                filteredAccounts.map(account => {
                  const isActive = columns.includes(account.username)
                  return (
                    <button
                      key={account.username}
                      onClick={() => {
                        if (isActive) {
                          removeColumn(account.username)
                        } else {
                          addColumn(account.username)
                        }
                      }}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-left text-sm transition-colors ${
                        isActive
                          ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isActive}
                        readOnly
                        className="h-4 w-4 rounded border-gray-300 text-blue-600 pointer-events-none"
                      />
                      {account.profile_image_url ? (
                        <img
                          src={account.profile_image_url}
                          alt=""
                          className="w-6 h-6 rounded-full flex-shrink-0"
                        />
                      ) : (
                        <div className="w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">
                          <User className="w-3 h-3 text-gray-500" />
                        </div>
                      )}
                      <div className="min-w-0 flex-1">
                        <div className="font-medium truncate">
                          @{account.username}
                        </div>
                        <div className="text-xs text-gray-500 truncate">
                          {account.display_name}
                          {account.tweets_collected > 0 &&
                            ` · ${account.tweets_collected} tweets`}
                        </div>
                      </div>
                    </button>
                  )
                })
              )}
            </div>
          </PopoverContent>
          </Popover>
        </div>
      </div>

      {/* Batch Annotation Panel */}
      {columns.length > 0 && (
        <div className="px-6 py-2 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 flex-shrink-0">
          <BatchAnnotationPanel
            tweetCount={getAllTweetIds().length}
            annotationStatusFacets={annotationFacets}
            batchAnnotating={batch.batchAnnotating}
            batchProgress={batch.batchProgress}
            batchModel={batch.batchModel}
            setBatchModel={batch.setBatchModel}
            batchResult={batch.batchResult}
            annotateAllRunning={batch.annotateAllRunning}
            annotateAllProgress={batch.annotateAllProgress}
            annotateAllResult={batch.annotateAllResult}
            onBatchAnnotate={() => batch.handleBatchAnnotate(getAllTweetIds())}
            onAnnotateAll={batch.handleAnnotateAll}
            onCancelAnnotateAll={batch.handleCancelAnnotateAll}
          />
        </div>
      )}

      {/* Columns Container */}
      {columns.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-4">
            <Columns className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600" />
            <div>
              <h2 className="text-xl font-semibold text-gray-600 dark:text-gray-400">
                No columns yet
              </h2>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                Click "Add Column" to select accounts and create your TweetDeck view
              </p>
            </div>
            <Popover>
              <PopoverTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Your First Column
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-72 p-0">
                <div className="p-2 border-b">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search accounts..."
                      value={accountSearch}
                      onChange={e => setAccountSearch(e.target.value)}
                      className="pl-8 h-9"
                    />
                  </div>
                </div>
                <div className="max-h-64 overflow-y-auto p-1">
                  {filteredAccounts.map(account => (
                    <button
                      key={account.username}
                      onClick={() => addColumn(account.username)}
                      className="w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                      <User className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <div className="min-w-0">
                        <div className="font-medium">@{account.username}</div>
                        <div className="text-xs text-gray-500">{account.display_name}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </PopoverContent>
            </Popover>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-x-auto p-4">
          <div className="flex gap-4 h-full">
            {columns.map(username => {
              const account = accounts.find(a => a.username === username)
              return (
                <TweetDeckColumn
                  key={username}
                  username={username}
                  displayName={account?.display_name || username}
                  profileImageUrl={account?.profile_image_url}
                  onRemove={() => removeColumn(username)}
                  onSuggestConcepts={handleSuggestConcepts}
                  onTweetsLoaded={handleTweetsLoaded}
                  summaryModel={batch.batchModel}
                />
              )
            })}
          </div>
        </div>
      )}

      {/* Shared Tag Suggestion Modal */}
      {selectedTweet && (
        <TagSuggestionModalModern
          contentId={selectedTweet.id}
          contentType="tweet"
          contentPreview={selectedTweet.text}
          isOpen={showSuggestionModal}
          onClose={() => {
            setShowSuggestionModal(false)
            setSelectedTweet(null)
          }}
          onTagsUpdated={handleTagsUpdated}
        />
      )}
    </div>
  )
}

