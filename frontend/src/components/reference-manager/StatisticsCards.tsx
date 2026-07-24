import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface Statistics {
  total_references: number
  unique_titles: number
  references_with_doi: number
  references_with_arxiv: number
  references_in_system: number
  importable_references: number
  top_cited: Array<{
    title: string
    citation_count: number
    year: number
  }>
  citation_distribution: {
    '1_citation': number
    '2-5_citations': number
    '6-10_citations': number
    'over_10_citations': number
  }
}

export type { Statistics }

interface StatisticsCardsProps {
  statistics: Statistics
}

export function StatisticsCards({ statistics }: StatisticsCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Total References</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{statistics.total_references.toLocaleString()}</div>
          <p className="text-xs text-gray-500">{statistics.unique_titles} unique titles</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">With Identifiers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{statistics.references_with_doi}</div>
          <p className="text-xs text-gray-500">DOI available</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">In Library</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{statistics.references_in_system}</div>
          <p className="text-xs text-gray-500">Already imported</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Importable</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{statistics.importable_references}</div>
          <p className="text-xs text-gray-500">Ready to import</p>
        </CardContent>
      </Card>
    </div>
  )
}
