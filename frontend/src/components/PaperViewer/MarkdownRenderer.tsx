import React from "react";
import ReactMarkdown from "react-markdown";
import { API_BASE_URL } from '@/config/api';
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import {
  CheckCircle,
  Copy,
} from "lucide-react";
import type { DocumentChunk, TOCItem } from "./types";

const HTML_TAG_COMPONENTS = {
  original: ({ children, ...props }: any) => (
    <span {...props} className={`font-semibold ${props.className ?? ""}`.trim()}>{children}</span>
  ),
  topic: ({ children, ...props }: any) => (
    <span {...props} className={`italic text-blue-600 ${props.className ?? ""}`.trim()}>{children}</span>
  ),
  empty: () => null,
  figure_caption: ({ children, ...props }: any) => (
    <figcaption {...props} className="text-sm text-gray-600 mt-2 italic">{children}</figcaption>
  ),
};

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

// Memoized markdown chunk component for large documents
const MarkdownChunk = React.memo(({ chunk, isLoaded }: {
  chunk: DocumentChunk;
  isLoaded: boolean;
}) => {
  if (!isLoaded) {
    return (
      <div className="my-8 p-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300" data-chunk-id={chunk.id}>
        <div className="flex flex-col items-center justify-center text-gray-500">
          <svg className="w-8 h-8 mb-2 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="text-sm font-medium">Section {parseInt(chunk.id.replace('chunk-', '')) + 1}</span>
          <span className="text-xs mt-1">Loading on scroll...</span>
        </div>
      </div>
    );
  }

  return (
    <div data-chunk-id={chunk.id}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[
          rehypeRaw,
          [rehypeKatex, katexOptions],
          rehypeHighlight,
        ]}
        components={{
          ...HTML_TAG_COMPONENTS,
          h1: ({ node, children, ...props }) => {
            const text = children?.toString() || '';
            const heading = chunk.headings.find(h => h.text === text && h.level === 1);
            const id = heading?.id || '';
            return (
              <h1 {...props} data-heading-id={id} className="text-3xl font-bold mt-8 mb-4 text-gray-900 scroll-mt-4">
                {children}
              </h1>
            );
          },
          h2: ({ node, children, ...props }) => {
            const text = children?.toString() || '';
            const heading = chunk.headings.find(h => h.text === text && h.level === 2);
            const id = heading?.id || '';
            return (
              <h2 {...props} data-heading-id={id} className="text-2xl font-semibold mt-6 mb-3 text-gray-800 scroll-mt-4">
                {children}
              </h2>
            );
          },
          h3: ({ node, children, ...props }) => {
            const text = children?.toString() || '';
            const heading = chunk.headings.find(h => h.text === text && h.level === 3);
            const id = heading?.id || '';
            return (
              <h3 {...props} data-heading-id={id} className="text-xl font-medium mt-4 mb-2 text-gray-700 scroll-mt-4">
                {children}
              </h3>
            );
          },
          img: ({ node, ...props }) => {
            const src = props.src?.startsWith("/api/")
              ? API_BASE_URL + props.src
              : props.src;
            return (
              <span className="block my-6">
                <img {...props} src={src} className="max-w-full h-auto rounded-lg shadow-lg mx-auto block" />
                {props.alt && (
                  <span className="block text-sm text-gray-600 mt-2 text-center">
                    {props.alt}
                  </span>
                )}
              </span>
            );
          },
        }}
      >
        {chunk.content}
      </ReactMarkdown>
    </div>
  );
});

MarkdownChunk.displayName = 'MarkdownChunk';

export interface MarkdownRendererProps {
  content: string;
  isLargeDocument: boolean;
  documentChunks: DocumentChunk[];
  loadedChunks: Set<string>;
  tableOfContents: TOCItem[];
  copiedText: string | null;
  handleCopyText: (text: string) => void;
  handleMarkdownContextMenu: (e: React.MouseEvent) => void;
  calculateReadingTime: (text: string) => number;
}

