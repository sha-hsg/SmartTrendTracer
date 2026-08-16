import React from 'react'
import ReactMarkdown from 'react-markdown'
import { decodeHtmlEntities } from '@/utils/htmlDecoder'
import {
  Eye,
  Download,
  Tag as TagIcon,
  Trash2,
  Loader2,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Clock,
  Building2,
  Calendar,
  BarChart3,
  GraduationCap,
  Flag,
  FileCode,
  Edit2,
  Save,
  X as CancelIcon,
  Users,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import type { Paper } from './types'
import { StarRating, ProcessingStatus } from './PaperCardSubComponents'

export interface PaperCardProps {
  paper: Paper
  processingPapers: Set<number>
  selectedPapersForAnalysis: Set<number>
  togglePaperSelection: (paperId: number) => void
  expandedTags: Set<number>
  toggleExpandedTags: (paperId: number) => void
  expandedSummaries: Set<string>
  editingSummaries: Set<string>
  editedSummaryContent: Record<string, string>
  savingSummaries: Set<string>
  toggleSummary: (paperId: string) => void
  startEditingSummary: (paperId: string, content: string) => void
  cancelEditingSummary: (paperId: string) => void
  saveSummaryEdit: (paperId: string) => void
  setEditedSummaryContent: React.Dispatch<React.SetStateAction<Record<string, string>>>
  setExpandedSummaries: React.Dispatch<React.SetStateAction<Set<string>>>
  setSelectedPaperId: (id: number | string | null) => void
  setSelectedPaperForTags: (paper: any) => void
  setShowTagSuggestionModal: (v: boolean) => void
  setSelectedTags: (s: Set<string>) => void
  togglePaperFlag: (paperId: number, e: React.MouseEvent) => void
  handleRatePaper: (paperId: number | string, rating: number, e?: React.MouseEvent) => void
  handleDeletePaper: (paperId: number, e: React.MouseEvent) => void
  handleProcessPaper: (paperId: number, processor: 'marker' | 'mineru', e?: React.MouseEvent) => void
  formatDate: (dateString: string) => string
  getTagColor: (tag: string, index: number) => string
}

const PaperCard: React.FC<PaperCardProps> = ({
  paper,
  processingPapers,
  selectedPapersForAnalysis,
  togglePaperSelection,
  expandedTags,
  toggleExpandedTags,
  expandedSummaries,
  editingSummaries,
  editedSummaryContent,
  savingSummaries,
  toggleSummary,
  startEditingSummary,
  cancelEditingSummary,
  saveSummaryEdit,
  setEditedSummaryContent,
  setExpandedSummaries,
  setSelectedPaperId,
  setSelectedPaperForTags,
  setShowTagSuggestionModal,
  setSelectedTags,
  togglePaperFlag,
  handleRatePaper,
  handleDeletePaper,
  handleProcessPaper,
  formatDate,
  getTagColor,
}) => {
  const paperId = paper.id.toString()
  const isExpanded = expandedSummaries.has(paperId)
  const isEditing = editingSummaries.has(paperId)
  const isSaving = savingSummaries.has(paperId)

  const mollickSummary = paper.analyses?.find((a: any) =>
    a.analysis_type === 'mollick_summary' ||
    a.analysis_name === 'mollick_summary' ||
    a.type === 'mollick_summary'
  )
  const summaryContent = mollickSummary?.content || mollickSummary?.analysis_content || ''

  return (
    <Card className={cn(
      "hover:shadow-md transition-all duration-200 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-700",
      selectedPapersForAnalysis.has(paper.id) && "ring-2 ring-purple-300 border-purple-300"
    )}>
      <CardContent className="p-3">
        <div className="flex justify-between items-start gap-3">
          <div className="flex-1 min-w-0">
            {/* Title and Main Actions */}
            <div className="flex items-start gap-2 mb-2">
              <Checkbox
                checked={selectedPapersForAnalysis.has(paper.id)}
                onCheckedChange={() => togglePaperSelection(paper.id)}
                className="h-4 w-4 mt-1 flex-shrink-0"
                onClick={(e) => e.stopPropagation()}
              />
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 line-clamp-2 flex-1">
                {decodeHtmlEntities(paper.title)}
              </h3>
              <div className="flex items-center gap-1 flex-shrink-0">
                <Button
                  size="sm"
                  variant={paper.is_flagged ? "default" : "outline"}
                  className={paper.is_flagged
                    ? "bg-orange-500 hover:bg-orange-600 text-white h-7 px-2"
                    : "h-7 px-2 hover:bg-orange-50 dark:hover:bg-orange-950 hover:text-orange-600 hover:border-orange-300"}
                  onClick={(e) => togglePaperFlag(paper.id, e)}
                  title={paper.is_flagged ? "Remove flag" : "Flag this paper"}
                >
                  <Flag className="h-3 w-3" fill={paper.is_flagged ? "currentColor" : "none"} />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 px-3 text-xs"
                  onClick={() => setSelectedPaperId(paper.id)}
                >
                  <Eye className="h-3 w-3 mr-1" />
                  View
                </Button>
                {paper.pdf_path && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 w-7 p-0"
                    onClick={(e) => {
                      e.stopPropagation()
                      window.open(`/api/papers/${paper.id}/pdf`, '_blank')
                    }}
                    title="Download PDF"
                  >
                    <Download className="h-3 w-3" />
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 w-7 p-0"
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedPaperForTags(paper)
                    setShowTagSuggestionModal(true)
                  }}
                  title="Suggest tags"
                >
                  <TagIcon className="h-3 w-3" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 w-7 p-0 hover:bg-red-50 dark:hover:bg-red-950 hover:text-red-600"
                  onClick={(e) => handleDeletePaper(paper.id, e)}
                  title="Delete"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </div>

            {/* Authors */}
            {paper.authors && (
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-2 flex items-center gap-1">
                <Users className="h-3 w-3 text-gray-400 flex-shrink-0" />
                <span className="line-clamp-1">
                  {typeof paper.authors === 'string'
                    ? paper.authors
                    : Array.isArray(paper.authors)
                      ? paper.authors.map(a => typeof a === 'string' ? a : a.name).join(', ')
                      : ''}
                </span>
                {paper.authors_detailed && paper.authors_detailed.length > 0 && (() => {
                  const affiliations = paper.authors_detailed
                    .filter(author => author.affiliation)
                    .map(author => author.affiliation)
                    .filter((value, index, self) => self.indexOf(value) === index)
                  if (affiliations.length === 0) return null
                  return (
                    <>
                      <span className="text-gray-400">&#8226;</span>
                      <Building2 className="h-3 w-3 text-gray-400" />
                      <span className="line-clamp-1">{affiliations[0]}</span>
                    </>
                  )
                })()}
              </div>
            )}

            {/* Star Rating */}
            <div className="flex items-center gap-2 mb-2">
              <StarRating
                rating={paper.user_rating}
                onRate={(rating) => handleRatePaper(paper.id, rating)}
                size="sm"
              />
              {paper.user_rating && (
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {paper.user_rating}/5
                </span>
              )}
            </div>

            {/* Additional Metadata */}
            {(paper.tei_content || (paper.analyses && paper.analyses.length > 0)) && (
              <div className="flex items-center gap-2 mb-2">
                {paper.tei_content && (
                  <div className="flex items-center text-xs text-blue-600 dark:text-blue-400" title="TEI/XML available">
                    <FileCode className="h-3 w-3 mr-1" />
                    XML
                  </div>
                )}
                {paper.analyses && paper.analyses.length > 0 && (
                  <div className="flex items-center text-xs text-purple-600 dark:text-purple-400" title={`${paper.analyses.length} ${paper.analyses.length === 1 ? 'analysis' : 'analyses'} available`}>
                    <BarChart3 className="h-3 w-3 mr-1" />
                    {paper.analyses.length} {paper.analyses.length === 1 ? 'Analysis' : 'Analyses'}
                  </div>
                )}
              </div>
            )}

            {/* Processing Status */}
            <ProcessingStatus
              paper={paper}
              processingPapers={processingPapers}
              handleProcessPaper={handleProcessPaper}
            />

            {/* Abstract */}
            {paper.abstract && (
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-2 line-clamp-3">
                {paper.abstract}
              </p>
            )}

            {/* Mollick-Style Summary */}
            {mollickSummary && (
              <div className="mb-2 border-l-2 border-purple-200 dark:border-purple-900 pl-2">
                <div className="flex items-center justify-between">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setExpandedSummaries(prev => {
                        const newSet = new Set(prev)
                        if (isExpanded) newSet.delete(paperId)
                        else newSet.add(paperId)
                        return newSet
                      })
                    }}
                    className="flex items-center gap-1 text-xs font-medium text-purple-700 dark:text-purple-300 hover:text-purple-900 dark:hover:text-purple-100 transition-colors"
                  >
                    {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                    <span>Mollick-Style Summary</span>
                    <Badge variant="outline" className="h-4 px-1 text-[10px] bg-purple-50 dark:bg-purple-950 border-purple-200 dark:border-purple-900">AI</Badge>
                  </button>
                  {isExpanded && !isEditing && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-5 px-1 mr-1"
                      onClick={(e) => {
                        e.stopPropagation()
                        startEditingSummary(paperId, summaryContent)
                      }}
                      title="Edit summary"
                    >
                      <Edit2 className="h-3 w-3 text-purple-600 dark:text-purple-400" />
                    </Button>
                  )}
                </div>
                {isExpanded && (
                  <div className="mt-1 text-xs text-gray-700 dark:text-gray-300 bg-purple-50 dark:bg-purple-950 rounded p-2">
                    {isEditing ? (
                      <div className="space-y-2">
                        <Textarea
                          value={editedSummaryContent[paperId] || ''}
                          onChange={(e) => setEditedSummaryContent(prev => ({ ...prev, [paperId]: e.target.value }))}
                          className="min-h-[200px] text-xs bg-white dark:bg-gray-950"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <div className="flex gap-2 justify-end">
                          <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); cancelEditingSummary(paperId) }} disabled={isSaving} className="h-6 px-2 text-xs">
                            <CancelIcon className="h-3 w-3 mr-1" />Cancel
                          </Button>
                          <Button size="sm" onClick={(e) => { e.stopPropagation(); saveSummaryEdit(paperId) }} disabled={isSaving} className="h-6 px-2 text-xs bg-purple-600 hover:bg-purple-700 text-white">
                            {isSaving ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Save className="h-3 w-3 mr-1" />}Save
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="prose prose-sm max-w-none markdown-content">
                        <ReactMarkdown
                          components={{
                            h1: ({children}) => <h1 className="text-base font-bold mt-2 mb-1">{children}</h1>,
                            h2: ({children}) => <h2 className="text-sm font-bold mt-2 mb-1">{children}</h2>,
                            h3: ({children}) => <h3 className="text-xs font-bold mt-1 mb-1">{children}</h3>,
                            p: ({children}) => <p className="text-xs mb-1">{children}</p>,
                            ul: ({children}) => <ul className="text-xs list-disc ml-4 mb-1">{children}</ul>,
                            ol: ({children}) => <ol className="text-xs list-decimal ml-4 mb-1">{children}</ol>,
                            li: ({children}) => <li className="mb-0.5">{children}</li>,
                            strong: ({children}) => <strong className="font-semibold">{children}</strong>,
                            em: ({children}) => <em className="italic">{children}</em>,
                          }}
                        >
                          {summaryContent || 'Loading summary...'}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Compact Metrics Row */}
            <div className="flex flex-wrap items-center gap-1.5 mb-2 text-xs">
              {paper.readability?.difficulty && (
                <Badge variant="outline" className="h-5 px-1.5 text-[10px] border-purple-200 dark:border-purple-900 bg-purple-50 dark:bg-purple-950 text-purple-700 dark:text-purple-300"
                  title={`Flesch Reading Ease: ${paper.readability.flesch_reading_ease || 'N/A'}`}>
                  {paper.readability.difficulty}
                </Badge>
              )}
              {paper.readability?.academic_level && (
                <Badge variant="outline" className="h-5 px-1.5 text-[10px] border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-700 dark:text-gray-300">
                  <GraduationCap className="h-2.5 w-2.5 inline mr-0.5" />
                  {paper.readability.academic_level.replace(' Level', '')}
                </Badge>
              )}
              {paper.word_count != null && paper.word_count > 0 && (
                <span className="text-gray-500 dark:text-gray-400">{paper.word_count.toLocaleString()} words</span>
              )}
              {paper.conference && (
                <Badge variant="outline" className="h-5 px-1.5 text-[10px] border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300">
                  {paper.conference}
                </Badge>
              )}
              {(paper.publication_date || paper.year) && (
                <span className="text-gray-500 dark:text-gray-400">
                  <Calendar className="h-2.5 w-2.5 inline mr-0.5" />
                  {paper.publication_date ? formatDate(paper.publication_date) : paper.year}
                </span>
              )}
            </div>

            {/* Tags Section */}
            {((paper.tags?.length ?? 0) > 0 || (paper.concepts?.length ?? 0) > 0) && (
              <div className="flex flex-wrap items-center gap-1 mb-2">
                <TagIcon className="h-3 w-3 text-gray-400" />
                <span className="text-[10px] font-medium text-gray-500 dark:text-gray-400 mr-1">
                  {paper.tags?.length || paper.concepts?.length || 0}
                </span>
                {([...(paper.tags || []), ...(paper.concepts || [])] as Array<string | { concept_id: string; display_name: string }>)
                  .slice(0, expandedTags.has(paper.id) ? undefined : 6)
                  .map((item, index) => {
                    const tagName = typeof item === 'string' ? item : (item as { display_name: string }).display_name
                    const tagId = typeof item === 'string' ? item : (item as { concept_id: string }).concept_id
                    return (
                      <Badge
                        key={`${paper.id}-tag-${index}`}
                        variant="outline"
                        className={`h-5 px-1.5 text-[10px] cursor-pointer transition-colors hover:bg-gray-100 dark:hover:bg-gray-800 ${getTagColor(tagName, index)}`}
                        onClick={() => {
                          setSelectedTags(new Set([tagId]))
                        }}
                        title={`Filter by: ${tagName}`}
                      >
                        {tagName}
                      </Badge>
                    )
                  })}
                {((paper.tags?.length || paper.concepts?.length || 0) > 6) && !expandedTags.has(paper.id) && (
                  <Badge
                    variant="outline"
                    className="h-5 px-1.5 text-[10px] text-gray-500 dark:text-gray-400 border-dashed hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                    title={`Click to show ${((paper.tags?.length || paper.concepts?.length || 0) - 6)} more tags`}
                    onClick={(e) => { e.stopPropagation(); toggleExpandedTags(paper.id) }}
                  >
                    +{((paper.tags?.length || paper.concepts?.length || 0) - 6)}
                  </Badge>
                )}
                {expandedTags.has(paper.id) && ((paper.tags?.length || paper.concepts?.length || 0) > 6) && (
                  <button
                    className="text-[10px] text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 ml-1"
                    onClick={(e) => { e.stopPropagation(); toggleExpandedTags(paper.id) }}
                  >
                    less
                  </button>
                )}
              </div>
            )}

            {/* Added date */}
            <div className="flex items-center gap-2 text-[10px] text-gray-400">
              <Clock className="h-2.5 w-2.5" />
              <span>Added: {formatDate(paper.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Foldable AI Summary Section (separate from Mollick) */}
        {paper.ai_summary && (
          <div className="mt-4 pt-4 border-t">
            <button
              onClick={(e) => { e.stopPropagation(); toggleSummary(`ai-${paper.id}`) }}
              className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-blue-600 transition-colors w-full text-left"
            >
              <span className="text-purple-600">&#127891;</span>
              <span>AI Summary</span>
              {expandedSummaries.has(`ai-${paper.id}`) ? (
                <ChevronUp className="h-4 w-4 ml-auto" />
              ) : (
                <ChevronDown className="h-4 w-4 ml-auto" />
              )}
            </button>
            {expandedSummaries.has(`ai-${paper.id}`) && (
              <div className="mt-3 p-3 bg-purple-50 dark:bg-purple-950 rounded-lg">
                <div className="prose prose-sm max-w-none">
                  <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{paper.ai_summary}</p>
                </div>
                {paper.key_findings && (
                  <div className="mt-3 pt-3 border-t border-purple-100 dark:border-purple-900">
                    <h4 className="text-xs font-semibold text-purple-700 dark:text-purple-300 mb-2">Key Findings:</h4>
                    <ul className="list-disc list-inside text-xs text-gray-600 dark:text-gray-400 space-y-1">
                      {paper.key_findings.map((finding: string, idx: number) => (
                        <li key={idx}>{finding}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* External Links */}
        {(paper.arxiv_id || paper.doi) && (
          <div className="flex gap-4 pt-3 border-t">
            {paper.arxiv_id && (
              <a href={`https://arxiv.org/abs/${paper.arxiv_id}`} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">
                arXiv:{paper.arxiv_id}
              </a>
            )}
            {paper.doi && (
              <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">
                DOI:{paper.doi}
              </a>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default PaperCard
