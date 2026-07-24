import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Scatter } from 'react-chartjs-2'
import ClusterCard from './ClusterCard'
import type { Article, ClusteringResult, VisualizationPoint } from './clusteringTypes'

interface ClusteringResultsProps {
  clusteringResult: ClusteringResult
  visualizationData: any
  selectedCluster: string | null
  setSelectedCluster: (clusterId: string | null) => void
  selectedArticle: Article | null
  setSelectedArticle: (article: Article | null) => void
  similarArticles: Article[]
  findSimilarArticles: (articleId: number) => void
  getClusterColor: (clusterId: string) => string
}

const ClusteringResults: React.FC<ClusteringResultsProps> = ({
  clusteringResult,
  visualizationData,
  selectedCluster,
  setSelectedCluster,
  selectedArticle,
  setSelectedArticle,
  similarArticles,
  findSimilarArticles,
  getClusterColor,
}) => {
  const renderScatterPlot = () => {
    if (!visualizationData || !clusteringResult) return null

    const datasets = Object.entries(clusteringResult.clusters).map(([clusterId, cluster]) => {
      const clusterPoints = visualizationData.points.filter((p: VisualizationPoint) =>
        cluster.articles.some(a => a.id === p.id)
      )

      const colorMap: Record<string, string> = {
        '0': 'rgb(59, 130, 246)',
        '1': 'rgb(34, 197, 94)',
        '2': 'rgb(168, 85, 247)',
        '3': 'rgb(250, 204, 21)',
        '4': 'rgb(236, 72, 153)',
        '5': 'rgb(99, 102, 241)',
        '6': 'rgb(239, 68, 68)',
        '7': 'rgb(251, 146, 60)',
      }

      return {
        label: `Cluster ${clusterId}`,
        data: clusterPoints.map((p: VisualizationPoint) => ({ x: p.x, y: p.y })),
        backgroundColor: colorMap[clusterId] || 'rgb(156, 163, 175)',
        pointRadius: 6,
        pointHoverRadius: 8,
      }
    })

    const chartData = {
      datasets
    }

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right' as const,
        },
        title: {
          display: true,
          text: `Article Clusters Visualization (${visualizationData.method.toUpperCase()})`,
        },
        tooltip: {
          callbacks: {
            label: (context: any) => {
              const point = visualizationData.points.find((p: VisualizationPoint) =>
                Math.abs(p.x - context.parsed.x) < 0.01 && Math.abs(p.y - context.parsed.y) < 0.01
              )
              if (point) {
                return [
                  point.title.substring(0, 50) + '...',
                  `Tags: ${point.tags.slice(0, 3).join(', ')}`
                ]
              }
              return context.dataset.label
            }
          }
        }
      },
      scales: {
        x: {
          type: 'linear' as const,
          position: 'bottom' as const,
          title: {
            display: true,
            text: visualizationData.method === 'pca' ? 'PC1' : 'Dimension 1'
          }
        },
        y: {
          title: {
            display: true,
            text: visualizationData.method === 'pca' ? 'PC2' : 'Dimension 2'
          }
        }
      }
    }

    return (
      <div className="h-[500px]">
        <Scatter data={chartData} options={options} />
      </div>
    )
  }

  return (
    <div className="mt-6 space-y-6">
      {/* Visualization */}
      {visualizationData && (
        <Card>
          <CardHeader>
            <CardTitle>Cluster Visualization</CardTitle>
            <CardDescription>
              2D projection of articles showing cluster assignments
            </CardDescription>
          </CardHeader>
          <CardContent>
            {renderScatterPlot()}
          </CardContent>
        </Card>
      )}

      {/* Cluster Details */}
      <Card>
        <CardHeader>
          <CardTitle>Cluster Details</CardTitle>
          <CardDescription>
            {clusteringResult.n_clusters} clusters found using {clusteringResult.method}
            {clusteringResult.silhouette_score && (
              <span className="ml-2">
                (Silhouette Score: {clusteringResult.silhouette_score.toFixed(3)})
              </span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(clusteringResult.clusters).map(([clusterId, cluster]) => (
              <ClusterCard
                key={clusterId}
                clusterId={clusterId}
                cluster={cluster}
                isSelected={selectedCluster === clusterId}
                onSelect={setSelectedCluster}
                getClusterColor={getClusterColor}
              />
            ))}
          </div>

          {/* Noise Articles (for DBSCAN) */}
          {clusteringResult.noise_articles && clusteringResult.noise_articles.length > 0 && (
            <div className="mt-4">
              <h3 className="font-semibold mb-2">
                Unclustered Articles ({clusteringResult.noise_articles.length})
              </h3>
              <ScrollArea className="h-[200px]">
                <div className="space-y-2">
                  {clusteringResult.noise_articles.map((article) => (
                    <div key={article.id} className="p-2 border rounded">
                      <p className="font-medium text-sm">{article.title}</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {article.tags.map((tag, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Selected Cluster Articles */}
      {selectedCluster && clusteringResult.clusters[selectedCluster] && (
        <Card>
          <CardHeader>
            <CardTitle>
              Articles in Cluster {selectedCluster}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {clusteringResult.clusters[selectedCluster].articles.map((article) => (
                  <Card
                    key={article.id}
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => {
                      setSelectedArticle(article)
                      findSimilarArticles(article.id)
                    }}
                  >
                    <CardContent className="pt-4">
                      <h4 className="font-semibold text-sm mb-1">{article.title}</h4>
                      <p className="text-xs text-gray-600 mb-2">By {article.author}</p>
                      {article.summary && (
                        <p className="text-xs text-gray-500 mb-2">
                          {article.summary}...
                        </p>
                      )}
                      <div className="flex flex-wrap gap-1">
                        {article.tags.map((tag, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Similar Articles */}
      {selectedArticle && similarArticles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Similar Articles</CardTitle>
            <CardDescription>
              Articles similar to: {selectedArticle.title}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {similarArticles.map((article) => (
                <div key={article.id} className="flex items-start justify-between p-3 border rounded">
                  <div className="flex-1">
                    <h4 className="font-medium text-sm">{article.title}</h4>
                    <p className="text-xs text-gray-600">By {article.author}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {article.tags.map((tag, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <Badge className="bg-green-100 text-green-700">
                    {((article.similarity_score || 0) * 100).toFixed(0)}% match
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default ClusteringResults
