import {
  Brain,
  AlertTriangle,
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { AnalysisCard } from './AnalysisCard'
import { AnalysisGenerationControls } from './AnalysisGenerationControls'
import { FreeAnalysisTab } from './FreeAnalysisTab'
import { AnalysisContextMenu, TagCreationDialog } from './AnalysisContextMenu'
import { usePaperAnalysis } from './usePaperAnalysis'


interface PaperAnalysisPanelProps {
  paperId: string | number
  paperTitle?: string
  hasContent?: boolean
  onTagCreate?: (tag: string) => void
  onSnippetCreate?: (text: string) => void
}


// Model selection - managed by ModelSelector component with localStorage persistence
import { useState } from 'react'

export default function PaperAnalysisPanel({ paperId, paperTitle, hasContent = true, onTagCreate, onSnippetCreate }: PaperAnalysisPanelProps) {
  const [selectedModel, setSelectedModel] = useState<string>('')

  const analysis = usePaperAnalysis({
    paperId,
    paperTitle,
    hasContent,
    selectedModel,
    onTagCreate,
    onSnippetCreate,
  })

  return (
    <Card className="w-full">
      {!hasContent && (
        <div className="mx-6 mt-6 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-amber-800">
            No extracted content available. Process the PDF with Marker or MinerU first to enable AI analyses.
          </p>
        </div>
      )}
      <CardHeader>
        <div className="flex items-center justify-between mb-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Paper Analyses
            </CardTitle>
            <CardDescription className="mt-1">
              Generate various types of summaries and analyses
            </CardDescription>
          </div>
          <AnalysisGenerationControls
            paperId={paperId}
            hasContent={hasContent}
            selectedCategory={analysis.selectedCategory}
            availableAnalyses={analysis.availableAnalyses}
            generatedAnalyses={analysis.generatedAnalyses}
            loadingAnalyses={analysis.loadingAnalyses}
            expandedAnalyses={analysis.expandedAnalyses}
            expandedFreeAnalyses={analysis.expandedFreeAnalyses}
            batchProgress={analysis.batchProgress}
            selectedModel={selectedModel}
            onSetSelectedModel={setSelectedModel}
            onSetExpandedAnalyses={analysis.setExpandedAnalyses}
            onSetExpandedFreeAnalyses={analysis.setExpandedFreeAnalyses}
            onSetGeneratedAnalyses={analysis.setGeneratedAnalyses}
            onGenerateAllAnalyses={analysis.generateAllAnalyses}
            onGenerateMultipleAnalyses={analysis.generateMultipleAnalyses}
            onExportAllAnalysesAsMarkdown={analysis.exportAllAnalysesAsMarkdown}
          />
        </div>
      </CardHeader>

      <CardContent>
        {/* Category Tabs */}
        <Tabs value={analysis.selectedCategory} onValueChange={analysis.setSelectedCategory} className="w-full">
          <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${Object.keys(analysis.availableAnalyses).length + 2}, 1fr)` }}>
            <TabsTrigger value="all">All</TabsTrigger>
            {Object.keys(analysis.availableAnalyses).map(category => (
              <TabsTrigger key={category} value={category} className="capitalize">
                {category}
              </TabsTrigger>
            ))}
            <TabsTrigger value="free" className="font-semibold text-purple-600">
              Free 🚀
            </TabsTrigger>
          </TabsList>

          {/* All Tab */}
          <TabsContent value="all" className="mt-4">
            <ScrollArea className="h-[600px] pr-4">
              <div className="space-y-3">
                {analysis.getAllAnalyses().map(a => (
                  <AnalysisCard
                    key={a.id}
                    analysis={a}
                    isLoading={analysis.loadingAnalyses.has(a.id)}
                    isGenerated={!!analysis.generatedAnalyses[a.id]}
                    isExpanded={analysis.expandedAnalyses.has(a.id)}
                    result={analysis.generatedAnalyses[a.id]}
                    hasContent={hasContent}
                    editingAnalysis={analysis.editingAnalysis}
                    editedContent={analysis.editedContent}
                    copiedAnalysis={analysis.copiedAnalysis}
                    onToggleExpansion={analysis.toggleAnalysisExpansion}
                    onStartEditing={analysis.startEditingAnalysis}
                    onSaveEditing={analysis.saveEditedAnalysis}
                    onCancelEditing={analysis.cancelEditingAnalysis}
                    onSetEditedContent={analysis.setEditedContent}
                    onCopy={analysis.copyAnalysis}
                    onDownload={analysis.downloadAnalysis}
                    onGenerate={analysis.generateAnalysis}
                    onContextMenu={analysis.handleContextMenu}
                  />
                ))}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Category-specific Tabs */}
          {Object.keys(analysis.availableAnalyses).map(category => (
            <TabsContent key={category} value={category} className="mt-4">
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-3">
                  {(analysis.availableAnalyses[category] || []).map(a => (
                    <AnalysisCard
                      key={a.id}
                      analysis={a}
                      isLoading={analysis.loadingAnalyses.has(a.id)}
                      isGenerated={!!analysis.generatedAnalyses[a.id]}
                      isExpanded={analysis.expandedAnalyses.has(a.id)}
                      result={analysis.generatedAnalyses[a.id]}
                      hasContent={hasContent}
                      editingAnalysis={analysis.editingAnalysis}
                      editedContent={analysis.editedContent}
                      copiedAnalysis={analysis.copiedAnalysis}
                      onToggleExpansion={analysis.toggleAnalysisExpansion}
                      onStartEditing={analysis.startEditingAnalysis}
                      onSaveEditing={analysis.saveEditedAnalysis}
                      onCancelEditing={analysis.cancelEditingAnalysis}
                      onSetEditedContent={analysis.setEditedContent}
                      onCopy={analysis.copyAnalysis}
                      onDownload={analysis.downloadAnalysis}
                      onGenerate={analysis.generateAnalysis}
                      onContextMenu={analysis.handleContextMenu}
                    />
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>
          ))}

          {/* Free Tab Content */}
          <TabsContent value="free" className="mt-2">
            <FreeAnalysisTab
              freeAnalyses={analysis.freeAnalyses}
              currentPrompt={analysis.currentPrompt}
              loadingFreeAnalysis={analysis.loadingFreeAnalysis}
              expandedFreeAnalyses={analysis.expandedFreeAnalyses}
              editingFreeAnalysis={analysis.editingFreeAnalysis}
              editedFreeContent={analysis.editedFreeContent}
              onSetCurrentPrompt={analysis.setCurrentPrompt}
              onSetExpandedFreeAnalyses={analysis.setExpandedFreeAnalyses}
              onSetEditingFreeAnalysis={analysis.setEditingFreeAnalysis}
              onSetEditedFreeContent={analysis.setEditedFreeContent}
              onSubmitFreeAnalysis={analysis.submitFreeAnalysis}
              onDeleteFreeAnalysis={analysis.deleteFreeAnalysis}
              onSaveFreeAnalysisEdit={analysis.saveFreeAnalysisEdit}
            />
          </TabsContent>
        </Tabs>

      </CardContent>

      {/* Context Menu Portal */}
      <AnalysisContextMenu
        showContextMenu={analysis.showContextMenu}
        contextMenuPosition={analysis.contextMenuPosition}
        onMenuAction={analysis.handleMenuAction}
      />

      {/* Tag Creation Dialog */}
      <TagCreationDialog
        open={analysis.showTagDialog}
        tagText={analysis.tagText}
        creatingTag={analysis.creatingTag}
        onTagTextChange={analysis.setTagText}
        onCreateTag={analysis.handleCreateTag}
        onClose={analysis.handleTagDialogClose}
      />
    </Card>
  )
}
