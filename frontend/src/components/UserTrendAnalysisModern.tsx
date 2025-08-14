import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
import { 
  TrendingUp,
  TrendingDown,
  Activity,
  User,
  Clock,
  Hash,
  BarChart3,
  Calendar,
  MessageSquare,
  Heart,
  Repeat2,
  Loader2,
  AlertCircle,
  Sparkles,
  Flame,
  Zap,
  Moon,
  Pause,
  ChevronRight,
  ExternalLink,
  Twitter
} from 'lucide-react'

interface UserTrend {
  tweet_count: number
  latest_tweet: string | null
  latest_text: string | null
  top_tags: { tag: string; count: number }[]
  daily_activity: Record<string, number>
  avg_daily: number
}

interface UserTrendsData {
  period_hours: number
  users: Record<string, UserTrend>
  total_users: number
  last_updated: string
}

interface UserDetails {
  username: string
  total_tweets: number
  avg_likes: number
  avg_retweets: number
  top_hashtags: { tag: string; count: number }[]
  top_mentions: { user: string; count: number }[]
  tweet_times: Record<string, number>
  sentiment_scores: { positive: number; neutral: number; negative: number }
  topics: string[]
  recent_tweets: Array<{
    id: string
    text: string
    created_at: string
    likes: number
    retweets: number
  }>
}

