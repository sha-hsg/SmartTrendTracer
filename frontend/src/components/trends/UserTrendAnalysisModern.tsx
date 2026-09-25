import { useState, useEffect } from 'react'
import http from '@/services/http'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import {
  TrendingUp,
  TrendingDown,
  Activity,
  User,
  Clock,
  Hash,
  Heart,
  Repeat2,
  Loader2,
  AlertCircle,
  Sparkles,
  Flame,
  Zap,
  Moon,
  Pause,
  Twitter,
  Users,
  Target
} from 'lucide-react'
import type { UserTrendsResponse, UserDetails } from './UserTrendAnalysisModern.types'

export default function UserTrendAnalysisModern() {
  const [userTrends, setUserTrends] = useState<UserTrendsResponse | null>(null)
  const [selectedUser, setSelectedUser] = useState<string | null>(null)
  const [_userDetails, setUserDetails] = useState<UserDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [_loadingDetails, setLoadingDetails] = useState(false)
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
      const response = await http.get(`/api/user-trends/per-user?hours=${timeframe}`)
      setUserTrends(response.data)
      // Auto-select first user if none selected
      if (!selectedUser && response.data.users.length > 0) {
        setSelectedUser(response.data.users[0].username)
      }
    } catch (error) {
      console.error('Error fetching user trends:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchUserDetails = async (username: string) => {
    setLoadingDetails(true)
    try {
      const response = await http.get(`/api/user-trends/user/${username}?days=${Math.floor(timeframe / 24)}`)
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

  const getActivityLevel = (tweetCount: number, hours: number) => {
    const avgDaily = (tweetCount / hours) * 24
    if (avgDaily === 0) return { icon: <Pause className="h-4 w-4" />, level: 'Inactive', color: 'text-gray-400' }
    if (avgDaily > 10) return { icon: <Flame className="h-4 w-4" />, level: 'Very Active', color: 'text-red-500' }
    if (avgDaily > 5) return { icon: <Zap className="h-4 w-4" />, level: 'Active', color: 'text-orange-500' }
    if (avgDaily > 1) return { icon: <Sparkles className="h-4 w-4" />, level: 'Moderate', color: 'text-green-500' }
    if (avgDaily > 0) return { icon: <Moon className="h-4 w-4" />, level: 'Low', color: 'text-gray-500' }
    return { icon: <Pause className="h-4 w-4" />, level: 'Inactive', color: 'text-gray-400' }
  }

  const calculateTrend = (username: string): string => {
    if (!userTrends?.timeline || userTrends.timeline.length < 2) return 'stable'
    
    // Get user's activity from timeline
    const userActivity = userTrends.timeline
      .map(point => point.users[username] || 0)
      .filter(count => count !== undefined)
    
    if (userActivity.length < 2) return 'stable'
    
    const firstHalf = userActivity.slice(0, Math.floor(userActivity.length / 2))
    const secondHalf = userActivity.slice(Math.floor(userActivity.length / 2))
    
    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / Math.max(firstHalf.length, 1)
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / Math.max(secondHalf.length, 1)
    
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
                {userTrends.users.length} users tracked
              </Badge>
              
              <Badge variant="outline" className="py-1.5 px-3">
                <Clock className="h-3 w-3 mr-1" />
                Period: {formatDate(userTrends.start_date)} - {formatDate(userTrends.end_date)}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {userTrends.user_statistics.most_active && (
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Most Active</p>
                  <p className="text-lg font-bold">@{userTrends.user_statistics.most_active.username}</p>
                  <p className="text-sm text-gray-600">{userTrends.user_statistics.most_active.tweet_count} tweets</p>
                </div>
                <Flame className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        )}
        
        {userTrends.user_statistics.most_diverse_concepts && (
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Most Diverse</p>
                  <p className="text-lg font-bold">@{userTrends.user_statistics.most_diverse_concepts.username}</p>
                  <p className="text-sm text-gray-600">{userTrends.user_statistics.most_diverse_concepts.unique_concepts} concepts</p>
                </div>
                <Target className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
        )}
        
        {userTrends.user_statistics.highest_engagement && (
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Highest Engagement</p>
                  <p className="text-lg font-bold">@{userTrends.user_statistics.highest_engagement.username}</p>
                  <p className="text-sm text-gray-600">{userTrends.user_statistics.highest_engagement.engagement_rate} avg</p>
                </div>
                <Heart className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        )}
      </div>

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
                  {userTrends.users.map((user) => {
                    const activity = getActivityLevel(user.tweet_count, userTrends.period_hours)
                    const trend = calculateTrend(user.username)
                    const isSelected = selectedUser === user.username
                    
                    return (
                      <Card
                        key={user.username}
                        className={cn(
                          "cursor-pointer transition-all hover:shadow-md",
                          isSelected && "ring-2 ring-blue-500"
                        )}
                        onClick={() => setSelectedUser(user.username)}
                      >
                        <CardContent className="p-3">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <div className={cn("p-1.5 rounded-full bg-gray-100", activity.color)}>
                                {activity.icon}
                              </div>
                              <div>
                                <p className="font-semibold text-sm">@{user.username}</p>
                                <p className="text-xs text-gray-500">{activity.level}</p>
                              </div>
                            </div>
                            {getTrendIcon(trend)}
                          </div>
                          
                          <div className="grid grid-cols-3 gap-2 mb-2">
                            <div className="text-center p-1 bg-gray-50 rounded">
                              <p className="text-xs text-gray-500">Tweets</p>
                              <p className="text-sm font-semibold">{user.tweet_count}</p>
                            </div>
                            <div className="text-center p-1 bg-gray-50 rounded">
                              <p className="text-xs text-gray-500">Concepts</p>
                              <p className="text-sm font-semibold">{user.unique_concepts}</p>
                            </div>
                            <div className="text-center p-1 bg-gray-50 rounded">
                              <p className="text-xs text-gray-500">Engage</p>
                              <p className="text-sm font-semibold">{user.engagement_rate}</p>
                            </div>
                          </div>
                          
                          {user.top_concepts && user.top_concepts.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {user.top_concepts.slice(0, 3).map(concept => (
                                <Badge key={concept.name} variant="secondary" className="text-xs">
                                  {concept.name}
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
                    <TabsTrigger value="concepts">Concepts</TabsTrigger>
                    <TabsTrigger value="cross-user">Cross-User</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="activity" className="mt-4 h-[calc(100%-3rem)] overflow-auto">
                    <div className="space-y-4">
                      {/* Activity Timeline */}
                      <div>
                        <h3 className="text-sm font-semibold mb-2">Activity Timeline (Last 24 Hours)</h3>
                        {userTrends.timeline && userTrends.timeline.length > 0 ? (
                          <div className="bg-gray-50 rounded-lg p-3">
                            <div className="flex items-end gap-1 h-32">
                              {userTrends.timeline.slice(-24).map((point, idx) => {
                                const count = point.users[selectedUser] || 0
                                const maxCount = Math.max(...userTrends.timeline.slice(-24).map(p => p.users[selectedUser] || 0))
                                const height = maxCount > 0 ? (count / maxCount) * 100 : 0
                                const date = new Date(point.time)
                                const hour = date.getHours()
                                
                                // Only show label every 4 hours or if there's activity
                                const showLabel = idx % 4 === 0 || count > 0
                                
                                return (
                                  <div
                                    key={point.time}
                                    className="flex-1 flex flex-col items-center justify-end"
                                  >
                                    {count > 0 && (
                                      <div
                                        className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600 min-h-[2px]"
                                        style={{ height: `${height}%` }}
                                        title={`${date.toLocaleDateString()} ${hour}:00 - ${count} tweet${count !== 1 ? 's' : ''}`}
                                      />
                                    )}
                                    {showLabel && (
                                      <span className="text-xs text-gray-500 mt-1">
                                        {hour}h
                                      </span>
                                    )}
                                  </div>
                                )
                              })}
                            </div>
                            <div className="text-xs text-gray-500 text-center mt-2">
                              {userTrends.timeline.length > 0 && (
                                <>
                                  {new Date(userTrends.timeline[Math.max(0, userTrends.timeline.length - 24)].time).toLocaleDateString()} - 
                                  {' '}{new Date(userTrends.timeline[userTrends.timeline.length - 1].time).toLocaleDateString()}
                                </>
                              )}
                            </div>
                          </div>
                        ) : (
                          <div className="bg-gray-50 rounded-lg p-8 text-center">
                            <Clock className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                            <p className="text-sm text-gray-500">No activity data available for this user</p>
                          </div>
                        )}
                      </div>

                      {/* Engagement Stats */}
                      {(() => {
                        const userData = userTrends.users.find(u => u.username === selectedUser)
                        if (!userData) return null
                        
                        return (
                          <div className="grid grid-cols-2 gap-4">
                            <Card>
                              <CardContent className="p-3">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-xs text-gray-500">Total Likes</p>
                                    <p className="text-xl font-bold">{userData.total_likes}</p>
                                  </div>
                                  <Heart className="h-5 w-5 text-red-500" />
                                </div>
                              </CardContent>
                            </Card>
                            
                            <Card>
                              <CardContent className="p-3">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-xs text-gray-500">Total Retweets</p>
                                    <p className="text-xl font-bold">{userData.total_retweets}</p>
                                  </div>
                                  <Repeat2 className="h-5 w-5 text-green-500" />
                                </div>
                              </CardContent>
                            </Card>
                          </div>
                        )
                      })()}
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="concepts" className="mt-4 h-[calc(100%-3rem)] overflow-auto">
                    <div className="space-y-4">
                      {/* Top Concepts */}
                      {userTrends.top_concepts_by_user[selectedUser] && (
                        <div>
                          <h3 className="text-sm font-semibold mb-2">Top Concepts Used</h3>
                          <div className="space-y-2">
                            {userTrends.top_concepts_by_user[selectedUser].map(concept => {
                              const userData = userTrends.users.find(u => u.username === selectedUser)
                              const percentage = userData ? (concept.count / userData.tweet_count) * 100 : 0
                              
                              return (
                                <div key={concept.name} className="flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <Hash className="h-3 w-3 text-gray-400" />
                                    <span className="text-sm">{concept.name}</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Progress value={percentage} className="w-20 h-2" />
                                    <Badge variant="secondary" className="text-xs">
                                      {concept.count}
                                    </Badge>
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )}

                      {/* Activity Details */}
                      {userTrends.activity_by_user[selectedUser] && (
                        <div>
                          <h3 className="text-sm font-semibold mb-2">Activity Summary</h3>
                          <div className="grid grid-cols-3 gap-2">
                            <Card>
                              <CardContent className="p-2 text-center">
                                <p className="text-xs text-gray-500">Total Tweets</p>
                                <p className="text-lg font-bold">{userTrends.activity_by_user[selectedUser].total_tweets}</p>
                              </CardContent>
                            </Card>
                            <Card>
                              <CardContent className="p-2 text-center">
                                <p className="text-xs text-gray-500">Engagement Rate</p>
                                <p className="text-lg font-bold">{userTrends.activity_by_user[selectedUser].engagement_rate}</p>
                              </CardContent>
                            </Card>
                            <Card>
                              <CardContent className="p-2 text-center">
                                <p className="text-xs text-gray-500">Unique Concepts</p>
                                <p className="text-lg font-bold">{userTrends.activity_by_user[selectedUser].unique_concepts}</p>
                              </CardContent>
                            </Card>
                          </div>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="cross-user" className="mt-4 h-[calc(100%-3rem)] overflow-auto">
                    <div className="space-y-4">
                      <h3 className="text-sm font-semibold mb-2">Shared Concepts</h3>
                      <div className="space-y-2">
                        {userTrends.cross_user_concepts
                          .filter(concept => concept.users.includes(selectedUser))
                          .map(concept => (
                            <Card key={concept.concept}>
                              <CardContent className="p-3">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="font-medium">{concept.concept}</span>
                                  <Badge variant="secondary">
                                    <Users className="h-3 w-3 mr-1" />
                                    {concept.user_count} users
                                  </Badge>
                                </div>
                                <div className="flex flex-wrap gap-1">
                                  {concept.users.map(user => (
                                    <Badge
                                      key={user}
                                      variant={user === selectedUser ? "default" : "outline"}
                                      className="text-xs cursor-pointer"
                                      onClick={() => setSelectedUser(user)}
                                    >
                                      @{user}
                                    </Badge>
                                  ))}
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
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