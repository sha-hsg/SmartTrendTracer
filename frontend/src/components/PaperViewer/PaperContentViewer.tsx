/**
 * PaperContentViewer - Renders the markdown/content tab of the paper viewer.
 * Handles large document mode, chunked rendering, TOC sidebar, reading progress,
 * edit/view toggle, ZIP download, and ReactMarkdown rendering with custom components.
 */
import React from "react";
import http from '@/services/http'
import { API_BASE_URL } from '@/config/api';
import JSZip from "jszip";
import {
  FileCode,
  Edit2,
  CheckCircle,
  Loader2,
  Download,
  ChevronUp,
  ChevronDown,
  ChevronRight,
  Menu,
  Cpu,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { ProcessingStatusIndicator } from "./ProcessingStatusIndicator";
import { useTableOfContents } from "./hooks/useTableOfContents";
import { useDocumentChunking } from "./hooks/useDocumentChunking";
import MarkdownRenderer from "./MarkdownRenderer";
import type { Paper } from "./types";

const focusRingStyles =
  "focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2";

export interface PaperContentViewerProps {
  paper: Paper;
  paperId: string | number;
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
}

const PaperContentViewer: React.FC<PaperContentViewerProps> = ({
  paper,
  paperId,
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
}) => {
  const content = paper?.markdown_content || paper?.content;

  const {
    tableOfContents,
    activeSection,
    showTOC,
    setShowTOC,
    readingProgress,
    scrollToSection,
    navigateToSection,
    calculateReadingTime,
  } = useTableOfContents(content, markdownContainerRef);

  const {
    isLargeDocument,
    documentChunks,
    loadedChunks,
  } = useDocumentChunking(content, markdownContainerRef);

  // Handle ZIP download
  const handleDownloadZip = async () => {
    try {
      const markdownContent = paper?.markdown_content || paper?.content || "";
      const paperTitle = paper.title?.replace(/[^a-zA-Z0-9\s]/g, '').trim().substring(0, 50) || 'paper';

      const zip = new JSZip();
      const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
      const images: Array<{ alt: string; url: string; filename: string }> = [];
      let match;

      while ((match = imageRegex.exec(markdownContent)) !== null) {
        const imageUrl = match[2];
        if (imageUrl.startsWith('/api/papers/')) {
          images.push({
            alt: match[1],
            url: imageUrl,
            filename: imageUrl.split('/').pop() || 'image.png'
          });
        }
      }

      let updatedContent = markdownContent;
      let successfulImages = 0;
      let failedImages = 0;

      for (const img of images) {
        try {
          const response = await fetch(`${API_BASE_URL}${img.url}`, {
            mode: 'cors',
            credentials: 'include'
          });

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          const blob = await response.blob();
          zip.file(`images/${img.filename}`, blob);
          successfulImages++;

          updatedContent = updatedContent.replace(
            new RegExp(`!\\[${img.alt.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]\\(${img.url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\)`, 'g'),
            `![${img.alt}](images/${img.filename})`
          );
        } catch (error) {
          console.warn(`Failed to download image: ${img.url}`, error);
          failedImages++;

          updatedContent = updatedContent.replace(
            new RegExp(`!\\[${img.alt.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]\\(${img.url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\)`, 'g'),
            `![${img.alt}](${API_BASE_URL}${img.url}) <!-- Image download failed -->`
          );
        }
      }

      if (images.length > 0) {
        const summaryNote = `\n\n---\n**Download Summary:** ${successfulImages} images included, ${failedImages} images failed to download.\n`;
        updatedContent += summaryNote;
      }

      zip.file(`${paperTitle}.md`, updatedContent);

      const blob = await zip.generateAsync({ type: 'blob' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${paperTitle}_with_images.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

    } catch (error) {
      console.error('Failed to create download:', error);
      alert('Failed to create download. Please try again.');
    }
  };

  return (
    <div className="h-full bg-white rounded-lg border flex flex-col overflow-hidden">
      {/* Enhanced Edit/View Toggle Bar */}
      <div className="p-4 border-b bg-gradient-to-r from-gray-50 to-blue-50 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <FileCode className="h-4 w-4 text-blue-600" />
          <h3 className="font-medium text-gray-700">
            Extracted Content
          </h3>
          {paper.processor_used &&
            paper.processor_used !== "pypdfium2" && (
              <Badge className="text-xs bg-green-100 text-green-800 border-green-300">
                Enhanced
              </Badge>
            )}
        </div>
        <div className="flex items-center gap-2">
          {!isEditingMarkdown && (
            <div className="flex items-center gap-1">
              <span className="text-xs text-gray-500">
                Reading mode:
              </span>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-xs"
                title="Toggle focus mode"
              >
                {'\uD83D\uDC41\uFE0F'}
              </Button>
            </div>
          )}
          {!isEditingMarkdown && (paper?.content || paper?.markdown_content) && (
            <Button
              onClick={handleDownloadZip}
              size="sm"
              variant="outline"
              className="px-3 py-2 text-sm border-gray-300 hover:bg-gray-50"
              title="Download markdown with images as ZIP file"
            >
              <Download className="h-4 w-4 mr-2" />
              Download ZIP
            </Button>
          )}
          <Button
            onClick={() => {
              if (isEditingMarkdown) {
                handleSaveMarkdown();
              } else {
                setEditedMarkdown(
                  paper?.markdown_content || paper?.content || "",
                );
                setIsEditingMarkdown(true);
              }
            }}
            disabled={savingMarkdown}
            className={cn(
              "px-4 py-2 rounded-lg transition-all flex items-center gap-2 text-sm font-medium shadow-sm hover:shadow",
              isEditingMarkdown
                ? "bg-green-600 hover:bg-green-700 text-white"
                : "bg-blue-600 hover:bg-blue-700 text-white",
              focusRingStyles,
            )}
          >
            {savingMarkdown ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : isEditingMarkdown ? (
              <>
                <CheckCircle className="h-4 w-4" />
                Save Changes
              </>
            ) : (
              <>
                <Edit2 className="h-4 w-4" />
                Edit Content
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden">
        {isEditingMarkdown ? (
          <textarea
            value={editedMarkdown}
            onChange={(e) => setEditedMarkdown(e.target.value)}
            className="w-full h-full p-6 font-mono text-sm border-0 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset"
            placeholder="Edit markdown content..."
            spellCheck={false}
          />
        ) : (
          <div className="h-full flex">
            {/* Main content area */}
            <div
              ref={markdownContainerRef}
              className="flex-1 bg-gray-50 overflow-y-auto relative"
            >
              {/* Reading progress bar */}
              <div className="fixed top-0 left-0 right-0 h-1 bg-gray-200 z-10">
                <div
                  className="h-full bg-blue-600 transition-all duration-150"
                  style={{ width: `${readingProgress}%` }}
                />
              </div>

              {/* Floating navigation buttons */}
              {tableOfContents.length > 0 && (
                <div className="fixed bottom-6 right-6 z-20 flex flex-col gap-2">
                  <Button
                    onClick={() => navigateToSection('previous')}
                    disabled={activeSection === tableOfContents[0]?.id}
                    size="sm"
                    variant="outline"
                    className="bg-white shadow-lg hover:shadow-xl"
                    title="Previous section (k)"
                  >
                    <ChevronUp className="h-4 w-4" />
                  </Button>
                  <Button
                    onClick={() => navigateToSection('next')}
                    disabled={activeSection === tableOfContents[tableOfContents.length - 1]?.id}
                    size="sm"
                    variant="outline"
                    className="bg-white shadow-lg hover:shadow-xl"
                    title="Next section (j)"
                  >
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                </div>
              )}

              {(paper?.markdown_content || paper?.content) ? (
                <MarkdownRenderer
                  content={paper?.markdown_content || paper?.content || ''}
                  isLargeDocument={isLargeDocument}
                  documentChunks={documentChunks}
                  loadedChunks={loadedChunks}
                  tableOfContents={tableOfContents}
                  copiedText={copiedText}
                  handleCopyText={handleCopyText}
                  handleMarkdownContextMenu={handleMarkdownContextMenu}
                  calculateReadingTime={calculateReadingTime}
                />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center max-w-md">
                    <div className="mb-4">
                      {isAnyProcessing ? (
                        <Loader2 className="h-16 w-16 text-blue-500 mx-auto mb-6 animate-spin" />
                      ) : (
                        <FileCode className="h-16 w-16 text-gray-400 mx-auto mb-6" />
                      )}
                    </div>
                    <h3 className="text-xl font-semibold text-gray-700 mb-3">
                      {isAnyProcessing
                        ? "Processing Content..."
                        : !paper.processed
                          ? "Not Yet Processed"
                          : "No Content Available"}
                    </h3>
                    <p className="text-gray-500 mb-6 leading-relaxed">
                      {isAnyProcessing
                        ? "The paper is being processed to extract readable content. This includes text extraction, formatting, and structure analysis."
                        : !paper.processed
                          ? "This paper has not been processed yet. Use Marker or MinerU to extract readable content from the PDF."
                          : "No markdown content is available for this paper. Try processing it with an advanced method like Marker or MinerU for better text extraction."}
                    </p>
                    {isAnyProcessing ? (
                      <div className="flex justify-center">
                        <ProcessingStatusIndicator
                          paperId={paperId}
                          compact={false}
                          onComplete={() => {
                            // Content will be automatically refreshed
                          }}
                        />
                      </div>
                    ) : (
                      <div className="flex gap-2 justify-center">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={async () => {
                            try {
                              await http.post(
                                `${API_BASE_URL}/api/papers/${paperId}/process-with-marker`,
                              );
                              setIsProcessing(true);
                              setProcessingStartTime(new Date());
                            } catch (error) {
                              console.error(
                                "Failed to start processing:",
                                error,
                              );
                            }
                          }}
                          className="bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-300"
                        >
                          <Cpu className="h-3 w-3 mr-1" />
                          Process with Marker
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Table of Contents Sidebar */}
            {tableOfContents.length > 0 && (
              <div
                className={cn(
                  "border-l border-gray-200 bg-white transition-all duration-300",
                  showTOC ? "w-80" : "w-12"
                )}
              >
                {/* TOC Header */}
                <div className="p-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
                  {showTOC ? (
                    <>
                      <div className="flex items-center gap-2">
                        <Menu className="h-4 w-4 text-gray-600" />
                        <span className="font-medium text-sm text-gray-700">Table of Contents</span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowTOC(false)}
                        className="hover:bg-gray-200"
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </>
                  ) : (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowTOC(true)}
                      className="mx-auto hover:bg-gray-200"
                      title="Show Table of Contents"
                    >
                      <Menu className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                {/* TOC Content */}
                {showTOC && (
                  <ScrollArea className="h-full">
                    <div className="p-4">
                      {/* Reading stats */}
                      <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                        <div className="text-xs text-blue-600 mb-1">Reading Progress</div>
                        <div className="bg-white rounded-full h-2 mb-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-150"
                            style={{ width: `${readingProgress}%` }}
                          />
                        </div>
                        <div className="text-xs text-gray-600">
                          {calculateReadingTime(paper?.markdown_content || paper?.content || '')} min read
                        </div>
                      </div>

                      {/* Section list */}
                      <nav className="space-y-1">
                        {tableOfContents.map((item) => (
                          <button
                            key={item.id}
                            onClick={() => scrollToSection(item.id)}
                            className={cn(
                              "w-full text-left transition-colors duration-150 rounded-lg",
                              "hover:bg-gray-100",
                              activeSection === item.id
                                ? "bg-blue-50 text-blue-700 font-medium"
                                : "text-gray-600 hover:text-gray-900",
                              item.level === 1 && "py-2 px-3 text-sm",
                              item.level === 2 && "py-1.5 px-3 pl-6 text-sm",
                              item.level === 3 && "py-1 px-3 pl-9 text-xs"
                            )}
                          >
                            {item.text}
                          </button>
                        ))}
                      </nav>

                      {/* Keyboard shortcuts help */}
                      <div className="mt-6 p-3 bg-gray-50 rounded-lg">
                        <div className="text-xs font-medium text-gray-700 mb-2">Keyboard Shortcuts</div>
                        <div className="space-y-1 text-xs text-gray-600">
                          <div className="flex justify-between">
                            <span>Next section</span>
                            <kbd className="px-1.5 py-0.5 bg-white rounded border border-gray-300">j</kbd>
                          </div>
                          <div className="flex justify-between">
                            <span>Previous section</span>
                            <kbd className="px-1.5 py-0.5 bg-white rounded border border-gray-300">k</kbd>
                          </div>
                          <div className="flex justify-between">
                            <span>Go to top</span>
                            <kbd className="px-1.5 py-0.5 bg-white rounded border border-gray-300">g</kbd>
                          </div>
                          <div className="flex justify-between">
                            <span>Go to bottom</span>
                            <kbd className="px-1.5 py-0.5 bg-white rounded border border-gray-300">G</kbd>
                          </div>
                        </div>
                      </div>
                    </div>
                  </ScrollArea>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PaperContentViewer;