const ARTICLE_PROSE_CLASSES = `prose prose-lg max-w-none overflow-hidden
  prose-headings:font-bold prose-headings:text-gray-900 prose-headings:scroll-mt-20
  prose-h1:text-3xl prose-h1:mt-8 prose-h1:mb-6 prose-h1:pb-3 prose-h1:border-b prose-h1:border-gray-200
  prose-h2:text-2xl prose-h2:mt-8 prose-h2:mb-4 prose-h2:text-blue-900
  prose-h3:text-xl prose-h3:mt-6 prose-h3:mb-3 prose-h3:text-gray-800
  prose-h4:text-lg prose-h4:mt-4 prose-h4:mb-2 prose-h4:text-gray-700
  prose-p:text-gray-700 prose-p:leading-relaxed prose-p:mb-5 prose-p:break-words prose-p:text-base
  prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline hover:prose-a:text-blue-800 prose-a:break-all prose-a:font-medium
  prose-strong:text-gray-900 prose-strong:font-semibold
  prose-em:text-gray-600 prose-em:italic
  prose-code:text-pink-700 prose-code:bg-pink-50 prose-code:px-2 prose-code:py-1 prose-code:rounded prose-code:font-mono prose-code:text-sm prose-code:before:content-[''] prose-code:after:content-[''] prose-code:break-all prose-code:border prose-code:border-pink-200
  prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-pre:overflow-x-auto prose-pre:rounded-xl prose-pre:p-0 prose-pre:my-8 prose-pre:max-w-full prose-pre:shadow-lg
  prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-6 prose-blockquote:pr-4 prose-blockquote:py-2 prose-blockquote:italic prose-blockquote:text-gray-600 prose-blockquote:my-6 prose-blockquote:bg-blue-50 prose-blockquote:rounded-r
  prose-ul:list-disc prose-ul:pl-8 prose-ul:my-5 prose-ul:space-y-1
  prose-ol:list-decimal prose-ol:pl-8 prose-ol:my-5 prose-ol:space-y-1
  prose-li:text-gray-700 prose-li:leading-relaxed prose-li:text-base
  prose-table:border-collapse prose-table:w-full prose-table:my-8 prose-table:overflow-x-auto prose-table:block prose-table:max-w-full prose-table:shadow-sm
  prose-thead:bg-gray-50
  prose-th:border prose-th:border-gray-300 prose-th:px-6 prose-th:py-3 prose-th:text-left prose-th:font-semibold prose-th:text-gray-900 prose-th:bg-gray-100
  prose-td:border prose-td:border-gray-300 prose-td:px-6 prose-td:py-3 prose-td:text-gray-700
  prose-img:rounded-xl prose-img:shadow-lg prose-img:my-8 prose-img:mx-auto prose-img:max-w-full prose-img:h-auto prose-img:border prose-img:border-gray-200
  prose-figure:my-8 prose-figure:text-center
  prose-figcaption:text-sm prose-figcaption:text-gray-500 prose-figcaption:mt-3 prose-figcaption:italic
  prose-hr:border-gray-300 prose-hr:my-12`;

