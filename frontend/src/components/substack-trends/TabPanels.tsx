import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
import {
  TrendingUp,
  Users,
  ArrowUp,
  Link2,
  Activity,
  Target,
} from 'lucide-react'
import type { TrendData } from './types'
import { getProductivityIcon, getProductivityColor, getTrendIcon } from './helpers'

interface TabPanelProps {
  trends: TrendData
}

export function TopicsTabPanel({ trends }: TabPanelProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Trending Up */}
      {trends?.topic_trends?.trending_up?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-500" />
              Trending Up
            </CardTitle>
            <CardDescription>Topics gaining momentum</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              <div className="space-y-2">
                {(trends?.topic_trends?.trending_up || []).map((topic, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50">
                    <span className="font-medium">{topic.term}</span>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-green-100 text-green-700 border-green-200">
                        +{topic.growth} articles
                      </Badge>
                      <ArrowUp className="h-4 w-4 text-green-500" />
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Tag Relationships */}
      {trends?.tag_trends?.tag_relationships?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Link2 className="h-5 w-5 text-blue-500" />
              Related Tags
            </CardTitle>
            <CardDescription>Commonly co-occurring tags</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {(trends?.tag_trends?.tag_relationships || []).slice(0, 5).map((rel, idx) => (
                  <div key={idx} className="space-y-2">
                    <div className="font-medium text-sm">{rel.tag}</div>
                    <div className="flex flex-wrap gap-1">
                      {rel.related.map((r, ridx) => (
                        <Badge key={ridx} variant="outline" className="text-xs">
                          {r.tag}
                          <span className="ml-1 text-gray-400">({r.strength})</span>
                        </Badge>
                      ))}
                    </div>
                    {idx < (trends?.tag_trends?.tag_relationships?.length || 0) - 1 && (
                      <Separator className="mt-2" />
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export function AuthorsTabPanel({ trends }: TabPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          Most Active Authors
        </CardTitle>
        <CardDescription>Author productivity and focus areas</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(trends?.author_trends?.most_active || []).map((author, idx) => (
            <Card key={idx}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-semibold">{author.author}</h4>
                    <Badge
                      variant="outline"
                      className={cn("mt-1", getProductivityColor(author.productivity))}
                    >
                      {getProductivityIcon(author.productivity)}
                      <span className="ml-1">{author.productivity?.replace('_', ' ') || 'unknown'}</span>
                    </Badge>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 mb-3 text-sm">
                  <div>
                    <span className="text-gray-500">Articles:</span>
                    <span className="ml-2 font-medium">{author.articles}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Avg words:</span>
                    <span className="ml-2 font-medium">{author.avg_words?.toLocaleString() || 0}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Reading time:</span>
                    <span className="ml-2 font-medium">{author.avg_reading_time?.toFixed(1) || 0} min</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Snippets:</span>
                    <span className="ml-2 font-medium">{author.total_snippets}</span>
                  </div>
                </div>

                {author.topics.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {author.topics.map((topic, tidx) => (
                      <Badge key={tidx} variant="secondary" className="text-xs">
                        {topic}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export function VelocityTabPanel({ trends }: TabPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Topic Velocity Analysis
        </CardTitle>
        <CardDescription>Rate of change in topic discussion</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {(trends?.velocity_trends || []).map((item, idx) => (
            <div
              key={idx}
              className={cn(
                "flex items-center justify-between p-3 rounded-lg border",
                item.trend === 'rising' && "bg-green-50 border-green-200",
                item.trend === 'falling' && "bg-red-50 border-red-200",
                item.trend === 'stable' && "bg-gray-50 border-gray-200"
              )}
            >
              <div className="flex items-center gap-3">
                {getTrendIcon(item.trend)}
                <span className="font-medium">{item.topic}</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <span className="text-gray-600">
                  {item.first_period} → {item.second_period}
                </span>
                <Badge
                  variant={item.velocity > 0 ? "default" : "secondary"}
                  className={cn(
                    item.velocity > 0 && "bg-green-100 text-green-700",
                    item.velocity < 0 && "bg-red-100 text-red-700"
                  )}
                >
                  {item.velocity > 0 ? '+' : ''}{((item.velocity || 0) * 100).toFixed(0)}%
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export function ClustersTabPanel({ trends }: TabPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5" />
          Content Clusters
        </CardTitle>
        <CardDescription>Articles grouped by similar themes</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {(trends?.content_clusters || []).map((cluster, idx) => (
            <Card key={idx}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    Cluster {cluster.cluster_id + 1}: {cluster.theme}
                  </CardTitle>
                  <Badge variant="secondary">{cluster.size} articles</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Keywords</p>
                    <div className="flex flex-wrap gap-1">
                      {cluster.keywords.map((keyword, kidx) => (
                        <Badge key={kidx} variant="outline" className="text-xs">
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {cluster.articles.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Sample Articles</p>
                      <div className="space-y-1">
                        {cluster.articles.slice(0, 2).map((article, aidx) => (
                          <div key={aidx} className="text-xs">
                            <span className="font-medium">{article.title}</span>
                            <span className="text-gray-500 ml-1">by {article.author}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
