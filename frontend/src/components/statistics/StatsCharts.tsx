import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { TrendingUp, Database, Activity, Hash, BookOpen, MessageSquare, AlertCircle, CheckCircle, Info, Search, Image, Tags } from 'lucide-react'
import { LLMUsageTab } from '../StatisticsDashboard/LLMUsageTab'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import type { SystemStats } from './StatisticsDashboard'

interface StatsChartsProps {
  stats: SystemStats
  tabValue: string
}

export function StatsCharts({ stats, tabValue }: StatsChartsProps) {
  switch (tabValue) {
    case 'overview':
      return <OverviewTab stats={stats} />
    case 'content':
      return <ContentTab stats={stats} />
    case 'cross-source':
      return <CrossSourceTab stats={stats} />
    case 'authors':
      return <AuthorsTab stats={stats} />
    case 'trends':
      return <TrendsTab stats={stats} />
    case 'llm':
      return <LLMTab stats={stats} />
    case 'system':
      return <SystemTab stats={stats} />
    default:
      return null
  }
}

function OverviewTab({ stats }: { stats: SystemStats }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Tweet Timeline */}
        <Card>
          <CardHeader>
            <CardTitle>Tweet Activity (7 Days)</CardTitle>
            <CardDescription>Daily tweet collection statistics</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={stats.timeline.tweets_per_day}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="count" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Tag Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Top Tags</CardTitle>
            <CardDescription>Most frequently used tags</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={stats.tags.most_used}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="tag" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Tweets with Media</p>
                <p className="text-xl font-semibold">{stats.tweets.with_media}</p>
              </div>
              <Image className="h-8 w-8 text-blue-500 opacity-50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Articles with Summaries</p>
                <p className="text-xl font-semibold">{stats.articles.with_summaries}</p>
              </div>
              <BookOpen className="h-8 w-8 text-green-500 opacity-50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Snippets</p>
                <p className="text-xl font-semibold">{stats.articles.with_snippets}</p>
              </div>
              <MessageSquare className="h-8 w-8 text-purple-500 opacity-50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Database Size</p>
                <p className="text-xl font-semibold">{stats.system.database_size}</p>
              </div>
              <Database className="h-8 w-8 text-orange-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function ContentTab({ stats }: { stats: SystemStats }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Tweet Statistics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Total Tweets</span>
              <span className="font-medium">{stats.tweets.total.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Today</span>
              <span className="font-medium text-green-600">+{stats.tweets.today}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">This Week</span>
              <span className="font-medium">{stats.tweets.this_week}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">This Month</span>
              <span className="font-medium">{stats.tweets.this_month}</span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Retweets</span>
              <span className="font-medium">{stats.tweets.retweets}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Quote Tweets</span>
              <span className="font-medium">{stats.tweets.quotes}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">With Tags</span>
              <span className="font-medium">{stats.tweets.with_tags}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">With Media</span>
              <span className="font-medium">{stats.tweets.with_media}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Article Statistics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Total Articles</span>
              <span className="font-medium">{stats.articles.total}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">This Week</span>
              <span className="font-medium text-green-600">+{stats.articles.this_week}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">This Month</span>
              <span className="font-medium">{stats.articles.this_month}</span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">With Summaries</span>
              <span className="font-medium">{stats.articles.with_summaries}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Total Snippets</span>
              <span className="font-medium">{stats.articles.with_snippets}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Avg Reading Time</span>
              <span className="font-medium">{stats.articles.avg_reading_time} min</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Total Words</span>
              <span className="font-medium">{stats.articles.total_word_count.toLocaleString()}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {stats.papers && (
        <Card>
          <CardHeader>
            <CardTitle>Paper Statistics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Total Papers</span>
                <span className="font-medium">{stats.papers.total}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">This Week</span>
                <span className="font-medium text-green-600">+{stats.papers.this_week}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">This Month</span>
                <span className="font-medium">{stats.papers.this_month}</span>
              </div>
              <Separator />
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">With Tags</span>
                <span className="font-medium">{stats.papers.with_tags}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Tag Coverage</span>
                <span className="font-medium">{stats.papers.tag_coverage}%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function CrossSourceTab({ stats }: { stats: SystemStats }) {
  if (!stats.cross_source) return null

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Content Coverage Analysis</CardTitle>
            <CardDescription>Tag overlap across different content sources</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Tags in All Sources</span>
                <Badge variant="default">{stats.cross_source.content_coverage.tags_in_all_sources}</Badge>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-sm">Tweets + Articles</span>
                <Badge variant="secondary">{stats.cross_source.content_coverage.tags_in_tweets_articles}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Tweets + Papers</span>
                <Badge variant="secondary">{stats.cross_source.content_coverage.tags_in_tweets_papers}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Articles + Papers</span>
                <Badge variant="secondary">{stats.cross_source.content_coverage.tags_in_articles_papers}</Badge>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-sm">Tweet-Only Tags</span>
                <Badge variant="outline">{stats.cross_source.content_coverage.tweets_only_tags}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Article-Only Tags</span>
                <Badge variant="outline">{stats.cross_source.content_coverage.articles_only_tags}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Paper-Only Tags</span>
                <Badge variant="outline">{stats.cross_source.content_coverage.papers_only_tags}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tag Distribution by Source</CardTitle>
            <CardDescription>How tags are distributed across content types</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(stats.cross_source.tag_distribution).map(([source, data]) => (
                <div key={source} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium capitalize">{source}</span>
                    <Badge>{data.unique_tags} unique</Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {data.total_applications} applications • {data.avg_tags_per_item} avg/item
                  </div>
                  <Progress
                    value={(data.unique_tags / stats.tags.unique) * 100}
                    className="h-2"
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {stats.cross_source.universal_tags.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Universal Tags</CardTitle>
            <CardDescription>Tags that appear across all content sources</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {stats.cross_source.universal_tags.map((tag) => (
                <Badge key={`universal-${tag}`} variant="default" className="py-1">
                  <Hash className="h-3 w-3 mr-1" />
                  {tag}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </>
  )
}

function AuthorsTab({ stats }: { stats: SystemStats }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Top Twitter Authors</CardTitle>
          <CardDescription>Most active Twitter accounts</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[300px]">
            <div className="space-y-4">
              {stats.authors.twitter.map((author, i) => (
                <div key={`twitter-${author.username}`} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold text-sm">
                      {i + 1}
                    </div>
                    <div>
                      <p className="font-medium">{author.username}</p>
                      <p className="text-sm text-muted-foreground">Last: {author.latest_tweet}</p>
                    </div>
                  </div>
                  <Badge variant="secondary">{author.tweet_count} tweets</Badge>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Newsletter Authors</CardTitle>
          <CardDescription>Most prolific article authors</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[300px]">
            <div className="space-y-4">
              {stats.authors.articles.map((author, i) => (
                <div key={`article-${author.name}`} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 text-green-600 font-semibold text-sm">
                      {i + 1}
                    </div>
                    <div>
                      <p className="font-medium">{author.name}</p>
                      <p className="text-sm text-muted-foreground">Last: {author.latest_article}</p>
                    </div>
                  </div>
                  <Badge variant="secondary">{author.article_count} articles</Badge>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}
function TrendsTab({ stats }: { stats: SystemStats }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Hot Topics</CardTitle>
            <CardDescription>Currently trending discussions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.trends.hot_topics.map((topic) => (
                <div key={`topic-${topic.topic}`} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {topic.trend === 'up' && <TrendingUp className="h-4 w-4 text-green-500" />}
                    {topic.trend === 'down' && <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />}
                    {topic.trend === 'stable' && <Activity className="h-4 w-4 text-gray-500" />}
                    <span className="font-medium">{topic.topic}</span>
                  </div>
                  <Badge variant={topic.trend === 'up' ? 'default' : topic.trend === 'down' ? 'destructive' : 'secondary'}>
                    {topic.mentions} mentions
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Emerging Tags</CardTitle>
            <CardDescription>Fastest growing tags</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.trends.emerging_tags.map((tag) => (
                <div key={`emerging-${tag.tag}`} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{tag.tag}</span>
                    <span className="text-sm text-green-600">+{tag.growth_rate}%</span>
                  </div>
                  <Progress value={Math.min(tag.growth_rate, 100)} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recently Added Tags</CardTitle>
          <CardDescription>Newest tags in the system</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {stats.tags.recently_added.map((tag) => (
              <Badge key={`recent-${tag.tag}-${tag.date}`} variant="outline" className="py-1">
                <Hash className="h-3 w-3 mr-1" />
                {tag.tag}
                <span className="ml-2 text-xs text-muted-foreground">{tag.date}</span>
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function LLMTab({ stats }: { stats: SystemStats }) {
  if (!stats.llm_usage) return null
  return <LLMUsageTab llmUsage={stats.llm_usage} />
}
function SystemTab({ stats }: { stats: SystemStats }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
          <CardDescription>Overall system status</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4" />
                <span>Database</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-sm">{stats.system.database_size}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Search className="h-4 w-4" />
                <span>RAG Index</span>
              </div>
              <div className="flex items-center gap-2">
                {stats.system.index_status.is_ready ? (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="text-sm">{stats.system.index_status.rag_documents} docs</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-4 w-4 text-yellow-500" />
                    <span className="text-sm">Index needs rebuild</span>
                  </>
                )}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Tags className="h-4 w-4" />
                <span>Tag Organization</span>
              </div>
              <div className="flex items-center gap-2">
                <Info className="h-4 w-4 text-blue-500" />
                <span className="text-sm">
                  {((stats.tags.organized / stats.tags.unique) * 100).toFixed(1)}% organized
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Collection Status</CardTitle>
          <CardDescription>Data collection schedule</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-muted-foreground">Last Tweet Collection</span>
                <Badge variant="outline">
                  {new Date(stats.system.collection_status.last_tweet_collection).toLocaleTimeString()}
                </Badge>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-muted-foreground">Last Article Collection</span>
                <Badge variant="outline">
                  {new Date(stats.system.collection_status.last_article_collection).toLocaleTimeString()}
                </Badge>
              </div>
            </div>
            {stats.papers && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-muted-foreground">Total Papers</span>
                  <Badge variant="outline">
                    {stats.papers.total} papers ({stats.papers.with_tags} tagged)
                  </Badge>
                </div>
              </div>
            )}
            <Separator />
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-muted-foreground">Next Scheduled</span>
                <Badge>
                  {stats.system.collection_status.next_scheduled === 'Manual collection only'
                    ? 'Manual'
                    : stats.system.collection_status.next_scheduled && !isNaN(new Date(stats.system.collection_status.next_scheduled).getTime())
                      ? new Date(stats.system.collection_status.next_scheduled).toLocaleTimeString()
                      : 'N/A'}
                </Badge>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-muted-foreground">Index Last Updated</span>
                <Badge variant="outline">
                  {stats.system.index_status.last_updated && stats.system.index_status.last_updated !== 'N/A' && !isNaN(new Date(stats.system.index_status.last_updated).getTime())
                    ? new Date(stats.system.index_status.last_updated).toLocaleDateString()
                    : 'N/A'}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
