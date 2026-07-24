import ReactMarkdown from 'react-markdown'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Sparkles,
  FileText,
  User,
  Heart,
  Repeat2,
  Calendar,
  Hash,
  AlertCircle,
  Twitter,
  BookOpen,
  Check,
  Copy,
  Download,
  RefreshCw,
} from 'lucide-react'

interface SummaryData {
  summary: string
  stats: {
    tweet_count: number
    article_count: number
    paper_count: number
    unique_authors: number
    total_likes: number
    total_retweets: number
    time_range: {
      start: string | null
      end: string | null
    }
    total_available?: {
      tweets: number
      articles: number
      papers: number
    }
  }
  filters: {
    period: string | null
    tags: string[] | null
    author: string | null
  }
  model_used?: string
  data_truncated?: boolean
  truncation_warning?: string | null
}

interface SummarizationResultProps {
  summaryData: SummaryData
  copied: boolean
  copyToClipboard: () => void
  onRegenerate: () => void
  loading: boolean
}

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleString()
}

const getModelIcon = (model?: string) => {
  if (!model) return null
  if (model.includes('gpt')) return '🤖'
  if (model.includes('claude')) return '🎭'
  if (model.includes('gemini')) return '💎'
  return '✨'
}

export default function SummarizationResult({
  summaryData,
  copied,
  copyToClipboard,
  onRegenerate,
  loading,
}: SummarizationResultProps) {
  const wordCount = summaryData.summary ? summaryData.summary.split(/\s+/).filter(Boolean).length : 0

  const downloadMarkdown = () => {
    const date = new Date().toISOString().split('T')[0]
    const blob = new Blob([summaryData.summary], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `summary_${date}.md`
    a.click()
    URL.revokeObjectURL(url)
  }
  return (
    <div className="space-y-4">
      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Tweets</p>
                <p className="text-2xl font-bold">{summaryData.stats.tweet_count}</p>
              </div>
              <Twitter className="h-8 w-8 text-blue-400 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Articles</p>
                <p className="text-2xl font-bold">{summaryData.stats.article_count || 0}</p>
              </div>
              <FileText className="h-8 w-8 text-purple-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Papers</p>
                <p className="text-2xl font-bold">{summaryData.stats.paper_count || 0}</p>
              </div>
              <BookOpen className="h-8 w-8 text-orange-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Authors</p>
                <p className="text-2xl font-bold">{summaryData.stats.unique_authors}</p>
              </div>
              <User className="h-8 w-8 text-green-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Total Likes</p>
                <p className="text-2xl font-bold">{summaryData.stats.total_likes.toLocaleString()}</p>
              </div>
              <Heart className="h-8 w-8 text-red-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Retweets</p>
                <p className="text-2xl font-bold">{summaryData.stats.total_retweets.toLocaleString()}</p>
              </div>
              <Repeat2 className="h-8 w-8 text-purple-500 opacity-20" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Summary Content */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              AI Summary
            </CardTitle>
            <div className="flex items-center gap-2">
              {wordCount > 0 && (
                <Badge variant="secondary" className="text-xs">
                  ~{wordCount} words
                </Badge>
              )}
              {summaryData.model_used && (
                <Badge variant="outline" className="font-mono text-xs">
                  {getModelIcon(summaryData.model_used)} {summaryData.model_used}
                </Badge>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={onRegenerate}
                disabled={loading}
                className="h-8 w-8 p-0"
                title="Regenerate summary"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={downloadMarkdown}
                className="h-8 w-8 p-0"
                title="Download as Markdown"
              >
                <Download className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={copyToClipboard}
                className="h-8 w-8 p-0"
                title="Copy to clipboard"
              >
                {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Truncation Warning */}
          {summaryData.data_truncated && summaryData.truncation_warning && (
            <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800 rounded-lg flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-amber-800 dark:text-amber-200">
                <p className="font-medium">Data Limit Reached</p>
                <p className="text-amber-700 dark:text-amber-300">{summaryData.truncation_warning}</p>
              </div>
            </div>
          )}
          <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:text-gray-900 dark:prose-headings:text-gray-100 prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg prose-strong:text-gray-900 dark:prose-strong:text-gray-100 prose-ul:list-disc prose-ol:list-decimal prose-li:text-gray-700 dark:prose-li:text-gray-300 prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-4 prose-blockquote:italic prose-code:bg-gray-100 dark:prose-code:bg-gray-800 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100">
            <ReactMarkdown
              components={{
                h1: ({children}) => <h1 className="text-2xl font-bold mt-4 mb-3 text-gray-900 dark:text-gray-100">{children}</h1>,
                h2: ({children}) => <h2 className="text-xl font-semibold mt-3 mb-2 text-gray-800 dark:text-gray-200">{children}</h2>,
                h3: ({children}) => <h3 className="text-lg font-semibold mt-2 mb-2 text-gray-800 dark:text-gray-200">{children}</h3>,
                p: ({children}) => <p className="mb-3 text-gray-700 dark:text-gray-300 leading-relaxed">{children}</p>,
                ul: ({children}) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
                ol: ({children}) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
                li: ({children}) => <li className="text-gray-700 dark:text-gray-300">{children}</li>,
                strong: ({children}) => <strong className="font-semibold text-gray-900 dark:text-gray-100">{children}</strong>,
                em: ({children}) => <em className="italic text-gray-700 dark:text-gray-300">{children}</em>,
                blockquote: ({children}) => (
                  <blockquote className="border-l-4 border-blue-500 pl-3 py-1 my-3 italic bg-blue-50 dark:bg-blue-950/50 rounded-r">
                    {children}
                  </blockquote>
                ),
                code: ({className, children}) => {
                  const isInline = !className?.includes('language-');
                  if (isInline) {
                    return <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-sm font-mono text-gray-800 dark:text-gray-200">{children}</code>;
                  }
                  return (
                    <pre className="bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto mb-3">
                      <code className="text-sm font-mono">{children}</code>
                    </pre>
                  );
                },
                hr: () => <hr className="my-4 border-gray-300 dark:border-gray-700" />,
                a: ({href, children}) => (
                  <a href={href} className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline" target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                ),
              }}
            >
              {summaryData.summary}
            </ReactMarkdown>
          </div>

          <Separator className="my-4" />

          {/* Metadata */}
          <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              <span className="font-medium">Time Range:</span>
              <span>
                {formatDate(summaryData.stats.time_range.start)} to {formatDate(summaryData.stats.time_range.end)}
              </span>
            </div>

            {summaryData.filters.tags && summaryData.filters.tags.length > 0 && (
              <div className="flex items-center gap-2">
                <Hash className="h-4 w-4" />
                <span className="font-medium">Filtered Tags:</span>
                <div className="flex flex-wrap gap-1">
                  {summaryData.filters.tags.map(tag => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {summaryData.filters.author && (
              <div className="flex items-center gap-2">
                <User className="h-4 w-4" />
                <span className="font-medium">Author:</span>
                <Badge variant="outline" className="text-xs">
                  @{summaryData.filters.author}
                </Badge>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
