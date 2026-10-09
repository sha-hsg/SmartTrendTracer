import { useState } from 'react'
import ModernNavigation, { ViewType } from './components/layout/ModernNavigation'
import ApiKeyStatusBanner from './components/llm/ApiKeyStatusBanner'
import DeprecatedPreferencesBanner from './components/llm/DeprecatedPreferencesBanner'
import DashboardHome from './components/layout/DashboardHome'
import { StatisticsDashboard } from './components/statistics'
import FacetedTweetsDashboardModern from './components/tweets/FacetedTweetsDashboardModern'
import FacetedArticlesDashboardModern from './components/articles'
import UserTrendAnalysisModern from './components/trends/UserTrendAnalysisModern'
import SummarizationModern from './components/summarization'
import ConceptManagementCenter from './components/concept-management'
import ConceptGraph from './components/concept-management/ConceptGraph'
import SubstackTrendsModern from './components/substack-trends/SubstackTrendsModern'
import TwitterMediaGalleryModern from './components/twitter-media'
import RAGSearchModern from './components/rag-search'
import FacetedPapersDashboard from './components/papers-dashboard/FacetedPapersDashboard'
import FacetedBooksDashboard from './components/books/FacetedBooksDashboard'
import ReferenceManager from './components/reference-manager'
import PaperFeed from './components/paper-feed'
import WeeklyDigest from './components/weekly-digest'
import PaperQA from './components/paper-qa'
import AuthorManagementModern from './components/authors/AuthorManagementModern'
import TwitterAccountManager from './components/twitter'
import TweetDeckView from './components/tweets/TweetDeckView'
import TopicExplorerModern from './components/topic-explorer'
import { TrendDashboardMain } from './components/trends'
import ErrorBoundary from './components/layout/ErrorBoundary'
import { Toaster } from 'sonner'
import './index.css'

export default function ModernApp() {
  const [activeView, setActiveView] = useState<ViewType>('dashboard')
  // concept handed from the Trend Dashboard to the Topic Explorer
  const [explorerConcept, setExplorerConcept] = useState<string | undefined>()

  const renderContent = () => {
    switch (activeView) {
      case 'dashboard':
        return <DashboardHome onNavigate={setActiveView} />
      case 'statistics':
        return <StatisticsDashboard />
      case 'rag-search':
        return <RAGSearchModern />
      case 'weekly-digest':
        return <WeeklyDigest />
      case 'paper-qa':
        return <PaperQA />
      // Twitter views
      case 'twitter-faceted':
        return <FacetedTweetsDashboardModern />
      case 'twitter-deck':
        return <TweetDeckView />
      case 'twitter-media':
        return <TwitterMediaGalleryModern />
      case 'twitter-users':
        return <UserTrendAnalysisModern />
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
      // Author views
      case 'author-management':
        return <AuthorManagementModern />
      // Papers views
      case 'papers-dashboard':
        return <FacetedPapersDashboard />
      case 'papers-references':
        return <ReferenceManager />
      case 'papers-feed':
        return <PaperFeed />
      case 'reviews-dashboard':
        return <FacetedPapersDashboard paperType="review" />
      // Books views
      case 'books-dashboard':
        return <FacetedBooksDashboard />
      // Analysis views
      case 'trend-dashboard':
        return <TrendDashboardMain onConceptClick={(conceptId) => { setExplorerConcept(conceptId); setActiveView('topic-explorer') }} />
      case 'topic-explorer':
        return <TopicExplorerModern initialConceptId={explorerConcept} />
      // New unified concept management
      case 'concept-management':
        return <ConceptManagementCenter />
      case 'concept-graph':
        return <ConceptGraph />
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
