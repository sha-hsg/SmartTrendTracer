import { useState } from 'react'
import ModernNavigation, { ViewType } from './components/ModernNavigation'
import ApiKeyStatusBanner from './components/ApiKeyStatusBanner'
import DeprecatedPreferencesBanner from './components/DeprecatedPreferencesBanner'
import DashboardHome from './components/DashboardHome'
import { StatisticsDashboard } from './components/statistics'
import FacetedTweetsDashboardModern from './components/tweets/FacetedTweetsDashboardModern'
import FacetedArticlesDashboardModern from './components/articles'
import { FacetedRedditDashboardModern } from './components/reddit'
import TrendAnalysisModern from './components/trend-analysis'
import TrendAnalysisOverview from './components/trend-overview'
import UserTrendAnalysisModern from './components/UserTrendAnalysisModern'
import TrendVisualizationModern from './components/TrendVisualizationModern'
import SummarizationModern from './components/summarization'
import TagOntologyModern from './components/tag-ontology'
import ConceptOrganizer from './components/ConceptOrganizer'
import ConceptManagementCenter from './components/concept-management'
import ConceptGraph from './components/ConceptGraph'
import SubstackTrendsModern from './components/SubstackTrendsModern'
import TwitterMediaGalleryModern from './components/twitter-media'
import RAGSearchModern from './components/rag-search'
import FacetedPapersDashboard from './components/FacetedPapersDashboard'
import FacetedBooksDashboard from './components/books/FacetedBooksDashboard'
import ReferenceManager from './components/reference-manager'
import { ArticleClusteringDashboard } from './components/clustering'
import AuthorManagementModern from './components/AuthorManagementModern'
import TwitterAccountManager from './components/twitter'
import TweetDeckView from './components/tweets/TweetDeckView'
import TopicExplorerModern from './components/topic-explorer'
import { TrendDashboardMain } from './components/trends'
import ErrorBoundary from './components/ErrorBoundary'
import { BookOpen } from 'lucide-react'
import { Toaster } from 'sonner'
import './index.css'

export default function ModernApp() {
  const [activeView, setActiveView] = useState<ViewType>('dashboard')

  const renderContent = () => {
    switch (activeView) {
      case 'dashboard':
        return <DashboardHome onNavigate={setActiveView} />
      case 'statistics':
        return <StatisticsDashboard />
      case 'rag-search':
        return <RAGSearchModern />
      // Twitter views
      case 'twitter-faceted':
        return <FacetedTweetsDashboardModern />
      case 'twitter-deck':
        return <TweetDeckView />
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
      case 'reviews-dashboard':
        return <FacetedPapersDashboard paperType="review" />
      // Books views
      case 'books-dashboard':
        return <FacetedBooksDashboard />
      case 'books-analysis':
        // TODO: Implement book analytics dashboard
        return (
          <div className="p-8 text-center">
            <BookOpen className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Book Analytics</h2>
            <p className="text-muted-foreground">Coming soon - Reading statistics and insights</p>
          </div>
        )
      // Analysis views
      case 'analysis-unified':
      case 'trend-dashboard':
        return <TrendDashboardMain onConceptClick={() => setActiveView('topic-explorer')} />
      case 'analysis-compare':
        return <TrendVisualizationModern />
      case 'analysis-clustering':
        return <TrendAnalysisModern />
      case 'topic-explorer':
        return <TopicExplorerModern />
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
        return <DashboardHome onNavigate={setActiveView} />
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Toaster richColors position="bottom-right" />
      <ApiKeyStatusBanner />
      <DeprecatedPreferencesBanner />
      <ModernNavigation activeView={activeView} onViewChange={setActiveView} />
      <main className="pb-8">
        {renderContent()}
      </main>
    </div>
  )
}