export default function UserTrendAnalysisModern() {
  const [userTrends, setUserTrends] = useState<UserTrendsData | null>(null)
  const [selectedUser, setSelectedUser] = useState<string | null>(null)
  const [userDetails, setUserDetails] = useState<UserDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [timeframe, setTimeframe] = useState(168) // 7 days default

  useEffect(() => {
    fetchUserTrends()
  }, [timeframe])

  useEffect(() => {
    if (selectedUser) {
      fetchUserDetails(selectedUser)
    }
  }, [selectedUser])

  const fetchUserTrends = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`http://localhost:8000/api/user-trends/per-user?hours=${timeframe}`)
      setUserTrends(response.data)
    } catch (error) {
      console.error('Error fetching user trends:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchUserDetails = async (username: string) => {
    setLoadingDetails(true)
    try {
      const response = await axios.get(`http://localhost:8000/api/user-trends/user/${username}?days=${timeframe / 24}`)
      setUserDetails(response.data)
    } catch (error) {
      console.error('Error fetching user details:', error)
    } finally {
      setLoadingDetails(false)
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)
    
    if (diffHours < 1) return 'Just now'
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  const getActivityLevel = (avgDaily: number | undefined) => {
    if (!avgDaily || avgDaily === 0) return { icon: <Pause className="h-4 w-4" />, level: 'Inactive', color: 'text-gray-400' }
    if (avgDaily > 10) return { icon: <Flame className="h-4 w-4" />, level: 'Very Active', color: 'text-red-500' }
    if (avgDaily > 5) return { icon: <Zap className="h-4 w-4" />, level: 'Active', color: 'text-orange-500' }
    if (avgDaily > 1) return { icon: <Sparkles className="h-4 w-4" />, level: 'Moderate', color: 'text-green-500' }
    if (avgDaily > 0) return { icon: <Moon className="h-4 w-4" />, level: 'Low', color: 'text-gray-500' }
    return { icon: <Pause className="h-4 w-4" />, level: 'Inactive', color: 'text-gray-400' }
  }

  const calculateTrend = (dailyActivity: Record<string, number>) => {
    const values = Object.values(dailyActivity)
    if (values.length < 2) return 'stable'
    
    const firstHalf = values.slice(0, Math.floor(values.length / 2))
    const secondHalf = values.slice(Math.floor(values.length / 2))
    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length
    
    if (secondAvg > firstAvg * 1.2) return 'up'
    if (secondAvg < firstAvg * 0.8) return 'down'
    return 'stable'
  }

  const getTrendIcon = (trend: string) => {
    switch(trend) {
      case 'up': return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'down': return <TrendingDown className="h-4 w-4 text-red-500" />
      default: return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto p-4 max-w-7xl">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 mr-3" />
          <span className="text-gray-500">Analyzing user trends...</span>
        </div>
      </div>
    )
  }

  if (!userTrends) {
    return (
      <div className="container mx-auto p-4 max-w-7xl">
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <p className="text-gray-600">Failed to load user trends</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const sortedUsers = Object.entries(userTrends.users).sort(
    ([, a], [, b]) => b.tweet_count - a.tweet_count
  )

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">User Activity Analysis</h1>
        <p className="text-gray-600">Track individual user engagement and posting patterns</p>
      </div>

      {/* Controls */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Select value={timeframe.toString()} onValueChange={(v) => setTimeframe(parseInt(v))}>
                <SelectTrigger className="w-40">
                  <Clock className="h-4 w-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="24">Last 24 hours</SelectItem>
                  <SelectItem value="72">Last 3 days</SelectItem>
                  <SelectItem value="168">Last 7 days</SelectItem>
                  <SelectItem value="720">Last 30 days</SelectItem>
                </SelectContent>
              </Select>
              
              <Badge variant="secondary" className="py-1.5 px-3">
                <User className="h-3 w-3 mr-1" />
                {userTrends.total_users} users tracked
              </Badge>
              
              <Badge variant="outline" className="py-1.5 px-3">
                <Clock className="h-3 w-3 mr-1" />
                Updated: {formatDate(userTrends.last_updated)}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* User List */}
        <div className="lg:col-span-1">
          <Card className="h-[600px] flex flex-col">
            <CardHeader>
              <CardTitle className="text-lg">Tracked Users</CardTitle>
              <CardDescription>Click to view detailed analytics</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 p-0">
              <ScrollArea className="h-full px-4 pb-4">
                <div className="space-y-2">
                  {sortedUsers.map(([username, data]) => {
                    const activity = getActivityLevel(data.avg_daily)
                    const trend = calculateTrend(data.daily_activity)
                    const isSelected = selectedUser === username
                    
                    return (
                      <Card
                        key={username}
                        className={cn(
                          "cursor-pointer transition-all hover:shadow-md",
                          isSelected && "ring-2 ring-blue-500"
                        )}
                        onClick={() => setSelectedUser(username)}
                      >
                        <CardContent className="p-3">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <div className={cn("p-1.5 rounded-full bg-gray-100", activity.color)}>
                                {activity.icon}
                              </div>
                              <div>
                                <p className="font-semibold text-sm">@{username}</p>
                                <p className="text-xs text-gray-500">{formatDate(data.latest_tweet)}</p>
                              </div>
                            </div>
                            {getTrendIcon(trend)}
                          </div>
                          
                          <div className="grid grid-cols-2 gap-2 mb-2">
                            <div className="text-center p-1 bg-gray-50 rounded">
                              <p className="text-xs text-gray-500">Tweets</p>
                              <p className="text-sm font-semibold">{data.tweet_count}</p>
                            </div>
                            <div className="text-center p-1 bg-gray-50 rounded">
                              <p className="text-xs text-gray-500">Daily Avg</p>
                              <p className="text-sm font-semibold">{data.avg_daily?.toFixed(1) || '0.0'}</p>
                            </div>
                          </div>
                          
                          {data.top_tags.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {data.top_tags.slice(0, 3).map(tag => (
                                <Badge key={tag.tag} variant="secondary" className="text-xs">
                                  {tag.tag}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    )
                  })}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* User Details */}
        <div className="lg:col-span-2">
          {selectedUser ? (
            loadingDetails ? (
              <Card className="h-[600px]">
                <CardContent className="h-full flex items-center justify-center">
                  <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                </CardContent>
              </Card>
            ) : (
              <Card className="h-[600px] flex flex-col">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-xl">@{selectedUser}</CardTitle>
                      <CardDescription>Detailed activity analysis</CardDescription>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => window.open(`https://twitter.com/${selectedUser}`, '_blank')}
                    >
                      <Twitter className="h-4 w-4 mr-2" />
                      View Profile
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 overflow-hidden">
                  <Tabs defaultValue="activity" className="h-full">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="activity">Activity</TabsTrigger>
                      <TabsTrigger value="content">Content</TabsTrigger>
                      <TabsTrigger value="engagement">Engagement</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="activity" className="mt-4 h-[calc(100%-3rem)] overflow-auto">
                      <div className="space-y-4">
                        {/* Daily Activity Chart */}
                        <div>
                          <h3 className="text-sm font-semibold mb-2">Daily Activity</h3>
                          <div className="bg-gray-50 rounded-lg p-3">
                            <div className="flex items-end gap-1 h-32">
                              {Object.entries(userTrends.users[selectedUser].daily_activity).map(([date, count]) => {
                                const maxCount = Math.max(...Object.values(userTrends.users[selectedUser].daily_activity))
                                const height = maxCount > 0 ? (count / maxCount) * 100 : 0
                                
                                return (
                                  <div
                                    key={date}
                                    className="flex-1 flex flex-col items-center"
                                  >
                                    <div
                                      className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600"
                                      style={{ height: `${height}%` }}
                                      title={`${date}: ${count} tweets`}
                                    />
                                    <span className="text-xs text-gray-500 mt-1">
                                      {new Date(date).getDate()}
                                    </span>
                                  </div>
                                )
                              })}
                            </div>
                          </div>
                        </div>

                        {/* Latest Tweet */}
                        {userTrends.users[selectedUser].latest_text && (
                          <div>
                            <h3 className="text-sm font-semibold mb-2">Latest Tweet</h3>
                            <Card>
                              <CardContent className="p-3">
                                <p className="text-sm text-gray-700 mb-2">
                                  {userTrends.users[selectedUser].latest_text}
                                </p>
                                <p className="text-xs text-gray-500">
                                  {formatDate(userTrends.users[selectedUser].latest_tweet)}
                                </p>
                              </CardContent>
                            </Card>
                          </div>
                        )}
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="content" className="mt-4 h-[calc(100%-3rem)] overflow-auto">
                      <div className="space-y-4">
                        {/* Top Tags */}
                        <div>
                          <h3 className="text-sm font-semibold mb-2">Top Tags Used</h3>
                          <div className="space-y-2">
                            {userTrends.users[selectedUser].top_tags.map(tag => (
                              <div key={tag.tag} className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <Hash className="h-3 w-3 text-gray-400" />
                                  <span className="text-sm">{tag.tag}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <Progress value={(tag.count / userTrends.users[selectedUser].tweet_count) * 100} className="w-20 h-2" />
                                  <Badge variant="secondary" className="text-xs">
                                    {tag.count}
                                  </Badge>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Topics if available from userDetails */}
                        {userDetails?.topics && userDetails.topics.length > 0 && (
                          <div>
                            <h3 className="text-sm font-semibold mb-2">Main Topics</h3>
                            <div className="flex flex-wrap gap-2">
                              {userDetails.topics.map(topic => (
                                <Badge key={topic} variant="outline">
                                  {topic}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="engagement" className="mt-4 h-[calc(100%-3rem)] overflow-auto">
                      <div className="space-y-4">
                        {userDetails ? (
                          <>
                            {/* Engagement Stats */}
                            <div className="grid grid-cols-2 gap-4">
                              <Card>
                                <CardContent className="p-3">
                                  <div className="flex items-center justify-between">
                                    <div>
                                      <p className="text-xs text-gray-500">Avg Likes</p>
                                      <p className="text-xl font-bold">{userDetails.avg_likes?.toFixed(1) || '0.0'}</p>
                                    </div>
                                    <Heart className="h-5 w-5 text-red-500" />
                                  </div>
                                </CardContent>
                              </Card>
                              
                              <Card>
                                <CardContent className="p-3">
                                  <div className="flex items-center justify-between">
                                    <div>
                                      <p className="text-xs text-gray-500">Avg Retweets</p>
                                      <p className="text-xl font-bold">{userDetails.avg_retweets?.toFixed(1) || '0.0'}</p>
                                    </div>
                                    <Repeat2 className="h-5 w-5 text-green-500" />
                                  </div>
                                </CardContent>
                              </Card>
                            </div>

                            {/* Sentiment if available */}
                            {userDetails.sentiment_scores && (
                              <div>
                                <h3 className="text-sm font-semibold mb-2">Sentiment Analysis</h3>
                                <div className="space-y-2">
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm">Positive</span>
                                    <div className="flex items-center gap-2">
                                      <Progress value={userDetails.sentiment_scores.positive * 100} className="w-32 h-2" />
                                      <span className="text-xs text-gray-500">
                                        {(userDetails.sentiment_scores.positive * 100).toFixed(0)}%
                                      </span>
                                    </div>
                                  </div>
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm">Neutral</span>
                                    <div className="flex items-center gap-2">
                                      <Progress value={userDetails.sentiment_scores.neutral * 100} className="w-32 h-2" />
                                      <span className="text-xs text-gray-500">
                                        {(userDetails.sentiment_scores.neutral * 100).toFixed(0)}%
                                      </span>
                                    </div>
                                  </div>
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm">Negative</span>
                                    <div className="flex items-center gap-2">
                                      <Progress value={userDetails.sentiment_scores.negative * 100} className="w-32 h-2" />
                                      <span className="text-xs text-gray-500">
                                        {(userDetails.sentiment_scores.negative * 100).toFixed(0)}%
                                      </span>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}
                          </>
                        ) : (
                          <p className="text-sm text-gray-500 text-center py-4">
                            Loading engagement data...
                          </p>
                        )}
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            )
          ) : (
            <Card className="h-[600px]">
              <CardContent className="h-full flex items-center justify-center">
                <div className="text-center">
                  <User className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">Select a user to view detailed analytics</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}