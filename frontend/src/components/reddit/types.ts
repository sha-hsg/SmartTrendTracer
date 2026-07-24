import { Concept } from '@/types/concept'

export interface RedditPost {
  _id: string
  reddit_id: string
  title: string
  selftext: string
  author: string
  subreddit: string
  subreddit_config: {
    name: string
    display_name: string
    category: string
    description: string
  }
  score: number
  upvote_ratio: number
  num_comments: number
  created_utc: string
  permalink: string
  url: string
  urls: string[]
  is_self: boolean
  is_video: boolean
  over_18: boolean
  spoiler: boolean
  stickied: boolean
  gilded: number
  comments: Array<{
    id: string
    author: string
    body: string
    score: number
  }>
  tags: string[]
  concepts: Concept[]
  processed: boolean
}

export interface SubredditFacet {
  name: string
  count: number
}

export interface AuthorFacet {
  name: string
  count: number
}

export interface TimeFacet {
  '24h': number
  '7d': number
  '30d': number
}

export interface ScoreFacet {
  high_score: number
  medium_score: number
  low_score: number
}

export interface PostTypeFacet {
  text_posts: number
  link_posts: number
  video_posts: number
}

export interface RedditFacets {
  subreddits: SubredditFacet[]
  authors: AuthorFacet[]
  time_ranges: TimeFacet
  score_ranges: ScoreFacet
  post_types: PostTypeFacet
  total_posts: number
}

export interface PaginationInfo {
  page: number
  page_size: number
  total_posts: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}
