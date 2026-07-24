import { decodeHtmlEntities } from '@/utils/htmlDecoder'
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { VisuallyHidden } from "@radix-ui/react-visually-hidden"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"

import EntityAnnotationReviewModern from '../EntityAnnotationReviewModern'
import UnifiedModelSelector from '../UnifiedModelSelector'
import { useModelSelector } from '@/hooks/useModelSelector'
import {
  X,
  Download,
  Edit2,
  Save,
  Link2,
  Tags,
  Sparkles,
  User,
  Clock,
  FileText,
  Loader2,
  ExternalLink,
  BookOpen,
  Edit3,
  Calendar,
  Plus,
  Wand2,
  RefreshCw
} from 'lucide-react'

import {
  useArticleViewer,
  ArticleContentRenderer,
  ArticleSnippetsPanel,
  useArticleAnnotator,
  AnnotatorPortals,
} from './index'
import { AuthorEditor, SummaryCard } from './ArticleContent'

interface ArticleViewerProps {
  articleId: string | number
  onClose: () => void
  onArticleUpdated?: () => void
}

function ArticleViewerModern({ articleId, onClose, onArticleUpdated }: ArticleViewerProps) {
  try {

  // --- Custom hooks ---
  const viewer = useArticleViewer(articleId)
  const annotator = useArticleAnnotator()

  // Use unified model selector hook for article summarization
  const {
    selectedModel: summarizerModel,
    loading: modelLoading,
    selectModel: selectSummarizerModel
  } = useModelSelector('article_summarizer')

  // Separate picker for the metadata-extraction action.
  const {
    selectedModel: metadataModel,
    selectModel: selectMetadataModel
  } = useModelSelector('entity_extraction')

  // --- Derived state for the annotator's save operations ---
  const handleSaveHighlight = async (text: string, color: string) => {
    const ok = await viewer.saveHighlight(text, color)
    return ok
  }

  const handleSaveAnnotation = async (text: string, category: string, annotationText: string) => {
    const ok = await viewer.saveAnnotation(text, category, annotationText)
    return ok
  }

  const handleSaveTag = async (tagText: string) => {
    const result = await viewer.saveTagFromSelection(tagText)
    return result
  }

  // --- Loading state ---
  if (viewer.loading) {
    return (
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent className="max-w-6xl max-h-[90vh]">
          <VisuallyHidden>
            <DialogTitle>Loading Article</DialogTitle>
            <DialogDescription>Please wait while the article is being loaded.</DialogDescription>
          </VisuallyHidden>
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  if (!viewer.article) {
    return (
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Article Not Found</DialogTitle>
            <DialogDescription>
              The requested article could not be loaded.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={onClose}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    )
  }

  const article = viewer.article

  return (
    <>
      <Dialog open={true} onOpenChange={(open) => {
        if (!open) {
          if (annotator.isInteractingWithMenu.current) return
          if (viewer.hasChanges && onArticleUpdated) {
            onArticleUpdated()
          }
          onClose()
        }
      }}>
        <DialogContent className="max-w-6xl max-h-[90vh] p-0 overflow-hidden">
          <VisuallyHidden>
            <DialogTitle>{decodeHtmlEntities(article.title) || 'Article Viewer'}</DialogTitle>
            <DialogDescription>View and edit article content, manage tags, and generate summaries.</DialogDescription>
          </VisuallyHidden>
          <ScrollArea className="h-[90vh]">
            {/* ===== Header ===== */}
            <div className="sticky top-0 z-10 bg-background border-b">
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 pr-8">
                    {viewer.isEditingTitle ? (
                      <div className="flex items-center gap-2">
                        <Input
                          value={viewer.editedTitle}
                          onChange={(e) => viewer.setEditedTitle(e.target.value)}
                          onBlur={viewer.saveTitle}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') viewer.saveTitle()
                            if (e.key === 'Escape') {
                              viewer.setEditedTitle(article.title)
                              viewer.setIsEditingTitle(false)
                            }
                          }}
                          className="text-2xl font-bold"
                          autoFocus
                        />
                        <Button size="sm" onClick={viewer.saveTitle} disabled={viewer.savingEdits}>
                          {viewer.savingEdits ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                        </Button>
                      </div>
                    ) : (
                      <h2
                        className="text-2xl font-bold cursor-pointer hover:text-primary transition-colors flex items-center gap-2"
                        onClick={() => viewer.setIsEditingTitle(true)}
                      >
                        {decodeHtmlEntities(article.title)}
                        <Edit3 className="h-4 w-4 opacity-50" />
                      </h2>
                    )}
                    {article.subtitle && (
                      <p className="text-muted-foreground mt-1">{article.subtitle}</p>
                    )}
                  </div>
                  <Button
                    variant="ghost" size="icon"
                    onClick={() => {
                      window.dispatchEvent(new CustomEvent('articleViewerClosed', {
                        detail: { articleId: article.id }
                      }))
                      if (viewer.hasChanges && onArticleUpdated) onArticleUpdated()
                      onClose()
                    }}
                    className="rounded-full"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* ===== Metadata Row ===== */}
                <div className="flex flex-wrap items-center gap-4 mt-4 text-sm text-muted-foreground">
                  {/* Author */}
                  {viewer.isEditingAuthor ? (
                    <AuthorEditor viewer={viewer} article={article} />
                  ) : (
                    article.author ? (
                      <button
                        onClick={() => {
                          viewer.setIsEditingAuthor(true)
                          viewer.setAuthorInput(article.author?.name || '')
                          viewer.setSelectedAuthorId(article.author?.id || null)
                        }}
                        className="flex items-center gap-1 hover:text-foreground transition-colors"
                      >
                        <User className="h-4 w-4" />
                        {article.author.name}
                        <Edit3 className="h-3 w-3 ml-1 opacity-50" />
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          viewer.setIsEditingAuthor(true)
                          viewer.setAuthorInput('')
                          viewer.setSelectedAuthorId(null)
                        }}
                        className="flex items-center gap-1 hover:text-foreground transition-colors text-muted-foreground"
                      >
                        <User className="h-4 w-4" />
                        <span className="italic">Add author</span>
                        <Plus className="h-3 w-3 ml-1 opacity-50" />
                      </button>
                    )
                  )}

                  {/* Published Date */}
                  {viewer.isEditingDate ? (
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      <Input type="date" value={viewer.editedDate}
                        onChange={(e) => viewer.setEditedDate(e.target.value)} className="h-8 w-40" />
                      <Button size="sm" variant="ghost" onClick={viewer.saveEditedDate}
                        disabled={viewer.savingEdits} className="h-8 px-2">
                        <Save className="h-3 w-3" />
                      </Button>
                      <Button size="sm" variant="ghost"
                        onClick={() => {
                          viewer.setIsEditingDate(false)
                          viewer.setEditedDate(article.published_at ? article.published_at.split('T')[0] : '')
                        }} className="h-8 px-2">
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ) : (
                    <button onClick={() => viewer.setIsEditingDate(true)}
                      className="flex items-center gap-1 hover:text-foreground transition-colors">
                      <Calendar className="h-4 w-4" />
                      {article.published_at ? new Date(article.published_at).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }) : 'No date'}
                      <Edit3 className="h-3 w-3 ml-1 opacity-50" />
                    </button>
                  )}

                  {/* Extract Metadata */}
                  {(!article.author || !article.published_at) && (
                    <div className="flex items-center gap-2">
                      <div className="min-w-[180px]">
                        <UnifiedModelSelector
                          taskType="entity_extraction"
                          value={metadataModel || ''}
                          onValueChange={selectMetadataModel}
                          compact={true}
                          disabled={viewer.extractingMetadata}
                        />
                      </div>
                      <Button size="sm" variant="outline"
                        onClick={() => viewer.handleExtractMetadata(metadataModel || undefined)}
                        disabled={viewer.extractingMetadata} className="h-8 gap-1.5">
                        {viewer.extractingMetadata ? (
                          <><Loader2 className="h-3 w-3 animate-spin" />Extracting...</>
                        ) : (
                          <><Wand2 className="h-3 w-3" />
                            Extract {!article.author && !article.published_at ? 'Author & Date' : !article.author ? 'Author' : 'Date'}
                          </>
                        )}
                      </Button>
                    </div>
                  )}

                  {/* Read time / word count */}
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />{article.reading_time_minutes} min read
                  </div>
                  <div className="flex items-center gap-1">
                    <FileText className="h-4 w-4" />{article.word_count} words
                  </div>

                  {/* URL editing */}
                  {viewer.isEditingUrl ? (
                    <div className="flex items-center gap-2 w-full max-w-2xl">
                      <Input type="url" value={viewer.editedUrl}
                        onChange={(e) => viewer.setEditedUrl(e.target.value)}
                        onBlur={viewer.saveUrl}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') viewer.saveUrl()
                          if (e.key === 'Escape') { viewer.setIsEditingUrl(false); viewer.setEditedUrl(article.url || '') }
                        }}
                        placeholder="Enter article URL" className="h-8 w-full" autoFocus />
                      <Button size="sm" onClick={viewer.saveUrl} className="h-8">Save</Button>
                      <Button size="sm" variant="outline"
                        onClick={() => { viewer.setIsEditingUrl(false); viewer.setEditedUrl(article.url || '') }}
                        className="h-8">Cancel</Button>
                    </div>
                  ) : (
                    <>
                      {article.url && (
                        <a href={article.url} target="_blank" rel="noopener noreferrer"
                          className="flex items-center gap-1 text-primary hover:underline">
                          <ExternalLink className="h-4 w-4" />View on Substack
                        </a>
                      )}
                      <Button variant="ghost" size="sm"
                        onClick={() => { viewer.setEditedUrl(article.url || ''); viewer.setIsEditingUrl(true) }}
                        className="h-8 px-2">
                        <Link2 className="h-4 w-4 mr-1" />{article.url ? 'Edit' : 'Add'} URL
                      </Button>
                    </>
                  )}
                </div>

                {/* AI Model Selection for Summarization */}
                {!article.summary && (
                  <div className="mt-4 p-4 border rounded-lg bg-muted/30">
                    <UnifiedModelSelector
                      taskType="article_summarizer"
                      value={summarizerModel || ''}
                      onValueChange={selectSummarizerModel}
                      label="Summarization Model"
                      description="Choose the AI model for generating article summaries"
                      disabled={modelLoading || viewer.generatingSummary}
                      compact={false}
                    />
                  </div>
                )}

                {/* ===== Action Buttons ===== */}
                <div className="flex flex-wrap gap-2 mt-4">
                  <Button variant="outline" size="sm" onClick={() => viewer.setShowEntityAnnotation(true)}
                    className="bg-gradient-to-r from-purple-500/10 to-purple-600/10 hover:from-purple-500/20 hover:to-purple-600/20">
                    <Sparkles className="h-4 w-4 mr-2" />Edit Annotation Review
                  </Button>

                  <Button variant="outline" size="sm"
                    onClick={() => {
                      if (article.summary) { viewer.setShowSummary(!viewer.showSummary) }
                      else { viewer.generateSummary(summarizerModel || undefined) }
                    }}
                    disabled={viewer.generatingSummary || !summarizerModel}>
                    {viewer.generatingSummary ? (
                      <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Generating...</>
                    ) : article.summary ? (
                      <><BookOpen className="h-4 w-4 mr-2" />{viewer.showSummary ? 'Hide' : 'View'} Summary</>
                    ) : (
                      <><Sparkles className="h-4 w-4 mr-2" />Generate Summary</>
                    )}
                  </Button>

                  {article.summary && (
                    <Button variant="outline" size="sm" onClick={() => viewer.generateSummary(summarizerModel || undefined)}
                      disabled={viewer.generatingSummary || !summarizerModel} title="Regenerate summary with current model">
                      {viewer.generatingSummary ? (
                        <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Regenerating...</>
                      ) : (
                        <><RefreshCw className="h-4 w-4 mr-2" />Redo Summary</>
                      )}
                    </Button>
                  )}

                  <Button variant="outline" size="sm" onClick={viewer.recollectArticle}
                    disabled={viewer.recollecting || !article.url} title="Re-fetch article content from URL">
                    {viewer.recollecting ? (
                      <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Recollecting...</>
                    ) : (
                      <><RefreshCw className="h-4 w-4 mr-2" />Recollect</>
                    )}
                  </Button>

                  <Button variant="outline" size="sm" onClick={() => viewer.setIsEditingContent(!viewer.isEditingContent)}>
                    <Edit2 className="h-4 w-4 mr-2" />{viewer.isEditingContent ? 'View' : 'Edit'} Content
                  </Button>

                  <Button variant="outline" size="sm" onClick={viewer.beautifyMarkdown}
                    disabled={viewer.beautifyingMarkdown} title="Beautify and format the markdown content">
                    {viewer.beautifyingMarkdown ? (
                      <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Beautifying...</>
                    ) : (
                      <><Wand2 className="h-4 w-4 mr-2" />Beautify Markdown</>
                    )}
                  </Button>

                  <Button variant="outline" size="sm" onClick={viewer.exportToPDF} disabled={viewer.exportingPDF}>
                    {viewer.exportingPDF ? (
                      <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Exporting...</>
                    ) : (
                      <><Download className="h-4 w-4 mr-2" />Export PDF</>
                    )}
                  </Button>

                  <Button variant="outline" size="sm" onClick={viewer.exportToMarkdown}>
                    <FileText className="h-4 w-4 mr-2" />Export Markdown
                  </Button>
                </div>
              </div>

              {/* Summary Error Message */}
              {viewer.summaryError && (
                <div className="px-6 pb-4">
                  <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <svg className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div className="flex-1">
                      <p className="text-sm text-red-800 font-medium">Summary Generation Failed</p>
                      <p className="text-sm text-red-700 mt-1">{viewer.summaryError}</p>
                    </div>
                    <button onClick={() => viewer.setSummaryError('')} className="text-red-600 hover:text-red-800" title="Dismiss">
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}

              {/* Tags */}
              {article.tags && article.tags.length > 0 && (
                <div className="px-6 pb-4">
                  <div className="flex flex-wrap gap-2">
                    {article.tags.map(tag => (
                      <Badge key={tag.id} variant="outline"
                        className="cursor-pointer bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 hover:text-blue-800 group">
                        <Tags className="h-3 w-3 mr-1" />{tag.tag}
                        <button onClick={() => viewer.removeTag(tag.id, tag.tag)}
                          className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity hover:text-blue-900">
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* ===== Content Area ===== */}
            <div className="p-6">
              {/* Summary */}
              {viewer.showSummary && article.summary && (
                <SummaryCard
                  article={article}
                  summaryModel={viewer.summaryModel}
                  keyPoints={viewer.keyPoints}
                  selectedSummaryText={annotator.selectedSummaryText}
                  setSelectedSummaryText={annotator.setSelectedSummaryText}
                  onAddConcept={async (text) => {
                    const ok = await viewer.addConceptFromSummary(text)
                    if (ok) {
                      annotator.setSelectedSummaryText('')
                      window.getSelection()?.removeAllRanges()
                    }
                  }}
                />
              )}

              {/* Snippets */}
              <ArticleSnippetsPanel
                snippets={article.snippets}
                onDeleteSnippet={viewer.deleteSnippet}
              />

              {/* Article Content */}
              <ArticleContentRenderer
                article={article}
                isEditing={viewer.isEditingContent}
                editedContent={viewer.editedContent}
                savingEdits={viewer.savingEdits}
                onEditedContentChange={viewer.setEditedContent}
                onSave={viewer.saveContent}
                onCancel={() => {
                  viewer.setEditedContent(article.content_markdown)
                  viewer.setIsEditingContent(false)
                }}
                onContextMenu={annotator.handleContextMenu}
                lastSelectionRef={annotator.lastSelectionRef}
              />
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* ===== Annotation Portals (context menu, highlight, snippet, tag forms) ===== */}
      <AnnotatorPortals
        showContextMenu={annotator.showContextMenu}
        showHighlightForm={annotator.showHighlightForm}
        showAnnotationForm={annotator.showAnnotationForm}
        showTagCreation={annotator.showTagCreation}
        selectionCoords={annotator.selectionCoords}
        selectedText={annotator.selectedText}
        selectedTextRef={annotator.selectedTextRef}
        tagEditText={annotator.tagEditText}
        tagError={annotator.tagError}
        highlightColor={annotator.highlightColor}
        annotation={annotator.annotation}
        snippetCategory={annotator.snippetCategory}
        isInteractingWithMenu={annotator.isInteractingWithMenu}
        onSetShowContextMenu={annotator.setShowContextMenu}
        onSetShowHighlightForm={annotator.setShowHighlightForm}
        onSetShowAnnotationForm={annotator.setShowAnnotationForm}
        onSetShowTagCreation={annotator.setShowTagCreation}
        onSetTagEditText={annotator.setTagEditText}
        onSetTagError={annotator.setTagError}
        onSetHighlightColor={annotator.setHighlightColor}
        onSetAnnotation={annotator.setAnnotation}
        onSetSnippetCategory={annotator.setSnippetCategory}
        onCancelSelection={annotator.cancelSelection}
        onSaveHighlight={handleSaveHighlight}
        onSaveAnnotation={handleSaveAnnotation}
        onSaveTag={handleSaveTag}
      />

      {/* Entity Annotation Review Dialog */}
      {viewer.showEntityAnnotation && (
        <Dialog open={viewer.showEntityAnnotation} onOpenChange={viewer.setShowEntityAnnotation}>
          <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
            <VisuallyHidden>
              <DialogTitle>Entity Annotation Review</DialogTitle>
              <DialogDescription>Review and manage entity annotations for this article</DialogDescription>
            </VisuallyHidden>
            <EntityAnnotationReviewModern
              articleId={article.id}
              onComplete={() => {
                viewer.setShowEntityAnnotation(false)
                viewer.fetchArticle()
                viewer.setHasChanges(true)
              }}
            />
          </DialogContent>
        </Dialog>
      )}
    </>
  )
  } catch (error) {
    console.error('ArticleViewerModern encountered an error:', error)
    console.error('Stack:', (error as Error).stack)
    return (
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Error</DialogTitle>
            <DialogDescription>
              An error occurred while rendering the article viewer. Please try again.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={onClose}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    )
  }
}

export default ArticleViewerModern
