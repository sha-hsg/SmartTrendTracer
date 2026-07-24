import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { TagBadge } from "@/components/ui/tag-badge"
import {
  User,
  Tag,
  MessageSquare,
  ArrowUp,
  Clock,
  Link as LinkIcon,
  Star
} from 'lucide-react'
import { RedditPost } from './types'

interface RedditPostCardProps {
  post: RedditPost
  onOpenTagModal: (post: RedditPost) => void
  formatDate: (dateString: string) => string
}

const RedditPostCard: React.FC<RedditPostCardProps> = ({ post, onOpenTagModal, formatDate }) => {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Post Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Badge variant="outline">r/{post.subreddit}</Badge>
              <span>•</span>
              <User className="w-3 h-3" />
              <span>{post.author}</span>
              <span>•</span>
              <Clock className="w-3 h-3" />
              <span>{formatDate(post.created_utc)}</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="text-xs">
                <ArrowUp className="w-3 h-3 mr-1" />
                {post.score}
              </Badge>
              <Badge variant="secondary" className="text-xs">
                <MessageSquare className="w-3 h-3 mr-1" />
                {post.num_comments}
              </Badge>
            </div>
          </div>

          {/* Post Title */}
          <div className="space-y-2">
            <h3 className="text-lg font-semibold leading-tight">
              <a
                href={`https://reddit.com${post.permalink}`}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-primary transition-colors"
              >
                {post.title}
              </a>
            </h3>

            {/* Post Content Preview */}
            {post.selftext && (
              <p className="text-muted-foreground line-clamp-3">
                {post.selftext.substring(0, 300)}
                {post.selftext.length > 300 && '...'}
              </p>
            )}

            {/* External URL */}
            {!post.is_self && post.url && (
              <div className="flex items-center gap-2 p-2 bg-muted rounded text-sm">
                <LinkIcon className="w-3 h-3" />
                <a
                  href={post.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline truncate"
                >
                  {post.url}
                </a>
              </div>
            )}

            {/* Post Type Indicators */}
            <div className="flex items-center gap-2">
              {post.is_self && <Badge variant="outline" className="text-xs">Text Post</Badge>}
              {post.is_video && <Badge variant="outline" className="text-xs">Video</Badge>}
              {post.stickied && <Badge variant="outline" className="text-xs">Pinned</Badge>}
              {post.gilded > 0 && (
                <Badge variant="outline" className="text-xs">
                  <Star className="w-3 h-3 mr-1" />
                  {post.gilded} Award{post.gilded > 1 ? 's' : ''}
                </Badge>
              )}
            </div>
          </div>

          {/* Tags and Actions */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-wrap">
              {post.concepts?.map(concept => (
                <TagBadge key={concept.id} size="sm">{concept.display_name}</TagBadge>
              ))}
              <Button
                onClick={() => onOpenTagModal(post)}
                variant="ghost"
                size="sm"
                className="text-xs"
              >
                <Tag className="w-3 h-3 mr-1" />
                Add Tag
              </Button>
            </div>

            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" asChild>
                <a
                  href={`https://reddit.com${post.permalink}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View on Reddit
                </a>
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default RedditPostCard
