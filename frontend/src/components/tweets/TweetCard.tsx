import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Loader2,
  ChevronLeft,
  ChevronRight,
  Twitter,
  Calendar,
} from 'lucide-react'
import TweetCardModern from './TweetCardModern'
import { Concept } from '@/types/concept'

interface Tweet {
  id: string
  text: string
  author_id: string
  author_username: string
  author_name?: string
  tags?: any
  concepts?: Concept[]
  created_at: string
  is_retweet?: boolean
  like_count?: number
  retweet_count?: number
  reply_count?: number
  metrics?: {
    like_count?: number
    retweet_count?: number
    reply_count?: number
    quote_count?: number
    likes: number
    retweets: number
    replies: number
    quotes?: number
  }
  media?: Array<{
    type: string
    url: string
    thumbnail_url?: string
  }>
}

interface TweetCardProps {
  tweets: Tweet[]
  loading: boolean
  totalTweets: number
  currentPage: number
  totalPages: number
  selectedAuthors: string[]
  selectedConcepts: string[]
  selectedYears: number[]
  onPageChange: (page: number) => void
  onConceptAdded: (tweetId: string, concept: Concept) => void
  onConceptRemoved: (tweetId: string, conceptId: string) => void
  onSuggestConcepts: (tweet: Tweet) => void
}

export type { Tweet }

export default function TweetCard({
  tweets,
  loading,
  totalTweets,
  currentPage,
  totalPages,
  selectedAuthors,
  selectedConcepts,
  selectedYears,
  onPageChange,
  onConceptAdded,
  onConceptRemoved,
  onSuggestConcepts,
}: TweetCardProps) {
  return (
    <div className="lg:col-span-7 order-2 lg:order-2">
      {/* Stats Bar */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Badge variant="outline" className="py-1.5 px-3">
            <Twitter className="h-3 w-3 mr-1" />
            {totalTweets} tweets
          </Badge>
          {selectedAuthors.length > 0 && (
            <Badge variant="secondary" className="py-1.5 px-3">
              {selectedAuthors.length} author{selectedAuthors.length !== 1 ? 's' : ''} selected
            </Badge>
          )}
          {selectedConcepts.length > 0 && (
            <Badge variant="secondary" className="py-1.5 px-3">
              {selectedConcepts.length} concept{selectedConcepts.length !== 1 ? 's' : ''} selected
            </Badge>
          )}
          {selectedYears.length > 0 && (
            <Badge variant="secondary" className="py-1.5 px-3">
              <Calendar className="h-3 w-3 mr-1" />
              {selectedYears.length > 1 ? `${selectedYears.length} years` : selectedYears[0]} selected
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Page {currentPage} of {totalPages}
          </span>
        </div>
      </div>

      {/* Tweets List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 dark:text-gray-500" />
        </div>
      ) : tweets.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Twitter className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">No tweets found matching your filters</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {tweets.map(tweet => (
            <TweetCardModern
              key={tweet.id}
              tweet={tweet}
              onConceptAdded={onConceptAdded}
              onConceptRemoved={onConceptRemoved}
              onSuggestConcepts={onSuggestConcepts}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-2">
          <Button
            onClick={() => onPageChange(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1 || loading}
            variant="outline"
            size="sm"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>

          <div className="flex gap-1">
            {[...Array(Math.min(5, totalPages))].map((_, i) => {
              let pageNum: number
              if (totalPages <= 5) {
                pageNum = i + 1
              } else if (currentPage <= 3) {
                pageNum = i + 1
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i
              } else {
                pageNum = currentPage - 2 + i
              }

              return (
                <Button
                  key={pageNum}
                  onClick={() => onPageChange(pageNum)}
                  variant={currentPage === pageNum ? "default" : "outline"}
                  size="sm"
                  className="w-10"
                >
                  {pageNum}
                </Button>
              )
            })}
          </div>

          <Button
            onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages || loading}
            variant="outline"
            size="sm"
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}
