import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import {
  Twitter,
  FileText,
  Tags,
  Database,
  AlertCircle,
  CheckCircle,
} from 'lucide-react'
import type { SystemStats } from './StatisticsDashboard'

interface StatsOverviewCardsProps {
  stats: SystemStats
}

export function StatsOverviewCards({ stats }: StatsOverviewCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Tweets</CardTitle>
          <Twitter className="h-4 w-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.tweets.total.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">
            +{stats.tweets.today} today
          </p>
          <Progress value={85} className="mt-2" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Articles</CardTitle>
          <FileText className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.articles.total}</div>
          <p className="text-xs text-muted-foreground">
            +{stats.articles.this_week} this week
          </p>
          <Progress value={65} className="mt-2" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Unique Tags</CardTitle>
          <Tags className="h-4 w-4 text-purple-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.tags.unique}</div>
          <p className="text-xs text-muted-foreground">
            {stats.tags.organized} organized
          </p>
          <Progress value={(stats.tags.organized / stats.tags.unique) * 100} className="mt-2" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">RAG Index</CardTitle>
          <Database className="h-4 w-4 text-orange-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.system.index_status.rag_documents.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">
            {stats.system.index_status.is_ready ? (
              <span className="flex items-center gap-1">
                <CheckCircle className="h-3 w-3 text-green-500" />
                Ready
              </span>
            ) : (
              <span className="flex items-center gap-1">
                <AlertCircle className="h-3 w-3 text-yellow-500" />
                Building
              </span>
            )}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
