import {
  BookOpen,
  ChevronDown,
  ChevronRight,
  FileText,
  Users,
  Calendar,
  Link as LinkIcon,
  CheckCircle,
  GraduationCap,
  Database,
  Import,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '@/components/ui/tooltip'

export interface Reference {
  _id: string
  title: string
  authors: string[]
  year: number
  venue: string
  doi: string
  arxiv_id: string
  citation_count: number
  is_in_system: boolean
  paper_id?: string
  cited_by: string[]
  reference_hash: string
  bibtex?: string
}

export interface ReferenceWithPapers extends Reference {
  citing_papers_sample?: Array<{
    id: string
    title: string
  }>
}

interface ReferenceCardProps {
  ref_data: Reference | ReferenceWithPapers
  isExpanded: boolean
  isSelected: boolean
  onToggleExpansion: (id: string) => void
  onToggleSelection: (id: string) => void
  onShowBibtex: (ref: Reference) => void
  onImportReference: (ref: Reference) => void
  onOpenExternalSearch: (ref: Reference, service: string) => void
}

export function ReferenceCard({
  ref_data: ref,
  isExpanded,
  isSelected,
  onToggleExpansion,
  onToggleSelection,
  onShowBibtex,
  onImportReference,
  onOpenExternalSearch,
}: ReferenceCardProps) {
  return (
    <div key={ref._id} className="border rounded-lg mb-2">
      <div className="p-4">
        <div className="flex items-start gap-3">
          <Checkbox
            checked={isSelected}
            onCheckedChange={() => onToggleSelection(ref._id)}
            className="mt-1"
          />

          <button
            onClick={() => onToggleExpansion(ref._id)}
            className="mt-1 text-gray-500 hover:text-gray-700"
          >
            {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>

          <div className="flex-1">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="font-semibold text-sm mb-1">{ref.title || 'Untitled'}</h3>

                <div className="flex flex-wrap gap-2 mb-2">
                  {ref.authors && ref.authors.length > 0 && (
                    <div className="flex items-center gap-1 text-xs text-gray-600">
                      <Users className="h-3 w-3" />
                      <span>{ref.authors.slice(0, 3).join(', ')}{ref.authors.length > 3 && ' et al.'}</span>
                    </div>
                  )}

                  {ref.year && (
                    <div className="flex items-center gap-1 text-xs text-gray-600">
                      <Calendar className="h-3 w-3" />
                      <span>{ref.year}</span>
                    </div>
                  )}

                  {ref.venue && (
                    <div className="flex items-center gap-1 text-xs text-gray-600">
                      <BookOpen className="h-3 w-3" />
                      <span>{ref.venue}</span>
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap gap-2">
                  {ref.is_in_system && (
                    <Badge variant="default" className="text-xs">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      In Library
                    </Badge>
                  )}

                  {ref.doi && (
                    <Badge variant="outline" className="text-xs">
                      DOI
                    </Badge>
                  )}

                  {ref.arxiv_id && (
                    <Badge variant="outline" className="text-xs">
                      ArXiv
                    </Badge>
                  )}

                  <Badge variant="secondary" className="text-xs">
                    {ref.citation_count} citation{ref.citation_count !== 1 ? 's' : ''}
                  </Badge>
                </div>
              </div>

              <div className="flex gap-1">
                <TooltipProvider>
                  {/* External Search Links */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onOpenExternalSearch(ref, 'google-scholar')}
                      >
                        <GraduationCap className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Google Scholar</TooltipContent>
                  </Tooltip>

                  {ref.doi && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onOpenExternalSearch(ref, 'doi')}
                        >
                          <LinkIcon className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Open DOI</TooltipContent>
                    </Tooltip>
                  )}

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onOpenExternalSearch(ref, 'arxiv')}
                      >
                        <Database className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Search ArXiv</TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onShowBibtex(ref)}
                      >
                        <FileText className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>View BibTeX</TooltipContent>
                  </Tooltip>

                  {!ref.is_in_system && (ref.doi || ref.arxiv_id) && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => onImportReference(ref)}
                        >
                          <Import className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Import to Library</TooltipContent>
                    </Tooltip>
                  )}
                </TooltipProvider>
              </div>
            </div>

            {isExpanded && (
              <div className="mt-4 pt-4 border-t">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium mb-2">Details</h4>
                    <div className="space-y-1 text-xs">
                      {ref.doi && (
                        <div>
                          <span className="font-medium">DOI:</span> {ref.doi}
                        </div>
                      )}
                      {ref.arxiv_id && (
                        <div>
                          <span className="font-medium">ArXiv:</span> {ref.arxiv_id}
                        </div>
                      )}
                      <div>
                        <span className="font-medium">Reference ID:</span> {ref._id}
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium mb-2">Cited By</h4>
                    <div className="space-y-1">
                      {'citing_papers_sample' in ref && ref.citing_papers_sample ? (
                        ref.citing_papers_sample.map(paper => (
                          <div key={paper.id} className="text-xs">
                            <a
                              href={`/papers/${paper.id}`}
                              className="text-blue-600 hover:underline"
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {paper.title}
                            </a>
                          </div>
                        ))
                      ) : (
                        <div className="text-xs text-gray-500">
                          {ref.cited_by.length} paper{ref.cited_by.length !== 1 ? 's' : ''}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