const ARTICLE_STYLE = {
  maxWidth: "100%",
  wordBreak: "break-word" as const,
  overflowWrap: "anywhere" as const,
  fontSize: "16px",
  lineHeight: "1.75",
};

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  isLargeDocument,
  documentChunks,
  loadedChunks,
  tableOfContents,
  copiedText,
  handleCopyText,
  handleMarkdownContextMenu,
  calculateReadingTime,
}) => {
  return (
    <div
      className="mx-auto my-8 p-8 overflow-x-hidden bg-white shadow-sm rounded-lg border border-gray-200"
      style={{
        width: "100%",
        maxWidth: "800px",
        lineHeight: "1.7",
      }}
      onContextMenu={handleMarkdownContextMenu}
    >
      {isLargeDocument && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-2 text-blue-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span className="font-medium">Large Document Mode</span>
            <span className="text-sm">({documentChunks.length} sections, {loadedChunks.size} loaded)</span>
          </div>
          <div className="mt-1 text-sm text-blue-600">
            Content is loaded progressively as you scroll
          </div>
        </div>
      )}
      <article
        className={ARTICLE_PROSE_CLASSES}
        style={ARTICLE_STYLE}
      >
        {isLargeDocument ? (
          <div>
            {documentChunks.map((chunk) => (
              <MarkdownChunk
                key={chunk.id}
                chunk={chunk}
                isLoaded={loadedChunks.has(chunk.id)}
              />
            ))}
          </div>
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[
              rehypeRaw,
              [rehypeKatex, katexOptions],
              rehypeHighlight,
            ]}
            components={{
              h1: ({ node, children, ...props }) => {
                const text = children?.toString() || '';
                const index = tableOfContents.findIndex(item => item.text === text && item.level === 1);
                const id = index >= 0 ? tableOfContents[index].id : '';
                return (
                  <h1
                    {...props}
                    data-heading-id={id}
                    className="text-3xl font-bold mt-8 mb-4 text-gray-900 scroll-mt-4"
                  >
                    {children}
                  </h1>
                );
              },
              h2: ({ node, children, ...props }) => {
                const text = children?.toString() || '';
                const index = tableOfContents.findIndex(item => item.text === text && item.level === 2);
                const id = index >= 0 ? tableOfContents[index].id : '';
                return (
                  <h2
                    {...props}
                    data-heading-id={id}
                    className="text-2xl font-semibold mt-6 mb-3 text-gray-800 scroll-mt-4"
                  >
                    {children}
                  </h2>
                );
              },
              h3: ({ node, children, ...props }) => {
                const text = children?.toString() || '';
                const index = tableOfContents.findIndex(item => item.text === text && item.level === 3);
                const id = index >= 0 ? tableOfContents[index].id : '';
                return (
                  <h3
                    {...props}
                    data-heading-id={id}
                    className="text-xl font-medium mt-4 mb-2 text-gray-700 scroll-mt-4"
                  >
                    {children}
                  </h3>
                );
              },
              h4: ({ node, ...props }) => (
                <h4
                  {...props}
                  className="text-lg font-medium mt-3 mb-2 text-gray-600"
                />
              ),
              p: ({ node, ...props }) => (
                <p
                  {...props}
                  className="mb-4 text-gray-700 leading-relaxed"
                />
              ),
              img: ({ node, ...props }) => {
                const src = props.src?.startsWith("/api/")
                  ? API_BASE_URL + props.src
                  : props.src;
                return (
                  <span className="block my-6">
                    <img
                      {...props}
                      src={src}
                      className="max-w-full h-auto rounded-lg shadow-lg mx-auto block"
                    />
                    {props.alt && (
                      <span className="block text-sm text-gray-600 mt-2 text-center">
                        {props.alt}
                      </span>
                    )}
                  </span>
                );
              },
              pre: ({ node, ...props }) => (
                <div className="relative group my-6 max-w-full overflow-x-auto">
                  <pre
                    {...props}
                    className="!bg-gray-900 !text-gray-100 rounded-lg overflow-x-auto max-w-full"
                  />
                  <button
                    onClick={() => {
                      const code =
                        (props.children as any)?.props?.children;
                      if (code) handleCopyText(code);
                    }}
                    className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity bg-gray-800 hover:bg-gray-700 text-gray-300 px-2 py-1 rounded text-xs"
                  >
                    {copiedText ===
                    (props.children as any)?.props?.children ? (
                      <span className="flex items-center gap-1">
                        <CheckCircle className="h-3 w-3" />
                        Copied!
                      </span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <Copy className="h-3 w-3" />
                        Copy
                      </span>
                    )}
                  </button>
                </div>
              ),
              code: ({
                className,
                children,
                ...props
              }: React.HTMLAttributes<HTMLElement> & { node?: unknown }) => {
                const isInline = !className?.includes('language-')
                if (isInline) {
                  return (
                    <code
                      {...props}
                      className="text-pink-600 bg-pink-50 px-1.5 py-0.5 rounded font-mono text-sm"
                    >
                      {children}
                    </code>
                  );
                }
                return (
                  <code {...props} className={className}>
                    {children}
                  </code>
                );
              },
              table: ({ node, ...props }) => (
                <div className="overflow-x-auto my-6 rounded-lg border border-gray-200 max-w-full">
                  <table
                    {...props}
                    className="min-w-full divide-y divide-gray-200"
                  />
                </div>
              ),
              blockquote: ({ node, ...props }) => (
                <blockquote
                  {...props}
                  className="border-l-4 border-blue-500 pl-4 italic text-gray-600 my-6"
                />
              ),
              sup: ({ node, ...props }) => (
                <sup {...props} className="text-xs align-super" />
              ),
              sub: ({ node, ...props }) => (
                <sub {...props} className="text-xs align-sub" />
              ),
              span: ({ node, id, ...props }) => (
                <span {...props} id={id} />
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
            {content}
          </ReactMarkdown>
        )}

        {content && (
          <div className="mt-8 pt-4 border-t border-gray-200 text-center text-sm text-gray-500">
            Estimated reading time: {calculateReadingTime(content)} minutes
          </div>
        )}
      </article>
    </div>
  );
};

export default MarkdownRenderer;
