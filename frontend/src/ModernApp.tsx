import { useState } from 'react'
import ModernNavigation, { ViewType } from './components/ModernNavigation'
import ApiKeyStatusBanner from './components/ApiKeyStatusBanner'
import StatisticsDashboard from './components/StatisticsDashboard'
import FacetedTweetsDashboardModern from './components/FacetedTweetsDashboardModern'
import FacetedArticlesDashboardModern from './components/FacetedArticlesDashboardModern'
import FacetedRedditDashboardModern from './components/FacetedRedditDashboardModern'
import TrendAnalysisModern from './components/TrendAnalysisModern'
import TrendAnalysisOverview from './components/TrendAnalysisOverview'
import UserTrendAnalysisModern from './components/UserTrendAnalysisModern'
import TrendVisualizationModern from './components/TrendVisualizationModern'
import SummarizationModern from './components/SummarizationModern'
import TagOntologyModern from './components/TagOntologyModern'
import ConceptOrganizer from './components/ConceptOrganizer'
import ConceptManagementCenter from './components/ConceptManagementCenter'
import ConceptGraph from './components/ConceptGraph'
import SubstackTrendsModern from './components/SubstackTrendsModern'
import UnifiedTrendsModern from './components/UnifiedTrendsModern'
import TwitterMediaGalleryModern from './components/TwitterMediaGalleryModern'
import RAGSearchModern from './components/RAGSearchModern'
import FacetedPapersDashboard from './components/FacetedPapersDashboard'
import FacetedBooksDashboard from './components/FacetedBooksDashboard'
import ReferenceManager from './components/ReferenceManager'
import ArticleClusteringDashboard from './components/ArticleClusteringDashboard'
import AuthorManagementModern from './components/AuthorManagementModern'
import TwitterAccountManager from './components/TwitterAccountManager'
import TopicExplorerModern from './components/TopicExplorerModern'
import ErrorBoundary from './components/ErrorBoundary'
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
  Brain
} from 'lucide-react'
import './index.css'

export default function ModernApp() {
  const [activeView, setActiveView] = useState<ViewType>('dashboard')

  const renderDashboard = () => (
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
          onClick={() => setActiveView('statistics')}
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
          onClick={() => setActiveView('rag-search')}
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
          onClick={() => setActiveView('twitter-faceted')}
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
          onClick={() => setActiveView('articles-faceted')}
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
          onClick={() => setActiveView('reddit-faceted')}
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
          onClick={() => setActiveView('papers-dashboard')}
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
          onClick={() => setActiveView('books-dashboard')}
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
          onClick={() => setActiveView('twitter-summary')}
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
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <Button
              variant="outline"
              className="h-auto py-4 flex-col items-start gap-2 bg-white dark:bg-gray-900"
              onClick={() => setActiveView('twitter-summary')}
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
              onClick={() => setActiveView('analysis-unified')}
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
              onClick={() => setActiveView('analysis-compare')}
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
              onClick={() => setActiveView('analysis-clustering')}
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
              onClick={() => setActiveView('topic-explorer')}
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
                onClick={() => setActiveView('twitter-faceted')}
              >
                Browse Tweets
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-between"
                onClick={() => setActiveView('twitter-trends')}
              >
                Trending Topics
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-between"
                onClick={() => setActiveView('twitter-media')}
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
                onClick={() => setActiveView('articles-faceted')}
              >
                Browse Articles
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-between"
                onClick={() => setActiveView('articles-trends')}
              >
                Article Trends
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-between"
                onClick={() => setActiveView('articles-charts')}
              >
                Article Analytics
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
                onClick={() => setActiveView('reddit-faceted')}
              >
                Browse Posts
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-between"
                onClick={() => setActiveView('reddit-trends')}
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
                onClick={() => setActiveView('papers-dashboard')}
              >
                Manage Papers
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-between"
                onClick={() => setActiveView('papers-references')}
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
                onClick={() => setActiveView('rag-search')}
              >
                AI Search
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => setActiveView('concept-management')}
              >
                Concept Management
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                className="w-full justify-between"
                onClick={() => setActiveView('concept-graph')}
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

  const renderContent = () => {
    switch (activeView) {
      case 'dashboard':
        return renderDashboard()
      case 'statistics':
        return <StatisticsDashboard />
      case 'rag-search':
        return <RAGSearchModern />
      // Twitter views
      case 'twitter-faceted':
        return <FacetedTweetsDashboardModern />
      case 'twitter-media':
        return <TwitterMediaGalleryModern />
      case 'twitter-trends':
        return <TrendAnalysisOverview />
      case 'twitter-users':
        return <UserTrendAnalysisModern />
      case 'twitter-charts':
        return <TrendVisualizationModern />
      case 'twitter-summary':
        return <SummarizationModern />
      case 'twitter-accounts':
        return <TwitterAccountManager />
      // Article views
      case 'articles-faceted':
        return <FacetedArticlesDashboardModern />
      case 'articles-trends':
        return (
          <ErrorBoundary 
            fallbackTitle="Article Trends Error"
            fallbackMessage="There was an error loading the Article Trends. This may be due to missing or incomplete data. Please try refreshing the page or check back later."
          >
            <SubstackTrendsModern />
          </ErrorBoundary>
        )
      case 'articles-charts':
        return <TrendVisualizationModern contentType="articles" />
      case 'articles-clustering':
        return <ArticleClusteringDashboard />
      // Author views
      case 'author-management':
        return <AuthorManagementModern />
      case 'author-analytics':
        return <div className="p-6"><h2 className="text-2xl font-bold">Author Analytics - Coming Soon</h2></div>
      case 'author-merge':
        return <div className="p-6"><h2 className="text-2xl font-bold">Author Merge - Coming Soon</h2></div>
      // Reddit views
      case 'reddit-faceted':
        return <FacetedRedditDashboardModern />
      case 'reddit-trends':
        return (
          <ErrorBoundary 
            fallbackTitle="Reddit Trends Error"
            fallbackMessage="Reddit trends analysis is not yet implemented. This feature will show trending topics across monitored subreddits."
          >
            <div className="container mx-auto p-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-4">Reddit Trends</h2>
                <p className="text-muted-foreground">Coming soon - Reddit trend analysis</p>
              </div>
            </div>
          </ErrorBoundary>
        )
      // Papers views
      case 'papers-dashboard':
        return <FacetedPapersDashboard />
      case 'papers-references':
        return <ReferenceManager />
      // Books views
      case 'books-dashboard':
        return <FacetedBooksDashboard />
      case 'books-analysis':
        // TODO: Implement book analytics dashboard
        return (
          <div className="p-8 text-center">
            <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Book Analytics</h2>
            <p className="text-gray-600">Coming soon - Reading statistics and insights</p>
          </div>
        )
      // Analysis views
      case 'analysis-unified':
        return <UnifiedTrendsModern />
      case 'analysis-compare':
        return <TrendVisualizationModern />
      case 'analysis-clustering':
        return <TrendAnalysisModern />
      case 'topic-explorer':
        return <TopicExplorerModern />
      // Tag management
      // New unified concept management
      case 'concept-management':
        return <ConceptManagementCenter />
      case 'concept-graph':
        return <ConceptGraph />
      // Legacy (to be removed)
      case 'tags-organisation':
        return <TagOntologyModern />
      case 'concept-organizer':
        return <ConceptOrganizer />
      default:
        return renderDashboard()
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <ApiKeyStatusBanner />
      <ModernNavigation activeView={activeView} onViewChange={setActiveView} />
      <main className="pb-8">
        {renderContent()}
      </main>
    </div>
  )
}
