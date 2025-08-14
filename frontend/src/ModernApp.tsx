import React, { useState } from 'react'
import ModernNavigation, { ViewType } from './components/ModernNavigation'
import StatisticsDashboard from './components/StatisticsDashboard'
import FacetedTweetsDashboardModern from './components/FacetedTweetsDashboardModern'
import FacetedSubstackDashboardModern from './components/FacetedSubstackDashboardModern'
import TrendAnalysisModern from './components/TrendAnalysisModern'
import UserTrendAnalysisModern from './components/UserTrendAnalysisModern'
import TrendVisualizationModern from './components/TrendVisualizationModern'
import SummarizationModern from './components/SummarizationModern'
import TagOntologyModern from './components/TagOntologyModern'
import SubstackTrendsModern from './components/SubstackTrendsModern'
import UnifiedTrendsModern from './components/UnifiedTrendsModern'
import TwitterMediaGalleryModern from './components/TwitterMediaGalleryModern'
import RAGSearchModern from './components/RAGSearchModern'
import PapersDashboardModern from './components/PapersDashboardModern'
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
  Database,
  Sparkles,
  Activity,
  ChevronRight,
  BookOpen
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
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
            <CardTitle className="text-sm font-medium">Newsletters</CardTitle>
            <FileText className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Articles</div>
            <p className="text-xs text-muted-foreground">Read articles</p>
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
      </div>

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
              Newsletter Analysis
            </CardTitle>
            <CardDescription>
              Analyze Substack articles from leading AI researchers
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
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              AI-Powered Features
            </CardTitle>
            <CardDescription>
              Advanced analysis and intelligent content organization
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
                onClick={() => setActiveView('tags-organisation')}
              >
                Tag Management
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-between"
                onClick={() => setActiveView('analysis-unified')}
              >
                Unified Trends
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
        return <TrendAnalysisModern />
      case 'twitter-users':
        return <UserTrendAnalysisModern />
      case 'twitter-charts':
        return <TrendVisualizationModern />
      case 'twitter-summary':
        return <SummarizationModern />
      // Article views
      case 'articles-faceted':
        return <FacetedSubstackDashboardModern />
      case 'articles-trends':
        return <SubstackTrendsModern />
      case 'articles-charts':
        return <TrendVisualizationModern contentType="articles" />
      // Papers views
      case 'papers-dashboard':
        return <PapersDashboardModern />
      // Analysis views
      case 'analysis-unified':
        return <UnifiedTrendsModern />
      case 'analysis-compare':
        return <TrendVisualizationModern />
      case 'analysis-clustering':
        return <TrendAnalysisModern />
      // Tag management
      case 'tags-organisation':
        return <TagOntologyModern />
      default:
        return renderDashboard()
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <ModernNavigation activeView={activeView} onViewChange={setActiveView} />
      <main className="pb-8">
        {renderContent()}
      </main>
    </div>
  )
}