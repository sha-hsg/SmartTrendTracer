import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Twitter,
  FileText,
  Tags,
  Search,
  TrendingUp,
  BarChart3,
  Sparkles,
  Activity,
  ChevronRight,
  BookOpen,
  MessageSquare,
  Library,
  GitCompare,
  Layers,
  ScrollText,
  Brain,
  Flame,
  Users
} from 'lucide-react'
import type { ViewType } from './ModernNavigation'

interface DashboardHomeProps {
  onNavigate: (view: ViewType) => void
}

export default function DashboardHome({ onNavigate }: DashboardHomeProps) {
  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-white">
        <h1 className="text-4xl font-bold mb-2">Welcome to SmartTrendTracer</h1>
        <p className="text-xl opacity-90">
          AI-powered content monitoring and trend analysis system
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => onNavigate('statistics')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Overview</CardTitle>
            <BarChart3 className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Statistics</div>
            <p className="text-xs text-muted-foreground">View system metrics</p>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => onNavigate('rag-search')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AI Search</CardTitle>
            <Search className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">RAG Search</div>
            <p className="text-xs text-muted-foreground">Search all content</p>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => onNavigate('twitter-faceted')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Twitter/X</CardTitle>
            <Twitter className="h-4 w-4 text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Tweets</div>
            <p className="text-xs text-muted-foreground">Browse tweets</p>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => onNavigate('articles-faceted')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Articles</CardTitle>
            <FileText className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Articles</div>
            <p className="text-xs text-muted-foreground">Browse web articles</p>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => onNavigate('reddit-faceted')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reddit Posts</CardTitle>
            <MessageSquare className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Reddit</div>
            <p className="text-xs text-muted-foreground">AI/ML discussions</p>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => onNavigate('papers-dashboard')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Research Papers</CardTitle>
            <BookOpen className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Papers</div>
            <p className="text-xs text-muted-foreground">Analyze PDFs</p>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => onNavigate('books-dashboard')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Book Library</CardTitle>
            <Library className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Books</div>
            <p className="text-xs text-muted-foreground">Browse long-form content</p>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-950 dark:to-blue-950"
          onClick={() => onNavigate('twitter-summary')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AI Summary</CardTitle>
            <ScrollText className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Summarize</div>
            <p className="text-xs text-muted-foreground">AI-powered insights</p>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-950 dark:to-red-950 border-orange-200 dark:border-orange-800"
          onClick={() => onNavigate('trend-dashboard')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Trend Detection</CardTitle>
            <Flame className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Trends</div>
            <p className="text-xs text-muted-foreground">Real-time trend analysis</p>
          </CardContent>
        </Card>
      </div>

      {/* Analysis & Insights Section */}
      <Card className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-950 dark:to-purple-950 border-indigo-200 dark:border-indigo-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-indigo-600" />
            Analysis & Insights
          </CardTitle>
          <CardDescription>
            Cross-source analysis, trend comparison, and topic clustering
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <Button
              variant="outline"
              className="h-auto py-4 flex-col items-start gap-2 bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900 dark:to-red-900 border-orange-300 dark:border-orange-700 hover:from-orange-100 hover:to-red-100"
              onClick={() => onNavigate('trend-dashboard')}
            >
              <div className="flex items-center gap-2 w-full">
                <Flame className="h-5 w-5 text-orange-500" />
                <span className="font-semibold">Trend Dashboard</span>
              </div>
              <span className="text-xs text-muted-foreground text-left">
                Real-time trend detection with 7 visualizations
              </span>
            </Button>

            <Button
              variant="outline"
              className="h-auto py-4 flex-col items-start gap-2 bg-white dark:bg-gray-900"
              onClick={() => onNavigate('twitter-summary')}
            >
              <div className="flex items-center gap-2 w-full">
                <ScrollText className="h-5 w-5 text-purple-500" />
                <span className="font-semibold">AI Summarization</span>
              </div>
              <span className="text-xs text-muted-foreground text-left">
                Generate intelligent summaries from tweets, articles, and papers
              </span>
            </Button>

            <Button
              variant="outline"
              className="h-auto py-4 flex-col items-start gap-2 bg-white dark:bg-gray-900"
              onClick={() => onNavigate('analysis-unified')}
            >
              <div className="flex items-center gap-2 w-full">
                <TrendingUp className="h-5 w-5 text-blue-500" />
                <span className="font-semibold">Unified Trends</span>
              </div>
              <span className="text-xs text-muted-foreground text-left">
                Combined insights across all content sources
              </span>
            </Button>

            <Button
              variant="outline"
              className="h-auto py-4 flex-col items-start gap-2 bg-white dark:bg-gray-900"
              onClick={() => onNavigate('analysis-compare')}
            >
              <div className="flex items-center gap-2 w-full">
                <GitCompare className="h-5 w-5 text-green-500" />
                <span className="font-semibold">Compare Sources</span>
              </div>
              <span className="text-xs text-muted-foreground text-left">
                Twitter vs Articles vs Papers comparison
              </span>
            </Button>

            <Button
              variant="outline"
              className="h-auto py-4 flex-col items-start gap-2 bg-white dark:bg-gray-900"
              onClick={() => onNavigate('analysis-clustering')}
            >
              <div className="flex items-center gap-2 w-full">
                <Layers className="h-5 w-5 text-orange-500" />
                <span className="font-semibold">Topic Clustering</span>
              </div>
              <span className="text-xs text-muted-foreground text-left">
                Discover related topics and content groups
              </span>
            </Button>

            <Button
              variant="outline"
              className="h-auto py-4 flex-col items-start gap-2 bg-white dark:bg-gray-900"
              onClick={() => onNavigate('topic-explorer')}
            >
              <div className="flex items-center gap-2 w-full">
                <Sparkles className="h-5 w-5 text-indigo-500" />
                <span className="font-semibold">Topic Explorer</span>
              </div>
              <span className="text-xs text-muted-foreground text-left">
                Analyze topic frequency and correlations
              </span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Twitter className="h-5 w-5" />
              Twitter/X Analytics
            </CardTitle>
            <CardDescription>
              Real-time monitoring of AI-related tweets from key accounts
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('twitter-faceted')}
              >
                Browse Tweets
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('twitter-trends')}
              >
                Trending Topics
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('twitter-deck')}
              >
                TweetDeck
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('twitter-media')}
              >
                Media Gallery
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Article Analysis
            </CardTitle>
            <CardDescription>
              Analyze web articles from various sources
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('articles-faceted')}
              >
                Browse Articles
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('articles-trends')}
              >
                Article Trends
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('articles-charts')}
              >
                Article Analytics
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('articles-clustering')}
              >
                Article Clustering
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Reddit Analytics
            </CardTitle>
            <CardDescription>
              AI/ML discussions from key subreddits
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('reddit-faceted')}
              >
                Browse Posts
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('reddit-trends')}
              >
                Reddit Trends
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Authors
            </CardTitle>
            <CardDescription>
              View and organize article authors
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('author-management')}
              >
                Manage Authors
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('author-analytics')}
              >
                Author Analytics
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('author-merge')}
              >
                Merge Duplicates
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              Research Papers
            </CardTitle>
            <CardDescription>
              Upload and analyze PDF research papers with AI
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('papers-dashboard')}
              >
                Manage Papers
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('reviews-dashboard')}
              >
                Paper Reviews
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('papers-references')}
              >
                References
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Library className="h-5 w-5" />
              Book Library
            </CardTitle>
            <CardDescription>
              Browse and analyze long-form content
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('books-dashboard')}
              >
                Browse Books
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('books-analysis')}
              >
                Book Analytics
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Tags className="h-5 w-5" />
              Concepts & Search
            </CardTitle>
            <CardDescription>
              AI search and concept organization
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('rag-search')}
              >
                AI Search
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('concept-management')}
              >
                Concept Management
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => onNavigate('concept-graph')}
              >
                Concept Graph
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Recent Activity
          </CardTitle>
          <CardDescription>Latest updates across the system</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="outline">Tweets</Badge>
                <span className="text-sm">New tweets collected from @OpenAI</span>
              </div>
              <span className="text-sm text-muted-foreground">2 hours ago</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="outline">Articles</Badge>
                <span className="text-sm">New article from Ethan Mollick</span>
              </div>
              <span className="text-sm text-muted-foreground">5 hours ago</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="outline">Papers</Badge>
                <span className="text-sm">Research papers system ready for upload</span>
              </div>
              <span className="text-sm text-muted-foreground">Just now</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="outline">Tags</Badge>
                <span className="text-sm">15 new tags added to ontology</span>
              </div>
              <span className="text-sm text-muted-foreground">1 day ago</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
