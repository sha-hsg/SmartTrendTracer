import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Twitter,
  FileText,
  Search,
  BarChart3,
  ChevronRight,
  BookOpen,
  BookOpenCheck,
  Library,
  Brain,
  Flame,
  Newspaper,
  Rss,
  Tags,
} from 'lucide-react'
import type { ViewType } from './ModernNavigation'
import { cn } from "@/lib/utils"

interface DashboardHomeProps {
  onNavigate: (view: ViewType) => void
}

interface QuickAccessCardProps {
  title: string
  heading: string
  description: string
  icon: React.ReactNode
  onClick: () => void
  className?: string
}

function QuickAccessCard({ title, heading, description, icon, onClick, className }: QuickAccessCardProps) {
  return (
    <Card
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick()
        }
      }}
      className={cn(
        "cursor-pointer hover:shadow-lg transition-shadow focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
        className
      )}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{heading}</div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  )
}

const QUICK: { title: string; heading: string; description: string; icon: React.ReactNode; view: ViewType; className?: string }[] = [
  { title: 'Trend Detection', heading: 'Trends', description: 'What is new, growing or fading in your bubble',
    icon: <Flame className="h-4 w-4 text-orange-500" />, view: 'trend-dashboard',
    className: 'bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-950 dark:to-red-950 border-orange-200 dark:border-orange-800' },
  { title: 'Weekly Digest', heading: 'Digest', description: 'Briefing on the last 7 days',
    icon: <Newspaper className="h-4 w-4 text-indigo-500" />, view: 'weekly-digest',
    className: 'bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-950 dark:to-blue-950' },
  { title: 'AI Search', heading: 'RAG Search', description: 'Ask questions across all content',
    icon: <Search className="h-4 w-4 text-green-500" />, view: 'rag-search' },
  { title: 'Paper Q&A', heading: 'Ask Papers', description: 'Answers with cited paper sections',
    icon: <BookOpenCheck className="h-4 w-4 text-orange-500" />, view: 'paper-qa' },
  { title: 'Paper Feed', heading: 'New on arXiv', description: 'Candidates ranked by your topics',
    icon: <Rss className="h-4 w-4 text-amber-500" />, view: 'papers-feed' },
  { title: 'System Overview', heading: 'Statistics', description: 'Collection, tagging and index status',
    icon: <BarChart3 className="h-4 w-4 text-blue-500" />, view: 'statistics' },
]

const SECTIONS: { title: string; icon: React.ReactNode; links: { label: string; view: ViewType }[] }[] = [
  { title: 'Twitter/X Analytics', icon: <Twitter className="h-5 w-5 text-blue-400" />, links: [
    { label: 'Browse Tweets', view: 'twitter-faceted' }, { label: 'TweetDeck', view: 'twitter-deck' },
    { label: 'Media Gallery', view: 'twitter-media' }, { label: 'User Analysis', view: 'twitter-users' },
    { label: 'Account Manager', view: 'twitter-accounts' }] },
  { title: 'Articles & Authors', icon: <FileText className="h-5 w-5 text-purple-500" />, links: [
    { label: 'Browse Articles', view: 'articles-faceted' }, { label: 'Article Trends', view: 'articles-trends' },
    { label: 'Manage Authors', view: 'author-management' }] },
  { title: 'Research Papers', icon: <BookOpen className="h-5 w-5 text-orange-500" />, links: [
    { label: 'Browse Papers', view: 'papers-dashboard' }, { label: 'Paper Reviews', view: 'reviews-dashboard' },
    { label: 'References', view: 'papers-references' }, { label: 'Paper Feed', view: 'papers-feed' },
    { label: 'Paper Q&A', view: 'paper-qa' }] },
  { title: 'Book Library', icon: <Library className="h-5 w-5 text-emerald-500" />, links: [
    { label: 'Browse Books', view: 'books-dashboard' }] },
  { title: 'Analysis', icon: <Brain className="h-5 w-5 text-indigo-600" />, links: [
    { label: 'Trend Dashboard', view: 'trend-dashboard' }, { label: 'Topic Explorer', view: 'topic-explorer' },
    { label: 'AI Summarization', view: 'twitter-summary' }, { label: 'Weekly Digest', view: 'weekly-digest' }] },
  { title: 'Concepts & Search', icon: <Tags className="h-5 w-5 text-teal-500" />, links: [
    { label: 'AI Search', view: 'rag-search' }, { label: 'Concept Management', view: 'concept-management' },
    { label: 'Concept Graph', view: 'concept-graph' }] },
]

export default function DashboardHome({ onNavigate }: DashboardHomeProps) {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-white">
        <h1 className="text-4xl font-bold mb-2">Welcome to SmartTrendTracer</h1>
        <p className="text-xl opacity-90">Your AI bubble — collected, tagged, searchable, and watched for trends</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {QUICK.map(q => (
          <QuickAccessCard key={q.view} title={q.title} heading={q.heading} description={q.description}
            icon={q.icon} onClick={() => onNavigate(q.view)} className={q.className} />
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {SECTIONS.map(section => (
          <Card key={section.title}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">{section.icon}{section.title}</CardTitle>
              <CardDescription className="sr-only">{section.title}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-1">
              {section.links.map(link => (
                <Button key={link.view + link.label} variant="ghost" className="w-full justify-between h-8 px-2"
                  onClick={() => onNavigate(link.view)}>
                  <span className="text-sm">{link.label}</span>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </Button>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
