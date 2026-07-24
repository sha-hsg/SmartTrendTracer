import React, { Suspense } from "react";
import {
  FileText,
  BookOpen,
  ExternalLink,
  Download,
  Search,
  FileCode,
  MessageSquare,
  Hash,
  Brain,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const PDFViewerModern = React.lazy(() => import("../PDFViewerModern"));

import { ProcessingStatusIndicator } from "../ProcessingStatusIndicator";
import PaperAnalysisPanel from "../paper-analysis";
import TEIViewer from "../TEIViewer";
import PaperReferences from "../PaperReferences";
import GROBIDMetadataPanel from "../GROBIDMetadataPanel";
import BibTeXViewer from "../BibTeXViewer";

import PaperContentViewer from "./PaperContentViewer";
import PaperSectionsTab from "./PaperSectionsTab";
import PaperSnippetsTab from "./PaperSnippetsTab";
import PaperSearchTab, { SearchMatch } from "./PaperSearchTab";
import { Paper, PaperSection } from "./types";

interface PaperTabsContentProps {
  paper: Paper;
  paperId: string | number;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pdfAvailable: boolean;
  setPdfAvailable: React.Dispatch<React.SetStateAction<boolean>>;
  isEditingMarkdown: boolean;
  setIsEditingMarkdown: React.Dispatch<React.SetStateAction<boolean>>;
  editedMarkdown: string;
  setEditedMarkdown: React.Dispatch<React.SetStateAction<string>>;
  savingMarkdown: boolean;
  handleSaveMarkdown: () => Promise<void>;
  isAnyProcessing: boolean;
  setIsProcessing: React.Dispatch<React.SetStateAction<boolean>>;
  setProcessingStartTime: React.Dispatch<React.SetStateAction<Date | null>>;
  copiedText: string | null;
  handleCopyText: (text: string) => void;
  handleMarkdownContextMenu: (e: React.MouseEvent) => void;
  markdownContainerRef: React.RefObject<HTMLDivElement>;
  expandedSections: Set<number>;
  editingSectionId: number | null;
  editedSectionContent: string;
  setEditedSectionContent: React.Dispatch<React.SetStateAction<string>>;
  editingSectionTitleId: number | null;
  editedSectionTitle: string;
  setEditedSectionTitle: React.Dispatch<React.SetStateAction<string>>;
  savingSection: boolean;
  extractingSections: boolean;
  toggleSection: (sectionId: number) => void;
  handleEditSection: (section: PaperSection) => void;
  handleEditSectionTitle: (section: PaperSection) => void;
  handleSaveSectionTitle: (sectionId: number) => Promise<void>;
  handleCancelSectionTitleEdit: () => void;
  handleSaveSection: (sectionId: number) => Promise<void>;
  handleCancelSectionEdit: () => void;
  handleExtractSections: () => Promise<void>;
  selectedText: string;
  setSelectedText: React.Dispatch<React.SetStateAction<string>>;
  snippetAnnotation: string;
  setSnippetAnnotation: React.Dispatch<React.SetStateAction<string>>;
  snippetCategory: string;
  setSnippetCategory: React.Dispatch<React.SetStateAction<string>>;
  creatingSnippet: boolean;
  handleCreateSnippet: () => Promise<void>;
  handleCreateTagFromPDF: (tagText: string) => Promise<void>;
  loadPaperDetails: () => void;
}

const PaperTabsContent: React.FC<PaperTabsContentProps> = ({
  paper,
  paperId,
  activeTab,
  setActiveTab,
  pdfAvailable,
  setPdfAvailable,
  isEditingMarkdown,
  setIsEditingMarkdown,
  editedMarkdown,
  setEditedMarkdown,
  savingMarkdown,
  handleSaveMarkdown,
  isAnyProcessing,
  setIsProcessing,
  setProcessingStartTime,
  copiedText,
  handleCopyText,
  handleMarkdownContextMenu,
  markdownContainerRef,
  expandedSections,
  editingSectionId,
  editedSectionContent,
  setEditedSectionContent,
  editingSectionTitleId,
  editedSectionTitle,
  setEditedSectionTitle,
  savingSection,
  extractingSections,
  toggleSection,
  handleEditSection,
  handleEditSectionTitle,
  handleSaveSectionTitle,
  handleCancelSectionTitleEdit,
  handleSaveSection,
  handleCancelSectionEdit,
  handleExtractSections,
  selectedText,
  setSelectedText,
  snippetAnnotation,
  setSnippetAnnotation,
  snippetCategory,
  setSnippetCategory,
  creatingSnippet,
  handleCreateSnippet,
  handleCreateTagFromPDF,
  loadPaperDetails,
}) => {
  // Jump from a search result to the corresponding text in the Content tab.
  // Walks the rendered markdown DOM and scrolls to the n-th occurrence of the
  // query. In Large Document Mode, chunks that are not yet lazy-loaded cannot
  // be scrolled to — in that case only the tab switch happens (result list
  // remains available in the Search tab).
  const handleNavigateToMatch = (match: SearchMatch, query: string) => {
    setActiveTab("markdown");
    setTimeout(() => {
      const container = markdownContainerRef.current;
      if (!container) return;

      const needle = query.toLowerCase();
      const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
      const occurrences: { node: Text; offset: number }[] = [];
      let node: Node | null;
      while ((node = walker.nextNode())) {
        const text = (node.textContent || "").toLowerCase();
        let idx = text.indexOf(needle);
        while (idx !== -1) {
          occurrences.push({ node: node as Text, offset: idx });
          idx = text.indexOf(needle, idx + needle.length);
        }
      }
      if (occurrences.length === 0) return;

      // Rendered occurrence count can differ slightly from the raw markdown
      // (syntax characters are stripped) — clamp to the available range.
      const target = occurrences[Math.min(match.index, occurrences.length - 1)];
      target.node.parentElement?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });

      // Highlight the match via text selection
      try {
        const range = document.createRange();
        range.setStart(target.node, target.offset);
        range.setEnd(
          target.node,
          Math.min(target.offset + query.length, target.node.length)
        );
        const selection = window.getSelection();
        selection?.removeAllRanges();
        selection?.addRange(range);
      } catch {
        // Selection is best-effort only
      }
    }, 300);
  };

  return (
    <Tabs
      value={activeTab}
      onValueChange={setActiveTab}
      className="flex-1 flex flex-col"
    >
      {/* Tab Navigation */}
      <div className="mx-4 mt-2 space-y-2">
        {/* Primary Tabs - Core Content */}
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="pdf" className="flex items-center gap-2">
            <FileText className="h-3 w-3" />
            PDF
          </TabsTrigger>
          <TabsTrigger value="markdown" className="flex items-center gap-2">
            <FileCode className="h-3 w-3" />
            Content
            {paper.processor_used &&
              paper.processor_used !== "pypdfium2" && (
                <div
                  className="w-1 h-1 rounded-full bg-green-500"
                  title="Enhanced processing"
                />
              )}
          </TabsTrigger>
          <TabsTrigger value="sections" className="flex items-center gap-2">
            <Hash className="h-3 w-3" />
            Sections
          </TabsTrigger>
          <TabsTrigger value="snippets" className="flex items-center gap-2">
            <MessageSquare className="h-3 w-3" />
            Notes
            {paper.snippets && paper.snippets.length > 0 && (
              <Badge variant="secondary" className="h-4 px-1 text-xs">
                {paper.snippets.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Secondary Tabs - Analysis & Tools */}
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="analyses" className="flex items-center gap-2">
            <Brain className="h-3 w-3" />
            Analysis
          </TabsTrigger>
          <TabsTrigger value="search" className="flex items-center gap-2">
            <Search className="h-3 w-3" />
            Search
          </TabsTrigger>
          <TabsTrigger value="references" className="flex items-center gap-2">
            <ExternalLink className="h-3 w-3" />
            References
          </TabsTrigger>
          <TabsTrigger value="grobid" className="flex items-center gap-2">
            <Search className="h-3 w-3" />
            Metadata
            {paper.metadata?.grobid_processed && (
              <div
                className="w-1 h-1 rounded-full bg-green-500"
                title="GROBID processed"
              />
            )}
          </TabsTrigger>
          <TabsTrigger value="tei" className="flex items-center gap-2">
            <FileCode className="h-3 w-3" />
            XML
          </TabsTrigger>
          <TabsTrigger value="bibtex" className="flex items-center gap-2">
            <BookOpen className="h-3 w-3" />
            BibTeX
          </TabsTrigger>
        </TabsList>

        {/* Tertiary Tabs - Additional Resources */}
        {paper.metadata?.supplementary && paper.metadata.supplementary.length > 0 && (
          <TabsList className="grid w-full grid-cols-1">
            <TabsTrigger value="supplementary" className="flex items-center gap-2">
              <Download className="h-3 w-3" />
              Supplementary Material
              <Badge variant="secondary" className="h-4 px-1 text-xs">
                {paper.metadata.supplementary.length}
              </Badge>
            </TabsTrigger>
          </TabsList>
        )}
      </div>

      {/* PDF Tab */}
      <TabsContent value="pdf" className="flex-1 p-4">
        {pdfAvailable ? (
          <div className="h-full bg-white rounded-lg border overflow-hidden">
            <Suspense fallback={
              <div className="flex items-center justify-center h-full">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                <span className="ml-2 text-gray-600">Loading PDF Viewer...</span>
              </div>
            }>
              <PDFViewerModern
                pdfUrl={`/api/papers/${paperId}/pdf`}
                paperId={paperId}
                onTextSelect={(text, _pageNumber) => {
                  setSelectedText(text);
                  const toast = document.createElement("div");
                  toast.textContent =
                    "Text selected - switch to Notes tab to create snippet";
                  toast.className =
                    "fixed top-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm z-50 shadow-lg";
                  document.body.appendChild(toast);
                  setTimeout(() => {
                    document.body.removeChild(toast);
                  }, 3000);
                }}
                onTagCreate={handleCreateTagFromPDF}
                className="h-full"
              />
            </Suspense>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full bg-white rounded-lg border">
            <div className="text-center max-w-md">
              <div className="mb-4">
                {!paper.processed ? (
                  <Loader2 className="h-12 w-12 text-blue-500 mx-auto mb-4 animate-spin" />
                ) : (
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                )}
              </div>
              <h3 className="text-lg font-medium text-gray-700 mb-2">
                {!paper.processed
                  ? "Processing PDF..."
                  : "PDF Not Available"}
              </h3>
              <p className="text-sm text-gray-500 mb-4">
                {!paper.processed
                  ? "The PDF is being processed to extract text and structure. This may take a few minutes."
                  : "The PDF file may not have been uploaded or may be corrupted. Try re-importing the paper."}
              </p>
              {!paper.processed && (
                <div className="flex justify-center">
                  <ProcessingStatusIndicator
                    paperId={paperId}
                    compact={false}
                    onComplete={() => {
                      setPdfAvailable(true);
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </TabsContent>

      {/* Content/Markdown Tab */}
      <TabsContent value="markdown" className="flex-1 p-4">
        <PaperContentViewer
          paper={paper}
          paperId={paperId}
          isEditingMarkdown={isEditingMarkdown}
          setIsEditingMarkdown={setIsEditingMarkdown}
          editedMarkdown={editedMarkdown}
          setEditedMarkdown={setEditedMarkdown}
          savingMarkdown={savingMarkdown}
          handleSaveMarkdown={handleSaveMarkdown}
          isAnyProcessing={isAnyProcessing}
          setIsProcessing={setIsProcessing}
          setProcessingStartTime={setProcessingStartTime}
          copiedText={copiedText}
          handleCopyText={handleCopyText}
          handleMarkdownContextMenu={handleMarkdownContextMenu}
          markdownContainerRef={markdownContainerRef}
        />
      </TabsContent>

      {/* Sections Tab */}
      <TabsContent value="sections" className="flex-1 p-4">
        <PaperSectionsTab
          paper={paper}
          expandedSections={expandedSections}
          editingSectionId={editingSectionId}
          editedSectionContent={editedSectionContent}
          setEditedSectionContent={setEditedSectionContent}
          editingSectionTitleId={editingSectionTitleId}
          editedSectionTitle={editedSectionTitle}
          setEditedSectionTitle={setEditedSectionTitle}
          savingSection={savingSection}
          extractingSections={extractingSections}
          toggleSection={toggleSection}
          handleEditSection={handleEditSection}
          handleEditSectionTitle={handleEditSectionTitle}
          handleSaveSectionTitle={handleSaveSectionTitle}
          handleCancelSectionTitleEdit={handleCancelSectionTitleEdit}
          handleSaveSection={handleSaveSection}
          handleCancelSectionEdit={handleCancelSectionEdit}
          handleExtractSections={handleExtractSections}
        />
      </TabsContent>

      {/* Snippets/Notes Tab */}
      <TabsContent value="snippets" className="flex-1 p-4">
        <PaperSnippetsTab
          paper={paper}
          selectedText={selectedText}
          setSelectedText={setSelectedText}
          snippetAnnotation={snippetAnnotation}
          setSnippetAnnotation={setSnippetAnnotation}
          snippetCategory={snippetCategory}
          setSnippetCategory={setSnippetCategory}
          creatingSnippet={creatingSnippet}
          handleCreateSnippet={handleCreateSnippet}
        />
      </TabsContent>

      {/* Analyses Tab */}
      <TabsContent value="analyses" className="flex-1 p-4">
        <div className="h-full overflow-y-auto">
          <PaperAnalysisPanel
            paperId={paperId}
            paperTitle={paper.title}
            hasContent={!!(paper.content && paper.content.length >= 100)}
            onTagCreate={handleCreateTagFromPDF}
            onSnippetCreate={(text) => {
              setSelectedText(text);
              setActiveTab("snippets");
            }}
          />
        </div>
      </TabsContent>

      {/* Search Tab - client-side full-text search over the loaded content */}
      <TabsContent value="search" className="flex-1 p-4">
        <PaperSearchTab
          content={paper.markdown_content || paper.content || ""}
          onNavigateToMatch={handleNavigateToMatch}
        />
      </TabsContent>

      {/* References Tab */}
      <TabsContent value="references" className="flex-1 p-4">
        <div className="h-full overflow-y-auto">
          <PaperReferences paperId={paperId} paperTitle={paper.title} />
        </div>
      </TabsContent>

      {/* GROBID Tab */}
      <TabsContent value="grobid" className="flex-1 p-4">
        <div className="h-full overflow-y-auto">
          <GROBIDMetadataPanel
            paperId={paperId}
            onMetadataUpdated={() => {
              loadPaperDetails();
            }}
            grobidProcessed={paper.metadata?.grobid_processed}
            grobidProcessedAt={paper.metadata?.grobid_processed_at}
          />
        </div>
      </TabsContent>

      {/* TEI XML Tab */}
      <TabsContent value="tei" className="flex-1 p-4">
        <div className="h-full overflow-y-auto">
          <TEIViewer paperId={paperId} paperTitle={paper.title} />
        </div>
      </TabsContent>

      {/* BibTeX Tab */}
      <TabsContent value="bibtex" className="flex-1 p-4">
        <div className="h-full overflow-y-auto">
          <BibTeXViewer
            bibtex={paper.bibtex}
            paperId={String(paper.id)}
            title={paper.title}
            authors={typeof paper.authors === 'string' ? paper.authors : paper.authors.map(a => a.name)}
            year={paper.publication_date ? new Date(paper.publication_date).getFullYear() : undefined}
            conference={paper.conference}
            journal={paper.journal}
            doi={paper.doi}
            dblpKey={paper.dblp_key}
            dblpUrl={paper.dblp_url}
          />
        </div>
      </TabsContent>

      {/* Supplementary Material Tab */}
      {paper.metadata?.supplementary && paper.metadata.supplementary.length > 0 && (
        <TabsContent value="supplementary" className="flex-1 p-4">
          <div className="h-full overflow-y-auto">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Download className="h-5 w-5" />
                  Supplementary Materials
                </CardTitle>
                <CardDescription>
                  Additional files, datasets, and appendices associated with this paper
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {paper.metadata.supplementary.map((item, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 rounded-lg">
                          <Download className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium">{item.type || 'Supplementary Material'}</p>
                          <p className="text-sm text-gray-500 truncate max-w-md">
                            {item.url}
                          </p>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => window.open(item.url, '_blank')}
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      )}
    </Tabs>
  );
};

export default PaperTabsContent;
