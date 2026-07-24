import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Cluster } from './clusteringTypes'

interface ClusterCardProps {
  clusterId: string
  cluster: Cluster
  isSelected: boolean
  onSelect: (clusterId: string) => void
  getClusterColor: (clusterId: string) => string
}

const ClusterCard: React.FC<ClusterCardProps> = ({
  clusterId,
  cluster,
  isSelected,
  onSelect,
  getClusterColor,
}) => {
  return (
    <Card
      className={`cursor-pointer transition-all ${
        isSelected ? 'ring-2 ring-blue-500' : ''
      }`}
      onClick={() => onSelect(clusterId)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">
            Cluster {clusterId}
          </CardTitle>
          <Badge className={getClusterColor(clusterId)}>
            {cluster.size} articles
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div>
            <p className="text-xs text-gray-500 mb-1">Representative Tags:</p>
            <div className="flex flex-wrap gap-1">
              {cluster.representative_tags.map((tag, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default ClusterCard
