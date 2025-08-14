import React, { useState } from 'react'
import FacetedTweetsDashboard from './FacetedTweetsDashboard'
import FacetedSubstackDashboard from './FacetedSubstackDashboard'
import TrendAnalysis from './TrendAnalysis'
import UserTrendAnalysis from './UserTrendAnalysis'
import TrendVisualization from './TrendVisualization'
import Summarization from './Summarization'
import TagOntologyModern from './TagOntologyModern'
import SubstackTrends from './SubstackTrends'
import UnifiedTrends from './UnifiedTrends'
import TwitterMediaGallery from './TwitterMediaGallery'
import RAGSearchModern from './RAGSearchModern'
import PaperTrendsDashboard from './PaperTrendsDashboard'
import PapersDashboardModern from './PapersDashboardModern'
import PaperUploadModern from './PaperUploadModern'
import PaperViewerModern from './PaperViewerModern'
import UnifiedTimelineView from './UnifiedTimelineView'
import ResearchAnalyticsDashboard from './ResearchAnalyticsDashboard'
import PaperAdvancedDashboard from './PaperAdvancedDashboard'
import PaperKnowledgeGraph from './PaperKnowledgeGraph'
import './Dashboard.css'

type TabType = 
  | 'dashboard'
  // Search
  | 'rag-search'
  // Twitter
  | 'twitter-faceted' 
  | 'twitter-media' 
  | 'twitter-trends'
  | 'twitter-users' 
  | 'twitter-charts' 
  | 'twitter-summary'
  // Articles
  | 'articles-faceted' 
  | 'articles-trends'
  | 'articles-charts'
  // Analysis
  | 'analysis-tweets'
  | 'analysis-articles'
  | 'analysis-compare'
  | 'analysis-tag-trends'
  | 'analysis-clustering'
  // Papers
  | 'papers-browse'
  | 'papers-upload'
  | 'papers-viewer'
  | 'papers-trends'
  // Tags
  | 'tags-organisation'
  // Phase 4 - Analytics
  | 'unified-timeline'
  | 'research-analytics'
  // Phase 5 - Advanced
  | 'paper-advanced'
  | 'paper-knowledge-graph'

