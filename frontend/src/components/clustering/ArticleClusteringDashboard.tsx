import React, { useState, useEffect } from 'react'
import http from '@/services/http'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Slider } from '@/components/ui/slider'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Network,
  GitBranch,
  Layers,
  Loader2,
  AlertCircle,
  Link2,
  Sparkles
} from 'lucide-react'

import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Legend,
  CategoryScale,
  Tooltip as ChartTooltip
} from 'chart.js'

import ClusteringResults from './ClusteringResults'
import type { Article, ClusteringResult, TagCooccurrence } from './clusteringTypes'

// Register Chart.js components
ChartJS.register(
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Legend,
  CategoryScale,
  ChartTooltip
)

const getClusterColor = (clusterId: string) => {
  const colors = [
    'bg-blue-100 text-blue-700',
    'bg-green-100 text-green-700',
    'bg-purple-100 text-purple-700',
    'bg-yellow-100 text-yellow-700',
    'bg-pink-100 text-pink-700',
    'bg-indigo-100 text-indigo-700',
    'bg-red-100 text-red-700',
    'bg-orange-100 text-orange-700',
  ]
  return colors[parseInt(clusterId) % colors.length]
}

const ArticleClusteringDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('kmeans')

  // Clustering parameters
  const [nClusters, setNClusters] = useState(5)
  const [dbscanEps, setDbscanEps] = useState(0.3)
  const [dbscanMinSamples, setDbscanMinSamples] = useState(2)

  // Results
  const [clusteringResult, setClusteringResult] = useState<ClusteringResult | null>(null)
  const [cooccurrence, setCooccurrence] = useState<any>(null)
  const [summary, setSummary] = useState<any>(null)
  const [visualizationData, setVisualizationData] = useState<any>(null)
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null)
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null)
  const [similarArticles, setSimilarArticles] = useState<Article[]>([])

  useEffect(() => {
    loadSummary()
  }, [])

  const loadSummary = async () => {
    try {
      const response = await http.get(`/api/article-clustering/summary`)
      if (response.data.success) {
        setSummary(response.data.summary)
      }
    } catch (err) {
      console.error('Failed to load summary:', err)
    }
  }

  const performClustering = async (method: string) => {
    setLoading(true)
    setError(null)
    setClusteringResult(null)

    try {
      let endpoint = ''
      let params: any = {}

      switch (method) {
        case 'kmeans':
          endpoint = '/api/article-clustering/cluster/kmeans'
          params = { n_clusters: nClusters }
          break
        case 'hierarchical':
          endpoint = '/api/article-clustering/cluster/hierarchical'
          params = { n_clusters: nClusters }
          break
        case 'dbscan':
          endpoint = '/api/article-clustering/cluster/dbscan'
          params = { eps: dbscanEps, min_samples: dbscanMinSamples }
          break
      }

      const response = await http.get(`${endpoint}`, { params })

      if (response.data.success) {
        setClusteringResult(response.data.clustering_results)

        // Load visualization data
        const vizResponse = await http.get(`/api/article-clustering/visualization-data`)
        if (vizResponse.data.success) {
          setVisualizationData(vizResponse.data.visualization)
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to perform clustering')
    } finally {
      setLoading(false)
    }
  }

  const loadCooccurrence = async () => {
    setLoading(true)
    try {
      const response = await http.get(`/api/article-clustering/tag-cooccurrence`)
      if (response.data.success) {
        setCooccurrence(response.data.cooccurrence_analysis)
      }
    } catch (err) {
      console.error('Failed to load co-occurrence:', err)
    } finally {
      setLoading(false)
    }
  }

  const findSimilarArticles = async (articleId: number) => {
    try {
      const response = await http.get(`/api/article-clustering/similar/${articleId}`)
      if (response.data.success) {
        setSimilarArticles(response.data.similar_articles)
      }
    } catch (err) {
      console.error('Failed to find similar articles:', err)
    }
  }

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Article Topic Clustering</h1>
        <p className="text-gray-600">Discover topic patterns and article relationships based on tags</p>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Total Articles</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.total_articles}</div>
              <p className="text-xs text-gray-500">With tags</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Unique Tags</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.total_unique_tags}</div>
              <p className="text-xs text-gray-500">Across all articles</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Avg Tags/Article</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {summary.average_tags_per_article?.toFixed(1) || 0}
              </div>
              <p className="text-xs text-gray-500">Per article</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Top Tag</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold">
                {summary.most_common_tags?.[0]?.[0] || 'N/A'}
              </div>
              <p className="text-xs text-gray-500">
                {summary.most_common_tags?.[0]?.[1] || 0} articles
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Clustering Methods */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="kmeans">
            <Layers className="w-4 h-4 mr-2" />
            K-Means
          </TabsTrigger>
          <TabsTrigger value="hierarchical">
            <GitBranch className="w-4 h-4 mr-2" />
            Hierarchical
          </TabsTrigger>
          <TabsTrigger value="dbscan">
            <Network className="w-4 h-4 mr-2" />
            DBSCAN
          </TabsTrigger>
          <TabsTrigger value="cooccurrence">
            <Link2 className="w-4 h-4 mr-2" />
            Co-occurrence
          </TabsTrigger>
        </TabsList>

        {/* K-Means Tab */}
        <TabsContent value="kmeans" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>K-Means Clustering</CardTitle>
              <CardDescription>
                Partition articles into K distinct clusters based on tag similarity
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <label className="text-sm font-medium w-32">Number of Clusters:</label>
                <Slider
                  value={[nClusters]}
                  onValueChange={(v) => setNClusters(v[0])}
                  min={2}
                  max={10}
                  step={1}
                  className="flex-1"
                />
                <span className="w-12 text-center font-mono">{nClusters}</span>
              </div>

              <Button onClick={() => performClustering('kmeans')} disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Clustering...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Run K-Means
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Hierarchical Tab */}
        <TabsContent value="hierarchical" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Hierarchical Clustering</CardTitle>
              <CardDescription>
                Build a hierarchy of clusters from bottom-up
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <label className="text-sm font-medium w-32">Number of Clusters:</label>
                <Slider
                  value={[nClusters]}
                  onValueChange={(v) => setNClusters(v[0])}
                  min={2}
                  max={10}
                  step={1}
                  className="flex-1"
                />
                <span className="w-12 text-center font-mono">{nClusters}</span>
              </div>

              <Button onClick={() => performClustering('hierarchical')} disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Clustering...
                  </>
                ) : (
                  <>
                    <GitBranch className="w-4 h-4 mr-2" />
                    Run Hierarchical
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* DBSCAN Tab */}
        <TabsContent value="dbscan" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>DBSCAN Clustering</CardTitle>
              <CardDescription>
                Density-based clustering that can find arbitrarily shaped clusters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <label className="text-sm font-medium w-32">Epsilon (e):</label>
                <Slider
                  value={[dbscanEps]}
                  onValueChange={(v) => setDbscanEps(v[0])}
                  min={0.1}
                  max={1.0}
                  step={0.1}
                  className="flex-1"
                />
                <span className="w-12 text-center font-mono">{dbscanEps.toFixed(1)}</span>
              </div>

              <div className="flex items-center gap-4">
                <label className="text-sm font-medium w-32">Min Samples:</label>
                <Slider
                  value={[dbscanMinSamples]}
                  onValueChange={(v) => setDbscanMinSamples(v[0])}
                  min={2}
                  max={10}
                  step={1}
                  className="flex-1"
                />
                <span className="w-12 text-center font-mono">{dbscanMinSamples}</span>
              </div>

              <Button onClick={() => performClustering('dbscan')} disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Clustering...
                  </>
                ) : (
                  <>
                    <Network className="w-4 h-4 mr-2" />
                    Run DBSCAN
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Co-occurrence Tab */}
        <TabsContent value="cooccurrence" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Tag Co-occurrence Analysis</CardTitle>
              <CardDescription>
                Discover which tags frequently appear together
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={loadCooccurrence} disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Link2 className="w-4 h-4 mr-2" />
                    Analyze Co-occurrence
                  </>
                )}
              </Button>

              {cooccurrence && (
                <div className="mt-4 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-semibold mb-2">Total Tags</h4>
                      <p className="text-2xl font-bold">{cooccurrence.total_tags}</p>
                    </div>
                    <div>
                      <h4 className="font-semibold mb-2">Tag Pairs</h4>
                      <p className="text-2xl font-bold">{cooccurrence.total_pairs}</p>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold mb-2">Strongest Associations</h4>
                    <ScrollArea className="h-[300px]">
                      <div className="space-y-2">
                        {cooccurrence.strong_associations?.map((assoc: TagCooccurrence, idx: number) => (
                          <div key={idx} className="flex items-center justify-between p-2 border rounded">
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">{assoc.tag1}</Badge>
                              <Link2 className="w-4 h-4 text-gray-400" />
                              <Badge variant="outline">{assoc.tag2}</Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-600">
                                {assoc.co_occurrence_count} times
                              </span>
                              <Badge className="bg-blue-100 text-blue-700">
                                {(assoc.jaccard_similarity * 100).toFixed(0)}%
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Clustering Results */}
      {clusteringResult && (
        <ClusteringResults
          clusteringResult={clusteringResult}
          visualizationData={visualizationData}
          selectedCluster={selectedCluster}
          setSelectedCluster={setSelectedCluster}
          selectedArticle={selectedArticle}
          setSelectedArticle={setSelectedArticle}
          similarArticles={similarArticles}
          findSimilarArticles={findSimilarArticles}
          getClusterColor={getClusterColor}
        />
      )}

      {/* Error Display */}
      {error && (
        <Alert className="mt-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}

export default ArticleClusteringDashboard
