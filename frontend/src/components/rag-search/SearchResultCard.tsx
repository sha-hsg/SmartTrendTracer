import ReactMarkdown from 'react-markdown'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  Twitter,
  Newspaper,
  User,
  Calendar,
  Hash,
  FileText,
  ExternalLink,
  GraduationCap,
} from 'lucide-react'
import { cn } from "@/lib/utils"

export interface Source {
  type: 'tweet' | 'article' | 'snippet' | 'paper'
  id: string
  paper_id?: string
  score: number
  content_preview: string
  content?: string
  metadata: any
  navigate_to?: string
  display_title?: string
  url?: string
  author?: string
  created_at?: string
  published_at?: string
  tags?: string[]
  title?: string
  annotation?: string
  article_id?: string
  category?: string
  authors?: string[] | string
  conference?: string
}

export const getSourceIcon = (type: string) => {
  switch (type) {
    case 'tweet': return <Twitter className="w-4 h-4" />
    case 'article': return <Newspaper className="w-4 h-4" />
    case 'paper': return <GraduationCap className="w-4 h-4" />
    case 'snippet': return <FileText className="w-4 h-4" />
    default: return <FileText className="w-4 h-4" />
  }
}

export const formatDate = (dateString?: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

export const getRelevanceColor = (score: number) => {
  if (score > 0.8) return 'bg-green-500'
  if (score > 0.6) return 'bg-blue-500'
  if (score > 0.4) return 'bg-yellow-500'
  return 'bg-gray-500'
}

export const getRelevanceLabel = (score: number) => {
  if (score > 0.8) return 'Very High'
  if (score > 0.6) return 'High'
  if (score > 0.4) return 'Medium'
  return 'Low'
}

interface SearchResultCardProps {
  source: Source
  onNavigate: () => void
}

export default function SearchResultCard({ source, onNavigate }: SearchResultCardProps) {
  return (
    <Card
      className="cursor-pointer hover:shadow-lg transition-shadow hover:border-blue-300 dark:hover:border-blue-700"
      onClick={(e) => {
        if (e.target === e.currentTarget ||
            !e.currentTarget.contains(e.target as Node) ||
            (e.target as HTMLElement).closest('button') === null) {
          onNavigate()
        }
      }}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 flex-1">
            {getSourceIcon(source.type)}
            <span className="font-medium text-sm">
              {source.type === 'paper'
                ? (source.metadata?.title || source.title || 'Research Paper')
                : (source.display_title || source.title || source.type)}
            </span>
          </div>
          <Badge
            className={cn(
              "text-xs text-white",
              getRelevanceColor(source.score)
            )}
          >
            {getRelevanceLabel(source.score)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-sm text-muted-foreground line-clamp-3">
          {source.type === 'article' ? (
            <div className="prose prose-sm dark:prose-invert">
              <ReactMarkdown>
                {source.content_preview || source.content || 'No preview available'}
              </ReactMarkdown>
            </div>
          ) : (
            source.content_preview || source.content || 'No preview available'
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
          {source.type === 'tweet' && (
            <>
              {source.author && (
                <div className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  @{source.author}
                </div>
              )}
              {source.created_at && (
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {formatDate(source.created_at)}
                </div>
              )}
              {source.tags && source.tags.length > 0 && (
                <div className="flex items-center gap-1">
                  <Hash className="w-3 h-3" />
                  {source.tags.slice(0, 3).join(', ')}
                </div>
              )}
            </>
          )}

          {source.type === 'article' && (
            <>
              {source.author && (
                <div className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  {source.author}
                </div>
              )}
              {source.published_at && (
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {formatDate(source.published_at)}
                </div>
              )}
            </>
          )}

          {source.type === 'paper' && (
            <>
              {(source.metadata?.authors || source.authors) && (
                <div className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  {Array.isArray(source.metadata?.authors)
                    ? source.metadata.authors.slice(0, 2).join(', ')
                    : Array.isArray(source.authors)
                    ? source.authors.slice(0, 2).join(', ')
                    : source.metadata?.authors || source.authors}
                  {((source.metadata?.authors?.length || source.authors?.length) > 2) && ' et al.'}
                </div>
              )}
              {(source.metadata?.publication_date || source.published_at) && (
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {formatDate(source.metadata?.publication_date || source.published_at)}
                </div>
              )}
              {(source.metadata?.conference || source.conference) && (
                <div className="flex items-center gap-1">
                  <GraduationCap className="w-3 h-3" />
                  {source.metadata?.conference || source.conference}
                </div>
              )}
              {(source.metadata?.tags || source.tags) && (source.metadata?.tags || source.tags).length > 0 && (
                <div className="flex items-center gap-1">
                  <Hash className="w-3 h-3" />
                  {(source.metadata?.tags || source.tags).slice(0, 3).join(', ')}
                </div>
              )}
            </>
          )}

          {source.type === 'snippet' && source.annotation && (
            <div className="flex items-center gap-1">
              <FileText className="w-3 h-3" />
              {source.annotation}
            </div>
          )}
        </div>

        <div className="flex justify-end">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                  onClick={(e) => {
                    e.stopPropagation()
                    onNavigate()
                  }}
                >
                  {source.type === 'tweet' ? (
                    <>
                      <Twitter className="w-3 h-3" />
                      View on X
                    </>
                  ) : source.type === 'article' ? (
                    <>
                      <FileText className="w-3 h-3" />
                      Read Article
                    </>
                  ) : (
                    <>
                      <Newspaper className="w-3 h-3" />
                      View Snippet
                    </>
                  )}
                  <ExternalLink className="w-3 h-3" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p className="text-xs">
                  {source.type === 'tweet' ? 'Open tweet in X/Twitter' :
                   source.type === 'article' ? 'Open article in viewer' :
                   'View snippet in article context'}
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </CardContent>
    </Card>
  )
}