function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard')

  const renderDashboardOverview = () => (
    <div className="dashboard-overview">
      <h2>SmartTrendTracer Dashboard</h2>
      <div className="overview-cards">
        <div className="overview-card">
          <h3>Twitter/X Analytics</h3>
          <p>Track AI-related tweets from key accounts</p>
          <button onClick={() => setActiveTab('twitter-faceted')} className="overview-link">
            Browse Twitter Content →
          </button>
        </div>
        <div className="overview-card">
          <h3>Newsletter Articles</h3>
          <p>Analyze Substack articles and trends</p>
          <button onClick={() => setActiveTab('articles-faceted')} className="overview-link">
            Browse Articles →
          </button>
        </div>
        <div className="overview-card">
          <h3>Tag Management</h3>
          <p>Organize and manage your content tags</p>
          <button onClick={() => setActiveTab('tags-organisation')} className="overview-link">
            Manage Tags →
          </button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h2 className="dashboard-title">SmartTrendTracer</h2>
        
        <nav className="dashboard-nav">
          {/* Dashboard Button */}
          <button 
            className={`nav-tab standalone ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
            title="Dashboard overview"
          >
            <span className="tab-icon">🏠</span>
            <span className="tab-text">Dashboard</span>
          </button>

          {/* Search Section */}
          <button 
            className={`nav-tab standalone search-tab ${activeTab === 'rag-search' ? 'active' : ''}`}
            onClick={() => setActiveTab('rag-search')}
            title="AI-powered search across tweets and articles"
          >
            <span className="tab-icon">🔍</span>
            <span className="tab-text">Search</span>
          </button>

          {/* Twitter Group */}
          <div className="nav-tab-group">
            <span className="nav-tab-label">Twitter</span>
            <div className="nav-tabs">
              <button 
                className={`nav-tab ${activeTab === 'twitter-faceted' ? 'active' : ''}`}
                onClick={() => setActiveTab('twitter-faceted')}
                title="Browse and filter tweets"
              >
                <span className="tab-icon">📋</span>
                <span className="tab-text">Faceted</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'twitter-media' ? 'active' : ''}`}
                onClick={() => setActiveTab('twitter-media')}
                title="View media attachments"
              >
                <span className="tab-icon">🖼️</span>
                <span className="tab-text">Media</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'twitter-trends' ? 'active' : ''}`}
                onClick={() => setActiveTab('twitter-trends')}
                title="Analyze trending topics"
              >
                <span className="tab-icon">📈</span>
                <span className="tab-text">Trends</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'twitter-users' ? 'active' : ''}`}
                onClick={() => setActiveTab('twitter-users')}
                title="Analyze trends per user"
              >
                <span className="tab-icon">👥</span>
                <span className="tab-text">Users</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'twitter-charts' ? 'active' : ''}`}
                onClick={() => setActiveTab('twitter-charts')}
                title="Data visualizations"
              >
                <span className="tab-icon">📊</span>
                <span className="tab-text">Charts</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'twitter-summary' ? 'active' : ''}`}
                onClick={() => setActiveTab('twitter-summary')}
                title="AI-generated summaries"
              >
                <span className="tab-icon">📝</span>
                <span className="tab-text">Summary</span>
              </button>
            </div>
          </div>

          {/* Articles Group */}
          <div className="nav-tab-group">
            <span className="nav-tab-label">Articles</span>
            <div className="nav-tabs">
              <button 
                className={`nav-tab ${activeTab === 'articles-faceted' ? 'active' : ''}`}
                onClick={() => setActiveTab('articles-faceted')}
                title="Browse and filter articles"
              >
                <span className="tab-icon">📋</span>
                <span className="tab-text">Faceted</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'articles-trends' ? 'active' : ''}`}
                onClick={() => setActiveTab('articles-trends')}
                title="Article trends and hot topics"
              >
                <span className="tab-icon">🔥</span>
                <span className="tab-text">Trends</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'articles-charts' ? 'active' : ''}`}
                onClick={() => setActiveTab('articles-charts')}
                title="Article analytics charts"
              >
                <span className="tab-icon">📊</span>
                <span className="tab-text">Charts</span>
              </button>
            </div>
          </div>

          {/* Papers Group */}
          <div className="nav-tab-group">
            <span className="nav-tab-label">Papers</span>
            <div className="nav-tabs">
              <button 
                className={`nav-tab ${activeTab === 'papers-browse' ? 'active' : ''}`}
                onClick={() => setActiveTab('papers-browse')}
                title="Browse research papers"
              >
                <span className="tab-icon">📚</span>
                <span className="tab-text">Browse</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'papers-upload' ? 'active' : ''}`}
                onClick={() => setActiveTab('papers-upload')}
                title="Upload new papers"
              >
                <span className="tab-icon">📤</span>
                <span className="tab-text">Upload</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'papers-viewer' ? 'active' : ''}`}
                onClick={() => setActiveTab('papers-viewer')}
                title="View paper details"
              >
                <span className="tab-icon">📖</span>
                <span className="tab-text">Viewer</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'papers-trends' ? 'active' : ''}`}
                onClick={() => setActiveTab('papers-trends')}
                title="Research paper trends and analytics"
              >
                <span className="tab-icon">📊</span>
                <span className="tab-text">Trends</span>
              </button>
            </div>
          </div>

          {/* Phase 5 Advanced Features Group */}
          <div className="nav-tab-group">
            <span className="nav-tab-label">Advanced</span>
            <div className="nav-tabs">
              <button 
                className={`nav-tab ${activeTab === 'paper-advanced' ? 'active' : ''}`}
                onClick={() => setActiveTab('paper-advanced')}
                title="AI-powered paper insights and recommendations"
              >
                <span className="tab-icon">🧠</span>
                <span className="tab-text">AI Insights</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'paper-knowledge-graph' ? 'active' : ''}`}
                onClick={() => setActiveTab('paper-knowledge-graph')}
                title="Interactive knowledge graph visualization"
              >
                <span className="tab-icon">🕸️</span>
                <span className="tab-text">Graph</span>
              </button>
            </div>
          </div>

          {/* Phase 4 Analytics Group */}
          <div className="nav-tab-group">
            <span className="nav-tab-label">Analytics</span>
            <div className="nav-tabs">
              <button 
                className={`nav-tab ${activeTab === 'unified-timeline' ? 'active' : ''}`}
                onClick={() => setActiveTab('unified-timeline')}
                title="Unified timeline of papers, tweets, and articles"
              >
                <span className="tab-icon">⏱️</span>
                <span className="tab-text">Timeline</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'research-analytics' ? 'active' : ''}`}
                onClick={() => setActiveTab('research-analytics')}
                title="Comprehensive research analytics dashboard"
              >
                <span className="tab-icon">📈</span>
                <span className="tab-text">Analytics</span>
              </button>
            </div>
          </div>

          {/* Analysis Group */}
          <div className="nav-tab-group">
            <span className="nav-tab-label">Analysis</span>
            <div className="nav-tabs">
              <button 
                className={`nav-tab ${activeTab === 'analysis-tweets' ? 'active' : ''}`}
                onClick={() => setActiveTab('analysis-tweets')}
                title="Tweet analysis and insights"
              >
                <span className="tab-icon">🐦</span>
                <span className="tab-text">Tweets</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'analysis-articles' ? 'active' : ''}`}
                onClick={() => setActiveTab('analysis-articles')}
                title="Article analysis and insights"
              >
                <span className="tab-icon">📰</span>
                <span className="tab-text">Articles</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'analysis-compare' ? 'active' : ''}`}
                onClick={() => setActiveTab('analysis-compare')}
                title="Compare tweets and articles"
              >
                <span className="tab-icon">⚖️</span>
                <span className="tab-text">Compare</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'analysis-tag-trends' ? 'active' : ''}`}
                onClick={() => setActiveTab('analysis-tag-trends')}
                title="Tag trends over time"
              >
                <span className="tab-icon">🏷️</span>
                <span className="tab-text">Tag Trends</span>
              </button>
              <button 
                className={`nav-tab ${activeTab === 'analysis-clustering' ? 'active' : ''}`}
                onClick={() => setActiveTab('analysis-clustering')}
                title="Content clustering and patterns"
              >
                <span className="tab-icon">🔬</span>
                <span className="tab-text">Clustering</span>
              </button>
            </div>
          </div>

          {/* Tags Organisation */}
          <button 
            className={`nav-tab standalone ${activeTab === 'tags-organisation' ? 'active' : ''}`}
            onClick={() => setActiveTab('tags-organisation')}
            title="Manage tag categories and relationships"
          >
            <span className="tab-icon">🏷️</span>
            <span className="tab-text">Tags Organization</span>
          </button>
        </nav>
      </header>

      <div className="dashboard-content">
        {/* Dashboard Overview */}
        {activeTab === 'dashboard' && renderDashboardOverview()}
        
        {/* RAG Search */}
        {activeTab === 'rag-search' && <RAGSearchModern />}
        
        {/* Twitter Sections */}
        {activeTab === 'twitter-faceted' && <FacetedTweetsDashboard />}
        
        {activeTab === 'twitter-media' && <TwitterMediaGallery />}
        
        {activeTab === 'twitter-trends' && <TrendAnalysis />}
        
        {activeTab === 'twitter-users' && <UserTrendAnalysis />}
        
        {activeTab === 'twitter-charts' && <TrendVisualization />}
        
        {activeTab === 'twitter-summary' && <Summarization />}
        
        {/* Articles Sections */}
        {activeTab === 'articles-faceted' && <FacetedSubstackDashboard />}
        
        {activeTab === 'articles-trends' && <SubstackTrends />}
        
        {activeTab === 'articles-charts' && (
          <div className="articles-charts">
            <h2>Article Analytics</h2>
            <p>Visualizations for article data and trends</p>
            {/* TODO: Create article-specific charts component */}
            <div className="coming-soon">Coming soon...</div>
          </div>
        )}
        
        {/* Papers Sections */}
        {activeTab === 'papers-browse' && <PapersDashboardModern />}
        {activeTab === 'papers-upload' && <PaperUploadModern />}
        {activeTab === 'papers-viewer' && <PaperViewerModern />}
        {activeTab === 'papers-trends' && <PaperTrendsDashboard />}
        
        {/* Phase 4 Analytics */}
        {activeTab === 'unified-timeline' && <UnifiedTimelineView />}
        {activeTab === 'research-analytics' && <ResearchAnalyticsDashboard />}
        
        {/* Phase 5 Advanced Features */}
        {activeTab === 'paper-advanced' && <PaperAdvancedDashboard />}
        {activeTab === 'paper-knowledge-graph' && <PaperKnowledgeGraph />}
        
        {/* Analysis Sections */}
        {activeTab === 'analysis-tweets' && <TrendAnalysis />}
        
        {activeTab === 'analysis-articles' && <SubstackTrends />}
        
        {activeTab === 'analysis-compare' && <UnifiedTrends />}
        
        {activeTab === 'analysis-tag-trends' && (
          <div className="tag-trends-analysis">
            <UnifiedTrends />
          </div>
        )}
        
        {activeTab === 'analysis-clustering' && (
          <div className="clustering-analysis">
            <h2>Content Clustering Analysis</h2>
            <p>Discover patterns and clusters in your AI content</p>
            <UnifiedTrends />
          </div>
        )}
        
        {/* Tags Organisation */}
        {activeTab === 'tags-organisation' && <TagOntologyModern />}
      </div>
    </div>
  )
}

export default Dashboard