import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  Search, 
  Sparkles, 
  X, 
  Loader2,
  Hash,
  User,
  Building,
  MapPin,
  Calendar,
  Package
} from 'lucide-react'
import { cn } from "@/lib/utils"

interface ConceptSearchResult {
  concept_id: string
  display_name: string
  slug: string
  entity_type: string
  icon?: string
  description?: string
  total_usage: number
  content_types: string[]
  usage_by_type: Record<string, number>
  similarity_score: number
}

interface SemanticConceptSearchProps {
  onConceptSelect: (conceptId: string, displayName: string) => void
  selectedConcepts?: string[]
  contentTypes?: string[] // Filter by content types: 'tweet', 'article', 'paper'
  placeholder?: string
  className?: string
}

const getEntityIcon = (entityType: string) => {
  switch (entityType) {
    case 'person':
      return <User className="h-3 w-3" />
    case 'organisation':
      return <Building className="h-3 w-3" />
    case 'location':
      return <MapPin className="h-3 w-3" />
    case 'event':
      return <Calendar className="h-3 w-3" />
    case 'product':
      return <Package className="h-3 w-3" />
    default:
      return <Hash className="h-3 w-3" />
  }
}

const getEntityColor = (entityType: string) => {
  switch (entityType) {
    case 'person':
      return 'bg-green-100 text-green-800 border-green-200'
    case 'organisation':
      return 'bg-blue-100 text-blue-800 border-blue-200'
    case 'location':
      return 'bg-purple-100 text-purple-800 border-purple-200'
    case 'event':
      return 'bg-orange-100 text-orange-800 border-orange-200'
    case 'product':
      return 'bg-pink-100 text-pink-800 border-pink-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

export default function SemanticConceptSearch({
  onConceptSelect,
  selectedConcepts = [],
  contentTypes = ['tweet', 'article', 'paper'],
  placeholder = "Search concepts semantically...",
  className = ""
}: SemanticConceptSearchProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<ConceptSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const searchRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query.trim().length > 2) {
        searchConcepts()
      } else {
        setResults([])
        setShowResults(false)
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [query, contentTypes])

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const searchConcepts = async () => {
    if (query.trim().length < 3) return

    setLoading(true)
    setError(null)
    
    try {
      const params = new URLSearchParams()
      params.append('query', query.trim())
      params.append('limit', '10')
      
      // Add content type filters
      contentTypes.forEach(type => {
        params.append('content_types', type)
      })

      const response = await axios.get(
        `/api/concepts/suggestions/search-concepts?${params}`
      )

      setResults(response.data.results || [])
      setShowResults(true)
    } catch (error) {
      console.error('Error searching concepts:', error)
      setError('Failed to search concepts')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handleConceptSelect = (concept: ConceptSearchResult) => {
    onConceptSelect(concept.concept_id, concept.display_name)
    setQuery('')
    setResults([])
    setShowResults(false)
    inputRef.current?.blur()
  }

  const clearSearch = () => {
    setQuery('')
    setResults([])
    setShowResults(false)
    inputRef.current?.focus()
  }

  return (
    <div className={cn("relative", className)} ref={searchRef}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
        <Input
          ref={inputRef}
          type="text"
          placeholder={placeholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (results.length > 0) {
              setShowResults(true)
            }
          }}
          className="pl-10 pr-20"
        />
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
          {loading && <Loader2 className="h-3 w-3 animate-spin text-gray-400" />}
          <Sparkles className="h-3 w-3 text-purple-400" />
          {query && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearSearch}
              className="h-6 w-6 p-0 hover:bg-gray-100"
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>

      {/* Search Results Dropdown */}
      {showResults && (
        <Card className="absolute top-full left-0 right-0 mt-1 z-50 border shadow-lg bg-white">
          <CardContent className="p-0">
            {error ? (
              <div className="p-4 text-center text-red-600 text-sm">
                {error}
              </div>
            ) : results.length === 0 ? (
              <div className="p-4 text-center text-gray-500 text-sm">
                {loading ? 'Searching...' : 'No concepts found'}
              </div>
            ) : (
              <ScrollArea className="max-h-64">
                <div className="p-2">
                  {results.map((concept, index) => {
                    const isSelected = selectedConcepts.includes(concept.concept_id)
                    
                    return (
                      <div
                        key={`${concept.concept_id}-${index}`}
                        className={cn(
                          "flex items-center justify-between p-2 rounded-md cursor-pointer transition-colors",
                          isSelected 
                            ? "bg-blue-50 border border-blue-200" 
                            : "hover:bg-gray-50",
                          isSelected && "opacity-60 pointer-events-none"
                        )}
                        onClick={() => !isSelected && handleConceptSelect(concept)}
                      >
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <div className="flex-shrink-0">
                            {getEntityIcon(concept.entity_type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-sm truncate">
                                {concept.display_name}
                              </span>
                              <Badge 
                                variant="outline" 
                                className={cn("text-xs", getEntityColor(concept.entity_type))}
                              >
                                {concept.entity_type}
                              </Badge>
                            </div>
                            {concept.description && (
                              <p className="text-xs text-gray-500 mt-0.5 truncate">
                                {concept.description}
                              </p>
                            )}
                            <div className="flex items-center gap-1 mt-1">
                              {concept.content_types.map(type => (
                                <span 
                                  key={type}
                                  className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded"
                                >
                                  {type}: {concept.usage_by_type[type] || 0}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className="text-xs text-purple-600 font-medium">
                            {concept.similarity_score}%
                          </span>
                          {isSelected && (
                            <Badge variant="secondary" className="text-xs">
                              Selected
                            </Badge>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}