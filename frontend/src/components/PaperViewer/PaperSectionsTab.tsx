/**
 * PaperSectionsTab - Renders the sections tab with section editing, title editing,
 * section extraction, and ReactMarkdown rendering for section content.
 */
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import {
  ChevronDown,
  ChevronRight,
  Check,
  X,
  Edit2,
  Loader2,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { Paper, PaperSection } from "./types";

const katexOptions = {
  strict: false,
  throwOnError: false,
  errorColor: "#cc0000",
  trust: true,
  macros: {
    "\\，": "\\,",
    "\\、": "\\,",
  },
};

export interface PaperSectionsTabProps {
  paper: Paper;
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
}

const PaperSectionsTab: React.FC<PaperSectionsTabProps> = ({
  paper,
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
}) => {
  return (
    <div className="h-full bg-white rounded-lg border">
      <ScrollArea className="h-full p-6">
        {/* Extract Sections Button */}
        {paper && (paper.markdown_content || paper.content) && (!paper.sections || paper.sections.length === 0) && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-blue-900">
                  Extract Key Sections
                </p>
                <p className="text-xs text-blue-700">
                  Use AI to extract Abstract, Introduction, and Conclusion from the paper
                </p>
              </div>
              <Button
                onClick={handleExtractSections}
                disabled={extractingSections}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {extractingSections ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Extracting...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Extract Sections
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {paper.sections && paper.sections.length > 0 ? (
          <div className="space-y-4">
            {paper.sections.map((section) => (
              <div
                key={section.id}
                className={`group border rounded-lg ${
                  section.section_type === "abstract"
                    ? "border-blue-300 bg-blue-50/30"
                    : section.section_type === "conclusion"
                      ? "border-green-300 bg-green-50/30"
                      : ""
                }`}
              >
                <div
                  onClick={() => toggleSection(section.id)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    {expandedSections.has(section.id) ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                    {editingSectionTitleId === section.id ? (
                      <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="text"
                          value={editedSectionTitle}
                          onChange={(e) => setEditedSectionTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleSaveSectionTitle(section.id);
                            } else if (e.key === 'Escape') {
                              handleCancelSectionTitleEdit();
                            }
                          }}
                          className="px-2 py-1 border rounded text-sm"
                          autoFocus
                        />
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleSaveSectionTitle(section.id)}
                          className="h-6 px-2"
                        >
                          <Check className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={handleCancelSectionTitleEdit}
                          className="h-6 px-2"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    ) : (
                      <span className="font-medium flex items-center gap-1">
                        {section.section_type === "abstract" && "\uD83D\uDCC4 "}
                        {section.section_type === "conclusion" && "\uD83C\uDFAF "}
                        {section.title}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEditSectionTitle(section);
                          }}
                          className="h-5 w-5 p-0 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Edit title"
                        >
                          <Edit2 className="h-3 w-3" />
                        </Button>
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={
                        section.section_type === "abstract"
                          ? "default"
                          : section.section_type === "conclusion"
                            ? "secondary"
                            : "outline"
                      }
                    >
                      {section.section_type}
                    </Badge>
                    {expandedSections.has(section.id) &&
                      editingSectionId !== section.id && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEditSection(section);
                          }}
                          className="h-6 px-2"
                        >
                          Edit
                        </Button>
                      )}
                  </div>
                </div>
                {expandedSections.has(section.id) && (
                  <div className="px-4 py-3 border-t">
                    {editingSectionId === section.id ? (
                      <div className="space-y-3">
                        <Textarea
                          value={editedSectionContent}
                          onChange={(e) =>
                            setEditedSectionContent(e.target.value)
                          }
                          className="min-h-[300px] font-mono text-sm"
                          placeholder="Edit section content..."
                        />
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={handleCancelSectionEdit}
                          >
                            Cancel
                          </Button>
                          <Button
                            size="sm"
                            onClick={() =>
                              handleSaveSection(section.id)
                            }
                            disabled={savingSection}
                          >
                            {savingSection ? (
                              <>
                                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                Saving...
                              </>
                            ) : (
                              "Save"
                            )}
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[
                            rehypeRaw,
                            [rehypeKatex, katexOptions],
                            rehypeHighlight,
                          ]}
                          components={{
                            h1: ({ node, ...props }) => (
                              <h1
                                {...props}
                                className="text-2xl font-bold text-gray-900 mb-4 mt-6"
                              />
                            ),
                            h2: ({ node, ...props }) => (
                              <h2
                                {...props}
                                className="text-xl font-semibold text-gray-800 mb-3 mt-5"
                              />
                            ),
                            h3: ({ node, ...props }) => (
                              <h3
                                {...props}
                                className="text-lg font-medium text-gray-800 mb-2 mt-4"
                              />
                            ),
                            h4: ({ node, ...props }) => (
                              <h4
                                {...props}
                                className="text-base font-medium text-gray-700 mb-2 mt-3"
                              />
                            ),
                            p: ({ node, ...props }) => (
                              <p
                                {...props}
                                className="text-gray-700 mb-4 leading-relaxed"
                              />
                            ),
                            ul: ({ node, ...props }) => (
                              <ul
                                {...props}
                                className="list-disc list-inside mb-4 space-y-1"
                              />
                            ),
                            ol: ({ node, ...props }) => (
                              <ol
                                {...props}
                                className="list-decimal list-inside mb-4 space-y-1"
                              />
                            ),
                            li: ({ node, ...props }) => (
                              <li
                                {...props}
                                className="text-gray-700"
                              />
                            ),
                            strong: ({ node, ...props }) => (
                              <strong
                                {...props}
                                className="font-semibold text-gray-900"
                              />
                            ),
                            em: ({ node, ...props }) => (
                              <em {...props} className="italic" />
                            ),
                            code: ({ className, ...props }: React.HTMLAttributes<HTMLElement> & { node?: unknown }) => {
                              const isInline = !className?.includes('language-')
                              if (isInline) {
                                return (
                                  <code
                                    {...props}
                                    className="text-pink-600 bg-pink-50 px-1.5 py-0.5 rounded font-mono text-sm"
                                  />
                                );
                              }
                              return <code className={className} {...props} />;
                            },
                            blockquote: ({ node, ...props }) => (
                              <blockquote
                                {...props}
                                className="border-l-4 border-blue-500 pl-4 italic text-gray-600 my-4"
                              />
                            ),
                            a: ({ node, href, children, ...props }) => {
                              if (href && href.startsWith('#')) {
                                return (
                                  <a
                                    {...props}
                                    href={href}
                                    onClick={(e) => {
                                      e.preventDefault();
                                      const targetId = href.substring(1);
                                      const targetElement = document.getElementById(targetId);
                                      if (targetElement) {
                                        targetElement.scrollIntoView({
                                          behavior: 'smooth',
                                          block: 'start'
                                        });
                                        targetElement.style.backgroundColor = '#fef3c7';
                                        setTimeout(() => {
                                          targetElement.style.backgroundColor = '';
                                        }, 2000);
                                      } else {
                                        const allSpans = document.querySelectorAll('span[id]');
                                        for (const span of allSpans) {
                                          if (span.id === targetId) {
                                            span.scrollIntoView({
                                              behavior: 'smooth',
                                              block: 'start'
                                            });
                                            (span as HTMLElement).style.backgroundColor = '#fef3c7';
                                            setTimeout(() => {
                                              (span as HTMLElement).style.backgroundColor = '';
                                            }, 2000);
                                            break;
                                          }
                                        }
                                      }
                                    }}
                                    className="text-blue-600 hover:text-blue-800 underline cursor-pointer"
                                  >
                                    {children}
                                  </a>
                                );
                              }
                              return (
                                <a
                                  {...props}
                                  href={href}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:text-blue-800 underline"
                                >
                                  {children}
                                </a>
                              );
                            },
                            sup: ({ node, ...props }) => (
                              <sup {...props} className="text-xs align-super" />
                            ),
                            sub: ({ node, ...props }) => (
                              <sub {...props} className="text-xs align-sub" />
                            ),
                            span: ({ node, id, ...props }) => (
                              <span {...props} id={id} />
                            ),
                            div: ({ node, id, className, ...props }) => (
                              <div {...props} id={id} className={className} />
                            ),
                            think: ({ children }: { node?: unknown; children?: React.ReactNode }) => (
                              <code className="text-pink-600 bg-pink-50 px-1.5 py-0.5 rounded font-mono text-sm">
                                {'<think>'}
                                {children}
                                {'</think>'}
                              </code>
                            ),
                          } as Record<string, React.ComponentType<any>>}
                        >
                          {section.content}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500">No sections available</p>
          </div>
        )}
      </ScrollArea>
    </div>
  );
};

export default PaperSectionsTab;
