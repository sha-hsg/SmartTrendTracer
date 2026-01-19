import React, { useState, useEffect, useCallback, useRef } from "react";
import ReactDOM from "react-dom";
import axios from "axios";
import JSZip from "jszip";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import "katex/dist/katex.min.css";
import "highlight.js/styles/github-dark.css";

const HTML_TAG_COMPONENTS = {
  original: ({ children, ...props }: any) => (
    <span {...props} className={`font-semibold ${props.className ?? ""}`.trim()}>{children}</span>
  ),
  topic: ({ children, ...props }: any) => (
    <span {...props} className={`italic text-blue-600 ${props.className ?? ""}`.trim()}>{children}</span>
  ),
};

// Configure KaTeX options for better error handling
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

import {
  FileText,
  User,
  Calendar,
  Building2,
  BookOpen,
  Tag as TagIcon,
  ExternalLink,
  Download,
  Search,
  Plus,
  X,
  Check,
  ChevronDown,
  ChevronUp,
  ChevronRight,
  ChevronLeft,
  Copy,
  CheckCircle,
  Loader2,
  MessageSquare,
  Hash,
  FileCode,
  Menu,
  Brain,
  Sparkles,
  Highlighter,
  PlayCircle,
  RotateCcw,
  Edit2,
  Cpu,
  GraduationCap,
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
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import PDFViewerModern from "./PDFViewerModern";

// Accessibility and UX enhancement styles
const focusRingStyles =
  "focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2";
const touchTargetStyles = "min-h-[44px] min-w-[44px]";
import { ProcessingTimer } from "./ProcessingTimer";
import { ProcessingStatusIndicator } from "./ProcessingStatusIndicator";
import PaperAnalysisPanel from "./PaperAnalysisPanel";
import TEIViewer from "./TEIViewer";
import PaperReferences from "./PaperReferences";
import GROBIDMetadataPanel from "./GROBIDMetadataPanel";
import PaperTagSuggestionModal from "./PaperTagSuggestionModal";
import PaperEntityAnnotationReview from "./PaperEntityAnnotationReview";
import { DBLPSearchModal } from "./DBLPSearchModal";
import BibTeXViewer from "./BibTeXViewer";
import ConceptEditModal from "./ConceptEditModal";
import { MarkerProgressModal } from "./MarkerProgressModal";

interface PaperSection {
  id: number;
  section_type: string;
  title: string;
  content: string;
  position: number;
}

interface PaperSnippet {
  id: number;
  content: string;
  annotation?: string;
  category?: string;
  created_at: string;
  page_number?: number;
}

interface PaperAuthor {
  name: string;
  email?: string;
}

interface Paper {
  id: number;
  title: string;
  abstract?: string;
  content?: string;
  markdown_content?: string;
  authors: PaperAuthor[] | string;  // Can be array or string
  authors_detailed?: Array<{
    name: string;
    affiliation?: string;
    email?: string;
  }>;
  authors_list?: Array<{
    name: string;
    affiliation?: string;
    email?: string;
    position?: number;
  }>;
  affiliations?: Array<string | { name: string }>;
  publication_date?: string;
  conference?: string;
  journal?: string;
  arxiv_id?: string;
  doi?: string;
  openreview_id?: string;
  openreview_url?: string;
  bibtex?: string;
  import_source?: string;  // Source type: arxiv, acl, acm, openreview, direct
  import_url?: string;  // Original import URL
  page_count: number;
  tags?: string[]; // Made optional since API might not return it
  created_at: string;
  processed: boolean;
  processor_used?: string;
  processing_status?: string;
  processing_error?: string;
  pdf_path?: string;
  sections?: PaperSection[];
  snippets?: PaperSnippet[];
  metadata?: {
    supplementary?: Array<{
      type: string;
      url: string;
    }>;
    grobid_processed?: boolean;
    grobid_processed_at?: string;
    [key: string]: any;
  };
}

interface PaperViewerOptimizedProps {
  paperId: string | number; // Support both MongoDB ObjectId strings and legacy integer IDs
  onClose?: () => void;
  onMetadataUpdate?: () => void;
}

const PaperViewerOptimized: React.FC<PaperViewerOptimizedProps> = ({
  paperId,
  onClose,
  onMetadataUpdate,
}) => {
  const [paper, setPaper] = useState<Paper | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("pdf");
  const [expandedSections, setExpandedSections] = useState<Set<number>>(
    new Set(),
  );
  const [copiedText, setCopiedText] = useState<string | null>(null);
  const [pdfAvailable, setPdfAvailable] = useState(false);
  const [processingStartTime, setProcessingStartTime] = useState<Date | null>(
    null,
  );
  const [isProcessing, setIsProcessing] = useState(false);
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isEditingMarkdown, setIsEditingMarkdown] = useState(false);
  const [editedMarkdown, setEditedMarkdown] = useState("");
  const [savingMarkdown, setSavingMarkdown] = useState(false);

  // Table of Contents and Navigation
  const [tableOfContents, setTableOfContents] = useState<Array<{
    id: string;
    text: string;
    level: number;
    position: number;
  }>>([]);
  const [activeSection, setActiveSection] = useState<string>("");
  const [showTOC, setShowTOC] = useState(true);
  const [readingProgress, setReadingProgress] = useState(0);
  const markdownContainerRef = useRef<HTMLDivElement>(null);
  const scrollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Large document handling
  const [isLargeDocument, setIsLargeDocument] = useState(false);
  const [documentChunks, setDocumentChunks] = useState<Array<{
    id: string;
    content: string;
    startIndex: number;
    endIndex: number;
    headings: Array<{ id: string; text: string; level: number; }>;
  }>>([]);
  const [loadedChunks, setLoadedChunks] = useState<Set<string>>(new Set());
  const CHUNK_SIZE = 50000; // 50KB chunks
  const LARGE_DOC_THRESHOLD = 200000; // 200KB = ~80 pages
  const chunkObserverRef = useRef<IntersectionObserver | null>(null);
  const [showTagModal, setShowTagModal] = useState(false);
  const [showEntityModal, setShowEntityModal] = useState(false);

  // Snippet creation
  const [selectedText, setSelectedText] = useState("");
  const [snippetAnnotation, setSnippetAnnotation] = useState("");
  const [snippetCategory, setSnippetCategory] = useState("");
  const [creatingSnippet, setCreatingSnippet] = useState(false);

  // Tag management
  const [newTag, setNewTag] = useState("");
  const [addingTag, setAddingTag] = useState(false);
  const [editingMetadata, setEditingMetadata] = useState(false);
  const [extractingAuthors, setExtractingAuthors] = useState(false);
  const [editedMetadata, setEditedMetadata] = useState<any>(null);
  const [editingSectionId, setEditingSectionId] = useState<number | null>(null);
  const [editedSectionContent, setEditedSectionContent] = useState<string>("");
  const [editingSectionTitleId, setEditingSectionTitleId] = useState<number | null>(null);
  const [editedSectionTitle, setEditedSectionTitle] = useState<string>("");
  const [savingSection, setSavingSection] = useState<boolean>(false);
  const [extractingSections, setExtractingSections] = useState<boolean>(false);

  // Markdown text selection and context menu
  const [, setSelectedMarkdownText] = useState("");
  const [showMarkdownContextMenu, setShowMarkdownContextMenu] = useState(false);
  const [markdownContextMenuPosition, setMarkdownContextMenuPosition] =
    useState({ x: 0, y: 0 });
  const [showMarkdownTagDialog, setShowMarkdownTagDialog] = useState(false);
  const [markdownTagText, setMarkdownTagText] = useState("");
  const [creatingMarkdownTag, setCreatingMarkdownTag] = useState(false);
  const selectedMarkdownTextRef = useRef<string>("");

  // DBLP search
  const [showDBLPModal, setShowDBLPModal] = useState(false);
  const [showMarkerModal, setShowMarkerModal] = useState(false);

  // Affiliation extraction
  const [showAffiliationDialog, setShowAffiliationDialog] = useState(false);
  const [extractingAffiliations, setExtractingAffiliations] = useState(false);
  const [affiliationSuggestions, setAffiliationSuggestions] = useState<any[]>([]);
  const [selectedAffiliations, setSelectedAffiliations] = useState<Set<number>>(new Set());
  
  // Import URL editing
  const [editingImportUrl, setEditingImportUrl] = useState(false);
  const [editedImportUrl, setEditedImportUrl] = useState("");
  const [savingImportUrl, setSavingImportUrl] = useState(false);
  
  // Concept editing
  const [editingConceptTag, setEditingConceptTag] = useState<string | null>(null);
  const [showConceptEditModal, setShowConceptEditModal] = useState(false);
  
  // Processing button states - derive from paper's processing_status
  const processingWithMarker = paper?.processing_status === "processing_with_marker";
  const processingWithMinerU = paper?.processing_status === "processing_with_mineru";
  const processingWithAuto = paper?.processing_status === "processing" || paper?.processing_status === "processing_pdf";
  const isAnyProcessing = processingWithMarker || processingWithMinerU || processingWithAuto;
  const [processingError, setProcessingError] = useState<string | null>(null);

  // Function declarations that are used by useEffect hooks must be declared before the hooks
  const loadPaperDetails = async (retryCount = 0) => {
    if (retryCount === 0) {
      setLoading(true);
    }
    setError(null);

    try {
      const paperResponse = await axios.get(
        `http://localhost:8000/api/papers/${paperId}`,
      );

      const combinedData: Partial<Paper> & { id?: string | number } = {
        ...paperResponse.data,
      };

      let pdfPath = paperResponse.data?.pdf_path;

      // Content, snippets, and sections may not exist yet while processing. Treat 404 as "not ready" instead of fatal.
      try {
        const contentResponse = await axios.get(
          `http://localhost:8000/api/papers/${paperId}/content`,
        );
        Object.assign(combinedData, contentResponse.data);
        pdfPath = contentResponse.data?.pdf_path ?? pdfPath;
      } catch (contentErr: any) {
        if (contentErr.response?.status === 404) {
          console.info("Paper content not available yet");
        } else {
          throw contentErr;
        }
      }

      try {
        const snippetsResponse = await axios.get(
          `http://localhost:8000/api/papers/${paperId}/snippets`,
        );
        combinedData.snippets = snippetsResponse.data;
      } catch (snippetsErr: any) {
        if (snippetsErr.response?.status === 404) {
          combinedData.snippets = [];
        } else {
          throw snippetsErr;
        }
      }

      try {
        const sectionsResponse = await axios.get(
          `http://localhost:8000/api/papers/${paperId}/sections`,
        );
        combinedData.sections = sectionsResponse.data || [];
      } catch (sectionsErr: any) {
        if (sectionsErr.response?.status === 404) {
          combinedData.sections = [];
        } else {
          console.warn("Paper sections unavailable:", sectionsErr);
        }
      }

      setPaper((prev) => ({ ...(prev || {}), ...combinedData } as Paper));
      setEditedImportUrl(combinedData.import_url || "");
      setPdfAvailable(Boolean(pdfPath));
    } catch (err: any) {
      const status = err.response?.status;
      const errorMsg =
        err.response?.data?.detail || err.message || "Failed to load paper details";
      console.error("Paper loading error:", errorMsg);

      if (retryCount < 2 && (status === 500 || status === 503)) {
        const delay = Math.min(1000 * Math.pow(2, retryCount), 10000);
        console.log(`Retrying paper load in ${delay}ms...`);
        setTimeout(() => loadPaperDetails(retryCount + 1), delay);
        return;
      }

      if (status === 404) {
        setPaper(null);
        setPdfAvailable(false);
      }

      setError(errorMsg);
    } finally {
      if (retryCount === 0) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    loadPaperDetails();
    // Don't load tag suggestions automatically - wait for user to request them
    // loadTagSuggestions() // REMOVED: This wastes LLM tokens by loading suggestions for every paper view

    // Cleanup function to stop polling when component unmounts or paperId changes
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [paperId]);

  // Create chunks for large documents
  const createDocumentChunks = useCallback((content: string) => {
    const chunks = [];
    let currentIndex = 0;
    let chunkId = 0;

    while (currentIndex < content.length) {
      const endIndex = Math.min(currentIndex + CHUNK_SIZE, content.length);

      // Try to find a good break point (paragraph or heading)
      let breakPoint = endIndex;
      if (endIndex < content.length) {
        // Look for paragraph break near the chunk boundary
        const searchStart = Math.max(endIndex - 2000, currentIndex);
        const nextParagraph = content.indexOf('\n\n', searchStart);
        if (nextParagraph > 0 && nextParagraph < endIndex + 2000 && nextParagraph > currentIndex) {
          breakPoint = nextParagraph;
        }
      }

      const chunkContent = content.substring(currentIndex, breakPoint);

      // Extract headings for this chunk
      const headingRegex = /^(#{1,3})\s+(.+)$/gm;
      const chunkHeadings = [];
      let match;

      while ((match = headingRegex.exec(chunkContent)) !== null) {
        chunkHeadings.push({
          id: `chunk-${chunkId}-heading-${chunkHeadings.length}`,
          text: match[2].trim(),
          level: match[1].length
        });
      }

      chunks.push({
        id: `chunk-${chunkId}`,
        content: chunkContent,
        startIndex: currentIndex,
        endIndex: breakPoint,
        headings: chunkHeadings
      });

      currentIndex = breakPoint;
      chunkId++;
    }

    return chunks;
  }, [CHUNK_SIZE]);

  // Extract table of contents from markdown
  const extractTableOfContents = useCallback((content: string) => {
    const headingRegex = /^(#{1,3})\s+(.+)$/gm;
    const toc = [];
    let match;
    let index = 0;

    while ((match = headingRegex.exec(content)) !== null) {
      const level = match[1].length;
      const text = match[2].trim();
      const id = `heading-${index}`;

      toc.push({
        id,
        text,
        level,
        position: match.index
      });
      index++;
    }

    setTableOfContents(toc);
  }, []);

  // Initialize TOC when paper content changes
  useEffect(() => {
    if (paper?.markdown_content || paper?.content) {
      const content = paper?.markdown_content || paper?.content || "";

      // Check if this is a large document
      const contentSize = new Blob([content]).size;

      if (contentSize > LARGE_DOC_THRESHOLD) {
        // Large document - use chunking
        setIsLargeDocument(true);
        const chunks = createDocumentChunks(content);
        setDocumentChunks(chunks);

        // Initially load first 3 chunks
        const initialChunks = new Set<string>();
        chunks.slice(0, 3).forEach(chunk => {
          initialChunks.add(chunk.id);
        });
        setLoadedChunks(initialChunks);

        console.log(`📚 Large document detected: ${(contentSize / 1024).toFixed(1)}KB, created ${chunks.length} chunks`);
      } else {
        // Regular document
        setIsLargeDocument(false);
        setDocumentChunks([]);
        setLoadedChunks(new Set());
      }

      // Extract TOC from full content regardless of size
      extractTableOfContents(content);
    }
  }, [paper?.markdown_content, paper?.content, extractTableOfContents, createDocumentChunks, LARGE_DOC_THRESHOLD]);

  // Handle scroll to track reading progress
  const handleMarkdownScroll = useCallback(() => {
    if (!markdownContainerRef.current) return;

    const container = markdownContainerRef.current;
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight - container.clientHeight;

    // Update reading progress
    const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
    setReadingProgress(Math.min(100, Math.round(progress)));
  }, []);

  // Use Intersection Observer for efficient section tracking
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    if (!markdownContainerRef.current || tableOfContents.length === 0) return;

    // Clean up previous observer
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    const options = {
      root: markdownContainerRef.current,
      rootMargin: '-20% 0px -70% 0px',
      threshold: [0, 0.1, 0.5, 0.9, 1]
    };

    observerRef.current = new IntersectionObserver((entries) => {
      const visibleSections = entries
        .filter(entry => entry.isIntersecting)
        .map(entry => ({
          id: entry.target.getAttribute('data-heading-id') || '',
          ratio: entry.intersectionRatio,
          top: entry.boundingClientRect.top
        }))
        .filter(section => section.id);

      if (visibleSections.length > 0) {
        // Find the section closest to the top of the viewport
        const closestSection = visibleSections.reduce((prev, curr) => {
          return Math.abs(curr.top) < Math.abs(prev.top) ? curr : prev;
        });

        if (closestSection.id && closestSection.id !== activeSection) {
          setActiveSection(closestSection.id);
          // Update URL hash without triggering scroll
          window.history.replaceState(null, '', `#${closestSection.id}`);
        }
      }
    }, options);

    // Observe all headings
    const headings = markdownContainerRef.current.querySelectorAll('[data-heading-id]');
    headings.forEach(heading => {
      if (observerRef.current) {
        observerRef.current.observe(heading);
      }
    });

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [tableOfContents, activeSection]);

  // Lazy loading observer for document chunks
  useEffect(() => {
    if (!isLargeDocument || !markdownContainerRef.current) return;

    // Clean up previous observer
    if (chunkObserverRef.current) {
      chunkObserverRef.current.disconnect();
    }

    const options = {
      root: markdownContainerRef.current,
      rootMargin: '500px', // Load chunks 500px before they come into view
      threshold: 0
    };

    chunkObserverRef.current = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const chunkId = entry.target.getAttribute('data-chunk-id');
          if (chunkId && !loadedChunks.has(chunkId)) {
            // Load this chunk
            setLoadedChunks(prev => new Set([...prev, chunkId]));
            console.log(`Loading chunk: ${chunkId}`);
          }
        }
      });
    }, options);

    // Observe chunk placeholders
    const chunkPlaceholders = markdownContainerRef.current.querySelectorAll('[data-chunk-id]');
    chunkPlaceholders.forEach(placeholder => {
      if (chunkObserverRef.current) {
        chunkObserverRef.current.observe(placeholder);
      }
    });

    return () => {
      if (chunkObserverRef.current) {
        chunkObserverRef.current.disconnect();
      }
    };
  }, [isLargeDocument, documentChunks, loadedChunks]);

  // Scroll to section
  const scrollToSection = useCallback((sectionId: string) => {
    if (!markdownContainerRef.current) return;

    const container = markdownContainerRef.current;
    const heading = container.querySelector(`[data-heading-id="${sectionId}"]`);

    if (heading) {
      const containerRect = container.getBoundingClientRect();
      const headingRect = heading.getBoundingClientRect();
      const scrollTop = container.scrollTop + headingRect.top - containerRect.top - 20;

      container.scrollTo({
        top: scrollTop,
        behavior: 'smooth'
      });

      setActiveSection(sectionId);
      window.location.hash = sectionId;
    }
  }, []);

  // Navigate to next/previous section
  const navigateToSection = useCallback((direction: 'next' | 'previous') => {
    const currentIndex = tableOfContents.findIndex(item => item.id === activeSection);

    if (direction === 'next' && currentIndex < tableOfContents.length - 1) {
      scrollToSection(tableOfContents[currentIndex + 1].id);
    } else if (direction === 'previous' && currentIndex > 0) {
      scrollToSection(tableOfContents[currentIndex - 1].id);
    }
  }, [activeSection, tableOfContents, scrollToSection]);

  // Handle initial scroll from URL hash
  useEffect(() => {
    const hash = window.location.hash.slice(1);
    if (hash && tableOfContents.some(item => item.id === hash)) {
      setTimeout(() => scrollToSection(hash), 100);
    }
  }, [tableOfContents, scrollToSection]);

  // Setup scroll listener
  useEffect(() => {
    const container = markdownContainerRef.current;
    if (!container) return;

    let scrollTimeout: ReturnType<typeof setTimeout>;
    const handleScroll = () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(handleMarkdownScroll, 50);
    };

    container.addEventListener('scroll', handleScroll);
    return () => {
      container.removeEventListener('scroll', handleScroll);
      clearTimeout(scrollTimeout);
    };
  }, [handleMarkdownScroll]);

  // Keyboard navigation for sections
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle if markdown tab is active and not editing
      if (activeTab !== 'markdown' || isEditingMarkdown) return;

      // Section navigation
      if (e.key === 'j' || (e.key === 'ArrowDown' && e.altKey)) {
        e.preventDefault();
        navigateToSection('next');
      } else if (e.key === 'k' || (e.key === 'ArrowUp' && e.altKey)) {
        e.preventDefault();
        navigateToSection('previous');
      } else if (e.key === 'g' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        // Go to top
        if (markdownContainerRef.current) {
          markdownContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
        }
      } else if (e.key === 'G' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        // Go to bottom
        if (markdownContainerRef.current) {
          const container = markdownContainerRef.current;
          container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
          });
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeTab, isEditingMarkdown, navigateToSection]);

  // Calculate reading time
  const calculateReadingTime = useCallback((content: string) => {
    const wordsPerMinute = 200;
    const words = content.trim().split(/\s+/).length;
    const minutes = Math.ceil(words / wordsPerMinute);
    return minutes;
  }, []);

  // Cleanup scroll timeout on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  // Memoized markdown chunk component for performance
  // Render a single markdown chunk with lazy loading
  const MarkdownChunk = React.memo(({ chunk, isLoaded }: {
    chunk: { id: string; content: string; startIndex: number; endIndex: number; headings: any[] };
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
                ? `http://localhost:8000${props.src}`
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

  const MemoizedMarkdownChunk = React.memo(({ content, chunkIndex }: { content: string; chunkIndex: number }) => (
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
            id={`heading-${chunkIndex}-${props.children?.toString().toLowerCase().replace(/\s+/g, '-') || ''}`}
            className="text-3xl font-bold text-gray-900 mt-8 mb-6 pb-3 border-b border-gray-200 scroll-mt-20"
            {...props}
          />
        ),
        h2: ({ node, ...props }) => (
          <h2
            id={`heading-${chunkIndex}-${props.children?.toString().toLowerCase().replace(/\s+/g, '-') || ''}`}
            className="text-2xl font-bold text-blue-900 mt-8 mb-4 scroll-mt-20"
            {...props}
          />
        ),
        h3: ({ node, ...props }) => (
          <h3
            id={`heading-${chunkIndex}-${props.children?.toString().toLowerCase().replace(/\s+/g, '-') || ''}`}
            className="text-xl font-bold text-gray-800 mt-6 mb-3 scroll-mt-20"
            {...props}
          />
        ),
        img: ({ node, ...props }) => (
          <img
            {...props}
            className="rounded-xl shadow-lg my-8 mx-auto max-w-full h-auto border border-gray-200"
            loading="lazy"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
            }}
          />
        ),
        pre: ({ node, ...props }) => (
          <pre
            className="bg-gray-900 text-gray-100 overflow-x-auto rounded-xl p-4 my-6 max-w-full shadow-lg"
            {...props}
          />
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  ));

  MemoizedMarkdownChunk.displayName = 'MemoizedMarkdownChunk';

  // Poll for status updates when processing is active
  useEffect(() => {
    if (isAnyProcessing) {
      const intervalId = setInterval(() => {
        loadPaperDetails();
      }, 10000); // Reduced frequency: 10s instead of 3s for better performance during analysis

      return () => {
        clearInterval(intervalId);
        console.log('Cleared paper polling interval');
      };
    }
  }, [isAnyProcessing, paperId]);

  // Handle markdown context menu
  const handleMarkdownContextMenu = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    // Get current selection
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.toString().trim()) {
      return;
    }

    const text = selection.toString().trim();
    setSelectedMarkdownText(text);
    selectedMarkdownTextRef.current = text;

    // Set context menu position
    const viewportHeight = window.innerHeight;
    const menuHeight = 200; // Approximate menu height

    let menuY = e.clientY;
    if (e.clientY + menuHeight > viewportHeight) {
      menuY = e.clientY - menuHeight;
    }

    setMarkdownContextMenuPosition({ x: e.clientX, y: menuY });
    setShowMarkdownContextMenu(true);
  }, []);

  const handleMarkdownMenuAction = (action: string) => {
    const text = selectedMarkdownTextRef.current;
    if (!text) return;

    switch (action) {
      case "copy":
        navigator.clipboard.writeText(text);
        break;
      case "snippet":
        // Set selected text for snippet creation
        setSelectedText(text);
        setActiveTab("snippets");
        break;
      case "highlight":
        // Could be extended to highlight in markdown
        console.log("Highlight:", text);
        break;
      case "tag":
        setMarkdownTagText(text.trim());
        setShowMarkdownTagDialog(true);
        break;
    }

    setShowMarkdownContextMenu(false);
  };

  const handleCreateMarkdownTag = async () => {
    if (!markdownTagText.trim() || !paper) return;

    setCreatingMarkdownTag(true);
    try {
      await axios.post(`http://localhost:8000/api/papers/${paper.id}/tags`, {
        tag: markdownTagText.trim(),
        tag_type: "manual",
      });

      // Update tags in local state without reloading entire paper
      setPaper((prev) =>
        prev
          ? {
              ...prev,
              tags: [...(prev.tags || []), markdownTagText.trim()],
            }
          : null,
      );
      setShowMarkdownTagDialog(false);
      setMarkdownTagText("");
    } catch (error) {
      console.error("Error creating markdown tag:", error);
    } finally {
      setCreatingMarkdownTag(false);
    }
  };

  const handleMarkdownTagDialogClose = () => {
    setShowMarkdownTagDialog(false);
    setMarkdownTagText("");
    setCreatingMarkdownTag(false);
  };

  // Close markdown context menu on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (showMarkdownContextMenu) {
        setShowMarkdownContextMenu(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showMarkdownContextMenu]);

  // Enhanced keyboard navigation - moved here to be before any conditional returns
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Global shortcuts
      if (e.key === "Escape" && onClose) {
        onClose();
        return;
      }

      // Only handle other shortcuts when not typing in inputs
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      // Tab navigation shortcuts
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case "1":
            e.preventDefault();
            setActiveTab("pdf");
            break;
          case "2":
            e.preventDefault();
            setActiveTab("markdown");
            break;
          case "3":
            e.preventDefault();
            setActiveTab("sections");
            break;
          case "4":
            e.preventDefault();
            setActiveTab("snippets");
            break;
          case "5":
            e.preventDefault();
            setActiveTab("analyses");
            break;
          case "t":
            e.preventDefault();
            setShowTagModal(true);
            break;
          case "e":
            e.preventDefault();
            if (paper?.content) {
              setShowEntityModal(true);
            }
            break;
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose, paper?.content]);

  // Early return after all hooks are declared to avoid hooks order issues
  const pollProcessingStatus = async () => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(
          `http://localhost:8000/api/papers/${paperId}`,
        );
        if (response.data.processed || response.data.processing_error) {
          setIsProcessing(false);
          setPaper(response.data);
          clearInterval(pollInterval);

          const contentResponse = await axios.get(
            `http://localhost:8000/api/papers/${paperId}/content`,
          );
          setPaper((prev) =>
            prev ? { ...prev, ...contentResponse.data } : null,
          );

          if (response.data.processed) {
            // Paper is processed, so PDF should be available
            setPdfAvailable(true);
          }
        }
      } catch (err: any) {
        console.error("Error polling processing status:", err);
        // Stop polling if we get a 404 (paper doesn't exist)
        if (err.response?.status === 404) {
          clearInterval(pollInterval);
          setIsProcessing(false);
          console.error(`Paper ${paperId} not found. Stopping polling.`);
        }
      }
    }, 3000);

    // Store interval ID for cleanup
    return pollInterval;
  };


  const handleCreateTagFromPDF = async (tagText: string) => {
    if (!paper) return;

    try {
      await axios.post(`http://localhost:8000/api/papers/${paper.id}/tags`, {
        tag: tagText,
        tag_type: "manual",
      });

      // Update tags in local state without reloading entire paper
      setPaper((prev) =>
        prev
          ? {
              ...prev,
              tags: [...(prev.tags || []), tagText],
            }
          : null,
      );
    } catch (error) {
      console.error("Error creating tag:", error);
      throw error;
    }
  };

  const handleAddTag = async () => {
    if (!newTag.trim() || !paper) return;

    setAddingTag(true);
    try {
      await axios.post(`http://localhost:8000/api/papers/${paperId}/tags`, {
        tag: newTag.trim(),
      });

      setPaper({
        ...paper,
        tags: [...(paper.tags || []), newTag.trim()],
      });
      setNewTag("");
    } catch (err) {
      console.error("Failed to add tag:", err);
    } finally {
      setAddingTag(false);
    }
  };

  const handleRemoveTag = async (tag: string) => {
    if (!paper) return;

    try {
      await axios.delete(
        `http://localhost:8000/api/papers/${paperId}/tags/${encodeURIComponent(tag)}`,
      );

      setPaper({
        ...paper,
        tags: (paper.tags || []).filter((t) => t !== tag),
      });
    } catch (err) {
      console.error("Failed to remove tag:", err);
    }
  };

  const handleCopyText = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(text);
    setTimeout(() => setCopiedText(null), 2000);
  };

  const handleCreateSnippet = async () => {
    if (!selectedText.trim()) return;

    setCreatingSnippet(true);
    try {
      const response = await axios.post(
        `http://localhost:8000/api/papers/${paperId}/snippets`,
        {
          content: selectedText,
          annotation: snippetAnnotation,
          category: snippetCategory,
          page_number: null,
        },
      );

      if (paper) {
        setPaper({
          ...paper,
          snippets: [...(paper.snippets || []), response.data],
        });
      }

      setSelectedText("");
      setSnippetAnnotation("");
      setSnippetCategory("");
    } catch (err) {
      console.error("Failed to create snippet:", err);
    } finally {
      setCreatingSnippet(false);
    }
  };

  const toggleSection = (sectionId: number) => {
    setExpandedSections(prev => {
      const newExpanded = new Set(prev);
      if (newExpanded.has(sectionId)) {
        newExpanded.delete(sectionId);
      } else {
        newExpanded.add(sectionId);
      }
      return newExpanded;
    });
  };

  // Enhanced loading state with skeleton
  if (loading) {
    return (
      <div className="h-[calc(100vh-4rem)] flex bg-gray-50">
        {/* Skeleton Sidebar */}
        <div className="w-[440px] bg-white border-r border-gray-200 p-4 space-y-4 animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-3/4"></div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-8 bg-gray-200 rounded"></div>
          </div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="flex flex-wrap gap-2">
              <div className="h-6 bg-gray-200 rounded w-16"></div>
              <div className="h-6 bg-gray-200 rounded w-20"></div>
              <div className="h-6 bg-gray-200 rounded w-12"></div>
            </div>
          </div>
        </div>

        {/* Skeleton Main Content */}
        <div className="flex-1 flex flex-col">
          <div className="p-4 border-b bg-white">
            <div className="h-6 bg-gray-200 rounded w-1/4 animate-pulse"></div>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full bg-white rounded-lg border p-6">
              <div className="space-y-4 animate-pulse">
                <div className="h-8 bg-gray-200 rounded w-full"></div>
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-full"></div>
                  <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                  <div className="h-4 bg-gray-200 rounded w-4/5"></div>
                </div>
                <div className="h-48 bg-gray-200 rounded"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Close button */}
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-50 bg-white/90 backdrop-blur-sm rounded-full p-2.5 shadow-lg hover:shadow-xl transition-all duration-200 group border border-gray-200"
            title="Close viewer (Esc)"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        )}
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="h-[calc(100vh-4rem)] flex items-center justify-center bg-white relative">
        <div className="max-w-md w-full px-6">
          <Alert variant="destructive" className="shadow-sm">
            <AlertDescription>
              {error || "Paper not found"}
            </AlertDescription>
          </Alert>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-50 bg-white/90 backdrop-blur-sm rounded-full p-2.5 shadow-lg hover:shadow-xl transition-all duration-200 group border border-gray-200"
            title="Close viewer (Esc)"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        )}
      </div>
    );
  }

  const handleExtractAuthors = async () => {
    if (!paper) return;

    setExtractingAuthors(true);
    try {
      const response = await axios.post(
        `http://localhost:8000/api/papers/${paperId}/extract-authors`,
        {
          use_full_content: false,
        },
      );

      if (response.data.success && response.data.authors) {
        // Update the paper with extracted authors
        setPaper({
          ...paper,
          authors: response.data.authors,
        });
        console.log(`Extracted ${response.data.authors.length} authors`);
      } else {
        console.error("Author extraction failed:", response.data.error);
        alert(
          `Failed to extract authors: ${response.data.error || "Unknown error"}`,
        );
      }
    } catch (err: any) {
      console.error("Failed to extract authors:", err);
      // Show more detailed error message
      const errorMsg =
        err.response?.data?.detail ||
        err.message ||
        "Failed to extract authors";
      alert(errorMsg);
    } finally {
      setExtractingAuthors(false);
    }
  };

  const handleExtractAffiliations = async () => {
    if (!paper) return;

    setExtractingAffiliations(true);
    setAffiliationSuggestions([]);
    setSelectedAffiliations(new Set());

    try {
      const response = await axios.post(
        `http://localhost:8000/api/papers/${paperId}/extract-affiliations`
      );

      if (response.data.suggestions && response.data.suggestions.length > 0) {
        setAffiliationSuggestions(response.data.suggestions);
        // Pre-select all suggestions by default
        const indices = new Set(response.data.suggestions.map((_: any, idx: number) => idx));
        setSelectedAffiliations(indices);
        setShowAffiliationDialog(true);
      } else {
        alert("No affiliations could be extracted from the paper header.");
      }
    } catch (err: any) {
      console.error("Failed to extract affiliations:", err);
      const errorMsg =
        err.response?.data?.detail ||
        err.message ||
        "Failed to extract affiliations";
      alert(errorMsg);
    } finally {
      setExtractingAffiliations(false);
    }
  };

  const handleApplyAffiliations = async () => {
    if (!paper || selectedAffiliations.size === 0) return;

    const affiliationsToApply = affiliationSuggestions
      .filter((_, idx) => selectedAffiliations.has(idx))
      .map((suggestion) => ({
        author_index: suggestion.author_index,
        affiliation: suggestion.suggested_affiliation,
      }));

    try {
      const response = await axios.put(
        `http://localhost:8000/api/papers/${paperId}/apply-affiliations`,
        {
          affiliations: affiliationsToApply,
        }
      );

      if (response.data.updated_count > 0) {
        // Update the paper with new authors data
        setPaper({
          ...paper,
          authors: response.data.authors,
        });
        alert(`Successfully updated ${response.data.updated_count} affiliations!`);
        setShowAffiliationDialog(false);
      } else {
        alert("No affiliations were updated.");
      }
    } catch (err: any) {
      console.error("Failed to apply affiliations:", err);
      alert("Failed to apply affiliations. Please try again.");
    }
  };

  const toggleAffiliationSelection = (index: number) => {
    const newSelection = new Set(selectedAffiliations);
    if (newSelection.has(index)) {
      newSelection.delete(index);
    } else {
      newSelection.add(index);
    }
    setSelectedAffiliations(newSelection);
  };

  const handleEditMetadata = () => {
    console.log("Edit metadata clicked");
    if (!paper) {
      console.log("No paper data");
      return;
    }

    // Convert publication_date to yyyy-MM-dd format for date input
    let formattedDate = "";
    if (paper.publication_date) {
      const date = new Date(paper.publication_date);
      if (!isNaN(date.getTime())) {
        formattedDate = date.toISOString().split('T')[0]; // Extract yyyy-MM-dd part
      }
    }

    // Handle authors from different sources (authors_detailed, authors_list, or authors string)
    let authorsList: Array<{ name: string; affiliation: string; email: string }> = [];
    if (Array.isArray(paper.authors_detailed) && paper.authors_detailed.length > 0) {
      // Papers with authors_detailed (GROBID, ACM with our fix)
      authorsList = paper.authors_detailed.map((a) => ({
        name: typeof a === 'string' ? a : (a.name || ''),
        affiliation: typeof a === 'object' ? (a.affiliation || "") : "",
        email: typeof a === 'object' ? (a.email || "") : "",
      }));
    } else if (Array.isArray(paper.authors_list) && paper.authors_list.length > 0) {
      // ACL Anthology papers with authors_list
      authorsList = paper.authors_list.map((a) => ({
        name: a.name || '',
        affiliation: a.affiliation || "",
        email: a.email || "",
      }));
    } else if (typeof paper.authors === "string" && paper.authors) {
      // Papers with comma-separated authors string
      authorsList = paper.authors.split(",").map((name) => ({
        name: name.trim(),
        affiliation: "",
        email: "",
      }));
    }

    setEditedMetadata({
      title: paper.title,
      abstract: paper.abstract || "",
      publication_date: formattedDate,
      conference: paper.conference || "",
      journal: paper.journal || "",
      arxiv_id: paper.arxiv_id || "",
      doi: paper.doi || "",
      authors: authorsList,
    });
    console.log("Opening metadata edit dialog");
    setEditingMetadata(true);
  };

  const handleSaveMetadata = async () => {
    if (!paper || !editedMetadata) return;

    try {
      const response = await axios.put(
        `http://localhost:8000/api/papers/${paperId}/metadata`,
        editedMetadata,
      );

      // Update the paper with new metadata
      setPaper({
        ...paper,
        ...response.data,
      });

      setEditingMetadata(false);
      setEditedMetadata(null);
      console.log("Metadata updated successfully");

      // Call the callback to refresh facets in parent component
      if (onMetadataUpdate) {
        onMetadataUpdate();
      }

      // After saving metadata, optionally process with GROBID for conclusion extraction
      // This could be done automatically or via a separate button
    } catch (err) {
      console.error("Failed to save metadata:", err);
    }
  };


  const handleEditSection = (section: PaperSection) => {
    setEditingSectionId(section.id);
    setEditedSectionContent(section.content);
  };

  const handleEditSectionTitle = (section: PaperSection) => {
    setEditingSectionTitleId(section.id);
    setEditedSectionTitle(section.title);
  };

  const handleSaveSectionTitle = async (sectionId: number) => {
    if (!paper || savingSection || !editedSectionTitle.trim()) return;
    setSavingSection(true);
    try {
      // Use the sections endpoint to update the title
      const response = await axios.put(
        `http://localhost:8000/api/papers/${paperId}/sections/${sectionId}`,
        {
          title: editedSectionTitle.trim(),
        },
      );
      if (response.data.success) {
        // Update local state
        const updatedSections = paper.sections?.map(s => 
          s.id === sectionId ? { ...s, title: editedSectionTitle.trim() } : s
        );
        setPaper({ ...paper, sections: updatedSections });
        setEditingSectionTitleId(null);
        setEditedSectionTitle("");
      }
    } catch (err: any) {
      console.error("Failed to save section title:", err);
      alert(
        "Failed to save section title: " +
          (err.response?.data?.detail || err.message)
      );
    } finally {
      setSavingSection(false);
    }
  };

  const handleCancelSectionTitleEdit = () => {
    setEditingSectionTitleId(null);
    setEditedSectionTitle("");
  };

  const handleSaveSection = async (sectionId: number) => {
    if (!paper || savingSection) return;

    setSavingSection(true);
    try {
      // Use the new sections endpoint for all section types
      const response = await axios.put(
        `http://localhost:8000/api/papers/${paperId}/sections/${sectionId}`,
        {
          content: editedSectionContent,
        },
      );

      if (response.data.success) {
        // Update local state
        if (sectionId === -1) {
          // Update abstract in paper
          setPaper((prev) => {
            if (!prev) return null;
            return {
              ...prev,
              abstract: editedSectionContent,
              sections: prev.sections?.map((s) =>
                s.id === -1 ? { ...s, content: editedSectionContent } : s,
              ),
            };
          });
        } else {
          // Update other sections
          setPaper((prev) => {
            if (!prev) return null;
            return {
              ...prev,
              sections: prev.sections?.map((s) =>
                s.id === sectionId
                  ? { ...s, content: editedSectionContent }
                  : s,
              ),
            };
          });
        }

        setEditingSectionId(null);
        setEditedSectionContent("");

        // Show success feedback
        console.log(
          `${response.data.section_type || "Section"} saved successfully`,
        );
      }
    } catch (err: any) {
      console.error("Failed to save section:", err);
      alert(
        "Failed to save section: " +
          (err.response?.data?.detail || err.message),
      );
    } finally {
      setSavingSection(false);
    }
  };

  const handleCancelSectionEdit = () => {
    setEditingSectionId(null);
    setEditedSectionContent("");
  };

  const handleExtractSections = async () => {
    if (!paper || extractingSections) return;

    setExtractingSections(true);
    try {
      const response = await axios.post(
        `http://localhost:8000/api/papers/${paperId}/extract-sections`
      );

      if (response.data.success) {
        // Reload paper to get the new sections
        await loadPaperDetails();
        
        const sectionsFound = response.data.sections_found;
        const extractedCount = response.data.sections_extracted;
        
        // Show success message
        let message = `Successfully extracted ${extractedCount} section${extractedCount !== 1 ? 's' : ''}`;
        if (response.data.conclusion_title && response.data.conclusion_title !== 'Conclusion') {
          message += ` (Conclusion found as "${response.data.conclusion_title}")`;
        }
        
        console.log(message);
        // You could also show a toast notification here if you have a toast library
        
        // Automatically expand the extracted sections
        if (paper.sections) {
          paper.sections.forEach(section => {
            setExpandedSections(prev => {
              const newSet = new Set(prev);
              newSet.add(section.id);
              return newSet;
            });
          });
        }
      }
    } catch (err: any) {
      console.error("Failed to extract sections:", err);
      alert(
        "Failed to extract sections: " +
          (err.response?.data?.detail || err.message)
      );
    } finally {
      setExtractingSections(false);
    }
  };

  const handleSaveMarkdown = async () => {
    setSavingMarkdown(true);
    try {
      await axios.put(`http://localhost:8000/api/papers/${paperId}/content`, {
        content: editedMarkdown,
      });
      setPaper((prev) =>
        prev
          ? {
              ...prev,
              markdown_content: editedMarkdown,
              content: editedMarkdown,
            }
          : null,
      );
      setIsEditingMarkdown(false);
      setEditedMarkdown("");
    } catch (err) {
      console.error("Failed to save markdown:", err);
    } finally {
      setSavingMarkdown(false);
    }
  };

  const handleSaveImportUrl = async () => {
    setSavingImportUrl(true);
    try {
      await axios.patch(`http://localhost:8000/api/papers/${paperId}`, {
        import_url: editedImportUrl,
      });
      setPaper((prev) =>
        prev
          ? {
              ...prev,
              import_url: editedImportUrl,
            }
          : null,
      );
      setEditingImportUrl(false);
    } catch (err) {
      console.error("Failed to save import URL:", err);
      alert("Failed to save import URL");
    } finally {
      setSavingImportUrl(false);
    }
  };

  // This check is now handled by the enhanced loading state above
  // Removed duplicate loading state for cleaner code

  return (
    <div className="h-[calc(100vh-4rem)] flex bg-gray-50 relative">
      {/* Modern Close Button */}
      {onClose && (
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-50 bg-white/90 backdrop-blur-sm rounded-full p-2.5 shadow-lg hover:shadow-xl transition-all duration-200 group border border-gray-200 hover:border-gray-300 hover:scale-105"
          title="Close viewer (Esc)"
        >
          <X className="w-5 h-5 text-gray-600 group-hover:text-gray-900 transition-colors" />
        </button>
      )}

      {error && (
        <div className="absolute top-4 left-1/2 z-40 w-full max-w-2xl -translate-x-1/2 px-4">
          <Alert variant="destructive" className="shadow-sm">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Enhanced Sidebar with Better Information Architecture */}
      <div
        className={cn(
          "bg-white border-r border-gray-200 transition-all duration-300 flex flex-col overflow-hidden shadow-sm",
          sidebarCollapsed ? "w-16" : "w-[440px]",
        )}
      >
        {/* Enhanced Sidebar Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-blue-50 to-indigo-50">
          {!sidebarCollapsed ? (
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-blue-600" />
              <h3 className="font-semibold text-sm text-gray-800">
                Paper Details
              </h3>
            </div>
          ) : (
            <FileText className="h-4 w-4 text-blue-600 mx-auto" />
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="hover:bg-white/60 transition-colors"
            title={sidebarCollapsed ? "Expand details" : "Collapse details"}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Scrollable Sidebar Content */}
        {!sidebarCollapsed && (
          <ScrollArea className="flex-1 overflow-x-hidden">
            <div className="p-4 space-y-4 pr-2">
              {/* Edit Button and Title */}
              <div className="space-y-2">
                <Button
                  size="sm"
                  variant="default"
                  onClick={handleEditMetadata}
                  className="w-fit bg-blue-600 hover:bg-blue-700 text-white"
                  title="Edit paper metadata"
                >
                  <Edit2 className="h-4 w-4 mr-1" />
                  Edit
                </Button>
                <h2 className="text-lg font-bold text-gray-900 leading-tight line-clamp-3">
                  {paper.title}
                </h2>
                {/* Quick Status Indicator */}
                <div className="flex items-center gap-2">
                  {paper.processed ? (
                    <Badge className="text-xs bg-green-100 text-green-800 border-green-300">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Processed
                    </Badge>
                  ) : (
                    <Badge
                      variant="outline"
                      className="text-xs bg-amber-50 text-amber-700 border-amber-300"
                    >
                      <Loader2 className="h-3 w-3 mr-1" />
                      Pending
                    </Badge>
                  )}
                  {paper.tags && paper.tags.length > 0 && (
                    <Badge variant="outline" className="text-xs">
                      <TagIcon className="h-3 w-3 mr-1" />
                      {paper.tags.length}
                    </Badge>
                  )}
                </div>
              </div>

              {/* Authors with Extract Buttons */}
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <User className="h-3 w-3" />
                    <span>Authors</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-1 justify-end">
                    {(!paper.authors ||
                      (typeof paper.authors === "string" &&
                        paper.authors.trim() === "")) && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={handleExtractAuthors}
                        disabled={extractingAuthors || !paper.content}
                        className="h-6 px-2 text-xs"
                        title={
                          !paper.content
                            ? "Paper must be processed first"
                            : "Extract authors from paper content"
                        }
                      >
                        {extractingAuthors ? "..." : "Extract"}
                      </Button>
                    )}
                    {paper.authors && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={handleExtractAffiliations}
                        disabled={extractingAffiliations}
                        className="h-6 px-2 text-xs"
                        title="Extract affiliations"
                      >
                        {extractingAffiliations ? "..." : "Affil."}
                      </Button>
                    )}
                  </div>
                </div>
                {(() => {
                  // Handle both string and array formats for authors
                  let authorsList = [];
                  
                  // First check for authors_detailed which contains affiliations
                  if (Array.isArray(paper.authors_detailed) && paper.authors_detailed.length > 0) {
                    // Use the detailed format which includes affiliations
                    authorsList = paper.authors_detailed;
                  } else if (typeof paper.authors === "string") {
                    // Simple string format - split by comma
                    authorsList = paper.authors
                      .split(",")
                      .map((name) => ({ name: name.trim() }));
                  } else if (Array.isArray(paper.authors)) {
                    // Array format - already structured
                    authorsList = paper.authors;
                  }
                  
                  // Check for affiliations in the paper object as fallback
                  const affiliations = paper.affiliations || [];
                  const affiliationMap = {};
                  
                  // Create a map of affiliations if they exist
                  if (Array.isArray(affiliations)) {
                    affiliations.forEach((aff, idx) => {
                      if (typeof aff === 'string') {
                        affiliationMap[idx] = aff;
                      } else if (aff && aff.name) {
                        affiliationMap[idx] = aff.name;
                      }
                    });
                  }

                  return authorsList.length > 0 ? (
                    <div className="text-sm text-gray-700 space-y-1.5">
                      {authorsList.map((author, idx) => {
                        // Determine the author name
                        let authorName = '';
                        if (typeof author === 'string') {
                          authorName = author;
                        } else if (author && typeof author === 'object') {
                          authorName = author.name || '';
                        }
                          
                        // Get affiliation for this author
                        let affiliation = null;
                        if (author && typeof author === 'object') {
                          if (author.affiliation) {
                            // Author has direct affiliation
                            affiliation = author.affiliation;
                          } else if (author.affiliation_index !== undefined && affiliationMap[author.affiliation_index]) {
                            // Author has affiliation index
                            affiliation = affiliationMap[author.affiliation_index];
                          } else if (affiliations.length === 1) {
                            // Only one affiliation for all authors
                            affiliation = typeof affiliations[0] === 'string' 
                              ? affiliations[0] 
                              : affiliations[0]?.name;
                          }
                        }
                        
                        // Only render if we have a valid author name
                        if (!authorName) return <React.Fragment key={idx} />;
                        
                        return (
                          <div key={idx} className="flex items-start gap-1">
                            <span className="font-medium text-gray-800">
                              {authorName}
                            </span>
                            {affiliation && (
                              <span className="text-xs text-gray-500 italic">
                                • {affiliation}
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-sm text-gray-400 italic">
                      No authors found. Click "Extract" to auto-detect.
                    </div>
                  );
                })()}
              </div>

              {/* Import Information */}
              {(paper.import_source || paper.import_url) && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                      <Download className="h-3 w-3" />
                      <span>Import Source</span>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditingImportUrl(!editingImportUrl)}
                      className="h-7 px-3 text-xs"
                    >
                      {editingImportUrl ? "Cancel" : "Edit"}
                    </Button>
                  </div>
                  
                  {!editingImportUrl ? (
                    <div className="space-y-1">
                      {paper.import_source && (
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {paper.import_source.toUpperCase()}
                          </Badge>
                        </div>
                      )}
                      {paper.import_url && (
                        <div className="group">
                          <a
                            href={paper.import_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:underline break-all line-clamp-2"
                            title={paper.import_url}
                          >
                            {paper.import_url}
                          </a>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <input
                        type="text"
                        value={editedImportUrl}
                        onChange={(e) => setEditedImportUrl(e.target.value)}
                        className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                        placeholder="Enter import URL"
                      />
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={handleSaveImportUrl}
                          disabled={savingImportUrl}
                          className="h-7 px-3 text-xs flex-1"
                        >
                          {savingImportUrl ? "Saving..." : "Save"}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setEditingImportUrl(false);
                            setEditedImportUrl(paper.import_url || '');
                          }}
                          className="h-7 px-3 text-xs flex-1"
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Publication Info - Compact */}
              <div className="space-y-3 text-sm">
                {paper.publication_date && (
                  <div className="flex items-center gap-2">
                    <Calendar className="h-3 w-3 text-gray-500 flex-shrink-0" />
                    <span className="text-sm text-gray-700">
                      {new Date(paper.publication_date).toLocaleDateString(
                        "en-US",
                        {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        },
                      )}
                    </span>
                  </div>
                )}

                {(paper.conference || paper.journal) && (
                  <div className="flex items-start gap-2">
                    <Building2 className="h-3 w-3 text-gray-500 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-gray-700 break-words">
                      {paper.conference || paper.journal}
                    </span>
                  </div>
                )}

                {paper.page_count > 0 && (
                  <div className="flex items-center gap-2">
                    <BookOpen className="h-3 w-3 text-gray-500 flex-shrink-0" />
                    <span className="text-gray-700">
                      {paper.page_count} pages
                    </span>
                  </div>
                )}

                {(paper.arxiv_id || paper.doi) && (
                  <div className="pt-1 space-y-1">
                    {paper.arxiv_id && (
                      <div className="flex items-center gap-2">
                        <ExternalLink className="h-3 w-3 text-gray-500 flex-shrink-0" />
                        <a
                          href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline text-xs"
                        >
                          arXiv:{paper.arxiv_id}
                        </a>
                      </div>
                    )}
                    {paper.doi && (
                      <div className="flex items-center gap-2">
                        <ExternalLink className="h-3 w-3 text-gray-500 flex-shrink-0" />
                        <a
                          href={`https://doi.org/${paper.doi}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline text-xs"
                        >
                          DOI:{paper.doi}
                        </a>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Enhanced Processing Status with Clear Actions */}
              <div className="bg-gray-50 rounded-lg p-3 border">
                <div className="flex items-center gap-2 mb-2">
                  <Cpu className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-gray-700">
                    Processing Status
                  </span>
                </div>
                {isProcessing ? (
                  <ProcessingTimer
                    startTime={processingStartTime || new Date()}
                    estimatedMinutes={10}
                    paperId={paperId}
                    onCheckStatus={async () => {
                      try {
                        const response = await axios.get(
                          `http://localhost:8000/api/papers/${paperId}`,
                        );
                        // Check if processing is complete (either processed or has error)
                        return (
                          response.data.processed ||
                          !!response.data.processing_error
                        );
                      } catch (error: any) {
                        // If paper doesn't exist (404), consider it complete to stop checking
                        if (error.response?.status === 404) {
                          return true;
                        }
                        return false;
                      }
                    }}
                    onCancel={async () => {
                      try {
                        const response = await axios.post(
                          `http://localhost:8000/api/papers/${paperId}/cancel-processing`,
                        );
                        if (response.data.success) {
                          setIsProcessing(false);
                          // Reload paper data to reflect cancellation
                          loadPaperDetails();
                        }
                      } catch (error) {
                        console.error("Failed to cancel processing:", error);
                      }
                    }}
                  />
                ) : (
                  <div className="space-y-1">
                    {paper.processed ? (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          {paper.processor_used === "marker_service" && (
                            <Badge className="text-xs bg-purple-100 text-purple-800 border-purple-300">
                              Marker
                            </Badge>
                          )}
                          {paper.processor_used === "mineru_service" && (
                            <Badge className="text-xs bg-blue-100 text-blue-800 border-blue-300">
                              MinerU
                            </Badge>
                          )}
                          {paper.processor_used === "pypdfium2" && (
                            <Badge className="text-xs bg-gray-100 text-gray-600 border-gray-300">
                              Basic
                            </Badge>
                          )}
                          {![
                            "marker_service",
                            "mineru_service",
                            "pypdfium2",
                          ].includes(paper.processor_used || "") &&
                            paper.processor_used && (
                              <Badge variant="outline" className="text-xs">
                                {paper.processor_used}
                              </Badge>
                            )}
                        </div>

                        {/* Reprocess Options */}
                        {!isProcessing && (
                          <div className="pt-2 border-t border-gray-200">
                            <div className="text-xs text-gray-500 mb-2">
                              Reprocess with different method:
                            </div>
                            <div className="flex flex-wrap gap-1">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setShowMarkerModal(true)}
                                className="h-6 px-2 text-xs bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-300"
                              >
                                <Cpu className="h-3 w-3 mr-1" />
                                Use Marker
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={async () => {
                                  try {
                                    const response = await axios.post(
                                      `http://localhost:8000/api/papers/${paperId}/process-with-mineru`,
                                    );
                                    if (response.data.success) {
                                      setPaper((prev) =>
                                        prev
                                          ? {
                                              ...prev,
                                              processing_status:
                                                "processing_with_mineru",
                                            }
                                          : null,
                                      );
                                    }
                                  } catch (error) {
                                    console.error(
                                      "Failed to start MinerU processing:",
                                      error,
                                    );
                                  }
                                }}
                                className="h-6 px-2 text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-300"
                              >
                                <GraduationCap className="h-3 w-3 mr-1" />
                                Use MinerU
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="flex items-center gap-2">
                          <div className="h-4 w-4 rounded-full bg-amber-100 flex items-center justify-center">
                            <div className="h-2 w-2 rounded-full bg-amber-500" />
                          </div>
                          <span className="text-sm font-medium text-amber-700">
                            Ready to Process
                          </span>
                        </div>
                        <p className="text-xs text-gray-600">
                          Choose a processing method to extract text and
                          structure:
                        </p>
                        {processingError && (
                          <Alert variant="destructive" className="mb-2">
                            <AlertDescription className="text-xs">
                              {processingError}
                            </AlertDescription>
                          </Alert>
                        )}
                        {!isProcessing && (
                          <div className="flex flex-wrap gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={async () => {
                                setProcessingError(null);
                                try {
                                  const response = await axios.post(
                                    `http://localhost:8000/api/papers/${paperId}/process-with-marker`,
                                  );
                                  if (response.data.success) {
                                    setPaper((prev) =>
                                      prev
                                        ? {
                                            ...prev,
                                            processing_status:
                                              "processing_with_marker",
                                          }
                                        : null,
                                    );
                                    // Don't reset loading state - let it be controlled by processing_status
                                  }
                                } catch (error: any) {
                                  console.error(
                                    "Failed to start Marker processing:",
                                    error,
                                  );
                                  setProcessingError(
                                    error.response?.data?.detail || 
                                    "Failed to start Marker processing. Please try again."
                                  );
                                  setTimeout(() => setProcessingError(null), 5000);
                                }
                              }}
                              disabled={processingWithMarker || processingWithMinerU || processingWithAuto}
                              className="h-6 px-2 text-xs bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-300 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {processingWithMarker ? (
                                <>
                                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                  Processing...
                                </>
                              ) : (
                                <>
                                  <Cpu className="h-3 w-3 mr-1" />
                                  Use Marker
                                </>
                              )}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={async () => {
                                setProcessingError(null);
                                try {
                                  const response = await axios.post(
                                    `http://localhost:8000/api/papers/${paperId}/process-with-mineru`,
                                  );
                                  if (response.data.success) {
                                    setPaper((prev) =>
                                      prev
                                        ? {
                                            ...prev,
                                            processing_status:
                                              "processing_with_mineru",
                                          }
                                        : null,
                                    );
                                    // Don't reset loading state - let it be controlled by processing_status
                                  }
                                } catch (error: any) {
                                  console.error(
                                    "Failed to start MinerU processing:",
                                    error,
                                  );
                                  setProcessingError(
                                    error.response?.data?.detail || 
                                    "Failed to start MinerU processing. Please try again."
                                  );
                                  setTimeout(() => setProcessingError(null), 5000);
                                }
                              }}
                              disabled={processingWithMarker || processingWithMinerU || processingWithAuto}
                              className="h-6 px-2 text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-300 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {processingWithMinerU ? (
                                <>
                                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                  Processing...
                                </>
                              ) : (
                                <>
                                  <GraduationCap className="h-3 w-3 mr-1" />
                                  Use MinerU
                                </>
                              )}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={async () => {
                                setProcessingError(null);
                                try {
                                  setIsProcessing(true);
                                  setProcessingStartTime(new Date());
                                  const response = await axios.post(
                                    `http://localhost:8000/api/papers/${paperId}/process`,
                                  );
                                  if (response.data.success) {
                                    // Processing started - now start polling for status
                                    console.log(
                                      "Processing started for paper",
                                      paperId,
                                    );
                                    const intervalId =
                                      await pollProcessingStatus();
                                    pollingIntervalRef.current = intervalId;
                                  }
                                } catch (error: any) {
                                  console.error(
                                    "Failed to start processing:",
                                    error,
                                  );
                                  setIsProcessing(false);
                                  setProcessingError(
                                    error.response?.data?.detail || 
                                    "Failed to start automatic processing. Please try again."
                                  );
                                  setTimeout(() => setProcessingError(null), 5000);
                                }
                              }}
                              disabled={processingWithMarker || processingWithMinerU || processingWithAuto}
                              className="h-6 px-2 text-xs disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {processingWithAuto ? (
                                <>
                                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                  Processing...
                                </>
                              ) : (
                                <>
                                  <PlayCircle className="h-3 w-3 mr-1" />
                                  Auto (Basic)
                                </>
                              )}
                            </Button>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Show retry button for errors */}
                    {paper && paper.processing_error && (
                      <div className="mt-2 space-y-1">
                        <p className="text-xs text-red-600">
                          {paper.processing_error.slice(0, 100)}...
                        </p>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={async () => {
                              try {
                                const response = await axios.post(
                                  `http://localhost:8000/api/papers/${paperId}/process-with-marker`,
                                );
                                if (response.data.success) {
                                  setPaper((prev) =>
                                    prev
                                      ? {
                                          ...prev,
                                          processing_status:
                                            "processing_with_marker",
                                        }
                                      : null,
                                  );
                                }
                              } catch (error) {
                                console.error(
                                  "Failed to retry with Marker:",
                                  error,
                                );
                              }
                            }}
                            className="h-6 px-2 text-xs"
                          >
                            <RotateCcw className="h-3 w-3 mr-1" />
                            Retry with Marker
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={async () => {
                              try {
                                const response = await axios.post(
                                  `http://localhost:8000/api/papers/${paperId}/process-with-mineru`,
                                );
                                if (response.data.success) {
                                  setPaper((prev) =>
                                    prev
                                      ? {
                                          ...prev,
                                          processing_status:
                                            "processing_with_mineru",
                                        }
                                      : null,
                                  );
                                }
                              } catch (error) {
                                console.error(
                                  "Failed to retry with MinerU:",
                                  error,
                                );
                              }
                            }}
                            className="h-6 px-2 text-xs"
                          >
                            <RotateCcw className="h-3 w-3 mr-1" />
                            Retry with MinerU
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* External Links with Better Accessibility */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 mb-2">
                  <ExternalLink className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-gray-700">
                    External Resources
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowDBLPModal(true)}
                    className={cn(
                      "h-8 px-3 text-xs bg-gray-50 hover:bg-gray-100 border-gray-300",
                      focusRingStyles,
                    )}
                    title="Search on DBLP for BibTeX and download links"
                  >
                    <Search className="h-3 w-3 mr-1" />
                    DBLP Search
                  </Button>
                  {paper.arxiv_id && (
                    <Button
                      size="sm"
                      variant="outline"
                      asChild
                      className={cn(
                        "h-8 px-3 text-xs bg-orange-50 hover:bg-orange-100 text-orange-700 border-orange-300",
                        focusRingStyles,
                      )}
                    >
                      <a
                        href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        aria-label={`Open arXiv paper ${paper.arxiv_id} in new tab`}
                      >
                        <ExternalLink className="h-3 w-3 mr-1" />
                        arXiv: {paper.arxiv_id}
                      </a>
                    </Button>
                  )}

                  {paper.doi && (
                    <Button
                      size="sm"
                      variant="outline"
                      asChild
                      className={cn(
                        "h-8 px-3 text-xs bg-green-50 hover:bg-green-100 text-green-700 border-green-300",
                        focusRingStyles,
                      )}
                    >
                      <a
                        href={`https://doi.org/${paper.doi}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        aria-label={`Open DOI ${paper.doi} in new tab`}
                      >
                        <ExternalLink className="h-3 w-3 mr-1" />
                        DOI: {paper.doi.slice(0, 20)}
                        {paper.doi.length > 20 ? "..." : ""}
                      </a>
                    </Button>
                  )}

                  {paper.openreview_url && (
                    <Button
                      size="sm"
                      variant="outline"
                      asChild
                      className={cn(
                        "h-8 px-3 text-xs bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-300",
                        focusRingStyles,
                      )}
                    >
                      <a
                        href={paper.openreview_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        aria-label="Open in OpenReview"
                      >
                        <ExternalLink className="h-3 w-3 mr-1" />
                        OpenReview
                      </a>
                    </Button>
                  )}
                </div>
              </div>


              {/* Enhanced Tags Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <TagIcon className="h-4 w-4 text-purple-600" />
                    <span className="text-sm font-medium text-gray-700">
                      Tags & Analysis
                    </span>
                  </div>
                </div>

                {/* Primary Action Buttons - Better contrast and spacing */}
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowTagModal(true)}
                    className="h-8 text-xs bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-300"
                  >
                    <Sparkles className="h-3 w-3 mr-2" />
                    Suggest Concept Tags
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowEntityModal(true)}
                    disabled={!paper?.content}
                    className="h-8 text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-300 disabled:opacity-60"
                    title={
                      !paper?.content
                        ? "Paper must be processed first"
                        : "Extract entities and add them as tags"
                    }
                  >
                    <Brain className="h-3 w-3 mr-2" />
                    Entity Extraction
                  </Button>
                </div>

                {/* Tags Display - Improved visibility and interaction */}
                <div className="space-y-2">
                  {(paper.tags || []).length > 0 ? (
                    <>
                      <div className="text-xs text-gray-500">
                        {paper.tags?.length || 0} tags assigned (click to edit)
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {(paper.tags || []).map((tag) => (
                          <Badge
                            key={tag}
                            variant="outline"
                            className="text-xs group border-blue-200 text-blue-800 bg-blue-50 hover:bg-blue-100 transition-all hover:shadow-sm cursor-pointer inline-flex items-center max-w-full"
                            onClick={() => {
                              setEditingConceptTag(tag);
                              setShowConceptEditModal(true);
                            }}
                            title={`Click to edit: ${tag}`}
                          >
                            <span className="break-words">
                              {tag}
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRemoveTag(tag);
                              }}
                              className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 hover:bg-red-100 rounded-full p-0.5"
                              title="Remove tag"
                              aria-label={`Remove tag ${tag}`}
                            >
                              <X className="h-2 w-2" />
                            </button>
                          </Badge>
                        ))}
                      </div>
                    </>
                  ) : (
                    <div className="text-xs text-gray-400 italic">
                      No tags assigned yet
                    </div>
                  )}
                </div>

                {/* Add New Tag - Improved UX */}
                <div className="flex items-center gap-2">
                  <Input
                    placeholder="Add tag..."
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === "Enter" && !addingTag && newTag.trim()) {
                        handleAddTag();
                      }
                    }}
                    className="h-8 text-xs flex-1"
                    disabled={addingTag}
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleAddTag}
                    disabled={addingTag || !newTag.trim()}
                    className="h-8 px-3 bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-300 disabled:opacity-60"
                    title="Add tag"
                  >
                    {addingTag ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Plus className="h-3 w-3" />
                    )}
                  </Button>
                </div>
              </div>
            </div>
            <div className="pb-6"></div>
          </ScrollArea>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Enhanced Header Bar with Keyboard Shortcuts */}
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {sidebarCollapsed && (
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-600" />
                <h2 className="text-lg font-semibold text-gray-900 truncate max-w-md">
                  {paper.title}
                </h2>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Keyboard shortcuts hint */}
            <div className="text-xs text-gray-500 hidden sm:flex items-center gap-2">
              <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">
                Ctrl+T
              </kbd>
              <span>Tags</span>
              <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">
                Ctrl+1-5
              </kbd>
              <span>Tabs</span>
            </div>
            {onClose && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                title="Close (Esc)"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Content Tabs - Full Height */}
        <div className="flex-1 flex flex-col">
          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="flex-1 flex flex-col"
          >
            {/* Improved Tab Navigation with Grouping */}
            <div className="mx-4 mt-2 space-y-2">
              {/* Primary Tabs - Core Content */}
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="pdf" className="flex items-center gap-2">
                  <FileText className="h-3 w-3" />
                  PDF
                </TabsTrigger>
                <TabsTrigger
                  value="markdown"
                  className="flex items-center gap-2"
                >
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
                <TabsTrigger
                  value="sections"
                  className="flex items-center gap-2"
                >
                  <Hash className="h-3 w-3" />
                  Sections
                </TabsTrigger>
                <TabsTrigger
                  value="snippets"
                  className="flex items-center gap-2"
                >
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
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger
                  value="analyses"
                  className="flex items-center gap-2"
                >
                  <Brain className="h-3 w-3" />
                  Analysis
                </TabsTrigger>
                <TabsTrigger
                  value="references"
                  className="flex items-center gap-2"
                >
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

            {/* Enhanced PDF Tab with Better Status Feedback */}
            <TabsContent value="pdf" className="flex-1 p-4">
              {pdfAvailable ? (
                <div className="h-full bg-white rounded-lg border overflow-hidden">
                  <PDFViewerModern
                    pdfUrl={`http://localhost:8000/api/papers/${paperId}/pdf`}
                    paperId={paperId}
                    onTextSelect={(text, pageNumber) => {
                      setSelectedText(text);
                      // Provide visual feedback for text selection
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

            {/* Enhanced Markdown Tab with Better Reading Experience */}
            <TabsContent value="markdown" className="flex-1 p-4">
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
                    {/* Reading mode controls */}
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
                          👁️
                        </Button>
                      </div>
                    )}
                    {/* Download button */}
                    {!isEditingMarkdown && (paper?.content || paper?.markdown_content) && (
                      <Button
                        onClick={async () => {
                          try {
                            const content = paper?.markdown_content || paper?.content || "";
                            const paperTitle = paper.title?.replace(/[^a-zA-Z0-9\s]/g, '').trim().substring(0, 50) || 'paper';
                            
                            // Create ZIP file
                            const zip = new JSZip();
                            
                            // Find all image references in markdown
                            const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
                            const images = [];
                            let match;
                            
                            while ((match = imageRegex.exec(content)) !== null) {
                              const imageUrl = match[2];
                              if (imageUrl.startsWith('/api/papers/')) {
                                images.push({
                                  alt: match[1],
                                  url: imageUrl,
                                  filename: imageUrl.split('/').pop() || 'image.png'
                                });
                              }
                            }
                            
                            // Download and add images to ZIP with better error handling
                            let updatedContent = content;
                            let successfulImages = 0;
                            let failedImages = 0;
                            
                            for (const img of images) {
                              try {
                                // Use fetch instead of axios for better CORS handling
                                const response = await fetch(`http://localhost:8000${img.url}`, {
                                  mode: 'cors',
                                  credentials: 'include'
                                });
                                
                                if (!response.ok) {
                                  throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                                }
                                
                                const blob = await response.blob();
                                
                                // Add image to ZIP in images folder
                                zip.file(`images/${img.filename}`, blob);
                                successfulImages++;
                                
                                // Update markdown to use relative path
                                updatedContent = updatedContent.replace(
                                  new RegExp(`!\\[${img.alt.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]\\(${img.url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\)`, 'g'),
                                  `![${img.alt}](images/${img.filename})`
                                );
                              } catch (error) {
                                console.warn(`Failed to download image: ${img.url}`, error);
                                failedImages++;
                                
                                // Keep original URL in markdown if download fails
                                updatedContent = updatedContent.replace(
                                  new RegExp(`!\\[${img.alt.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]\\(${img.url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\)`, 'g'),
                                  `![${img.alt}](http://localhost:8000${img.url}) <!-- Image download failed -->`
                                );
                              }
                            }
                            
                            // Add download summary to markdown
                            if (images.length > 0) {
                              const summaryNote = `\n\n---\n**Download Summary:** ${successfulImages} images included, ${failedImages} images failed to download.\n`;
                              updatedContent += summaryNote;
                            }
                            
                            // Add markdown file to ZIP
                            zip.file(`${paperTitle}.md`, updatedContent);
                            
                            // Generate and download ZIP
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
                        }}
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
                            className="prose prose-lg max-w-none overflow-hidden
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
                            prose-hr:border-gray-300 prose-hr:my-12"
                            style={{
                              maxWidth: "100%",
                              wordBreak: "break-word",
                              overflowWrap: "anywhere",
                              fontSize: "16px",
                              lineHeight: "1.75",
                            }}
                          >
                            {/* Render based on document size */}
                            {isLargeDocument ? (
                              // Large document - render chunks with lazy loading
                              // Each MarkdownChunk has its own ReactMarkdown internally
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
                              // Regular document - render all at once with ReactMarkdown wrapper
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
                                      ? `http://localhost:8000${props.src}`
                                      : props.src;
                                    // Use span instead of figure to avoid HTML nesting violations
                                    // when markdown has images inside paragraphs
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
                                            props.children?.props?.children;
                                          if (code) handleCopyText(code);
                                        }}
                                        className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity bg-gray-800 hover:bg-gray-700 text-gray-300 px-2 py-1 rounded text-xs"
                                      >
                                        {copiedText ===
                                        props.children?.props?.children ? (
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
                                  // Support for superscript tags
                                  sup: ({ node, ...props }) => (
                                    <sup {...props} className="text-xs align-super" />
                                  ),
                                  // Support for subscript tags
                                  sub: ({ node, ...props }) => (
                                    <sub {...props} className="text-xs align-sub" />
                                  ),
                                  // Support for span elements with IDs (jump targets)
                                  span: ({ node, id, ...props }) => (
                                    <span {...props} id={id} />
                                  ),
                                  // Enhanced anchor links for internal navigation
                                  a: ({ node, href, children, ...props }) => {
                                    // Check if it's an internal anchor link
                                    if (href && href.startsWith('#')) {
                                      return (
                                        <a
                                          {...props}
                                          href={href}
                                          onClick={(e) => {
                                            e.preventDefault();
                                            // Extract the anchor ID
                                            const targetId = href.substring(1);
                                            // Try to find the element by ID
                                            const targetElement = document.getElementById(targetId);
                                            if (targetElement) {
                                              targetElement.scrollIntoView({
                                                behavior: 'smooth',
                                                block: 'start'
                                              });
                                              // Briefly highlight the target
                                              targetElement.style.backgroundColor = '#fef3c7';
                                              setTimeout(() => {
                                                targetElement.style.backgroundColor = '';
                                              }, 2000);
                                            } else {
                                              // Try to find spans with matching ID patterns like page-x-y
                                              const allSpans = document.querySelectorAll('span[id]');
                                              for (const span of allSpans) {
                                                if (span.id === targetId) {
                                                  span.scrollIntoView({
                                                    behavior: 'smooth',
                                                    block: 'start'
                                                  });
                                                  // Briefly highlight the target
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
                                    // External links
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
                                  // Support for div elements with IDs (for section anchors)
                                  div: ({ node, id, className, ...props }) => (
                                    <div {...props} id={id} className={className} />
                                  ),
                                  // Handle <think> tags as literal text (for documentation about AI markup)
                                  think: ({ children }: { node?: unknown; children?: React.ReactNode }) => (
                                    <code className="text-pink-600 bg-pink-50 px-1.5 py-0.5 rounded font-mono text-sm">
                                      {'<think>'}
                                      {children}
                                      {'</think>'}
                                    </code>
                                  ),
                                } as Record<string, React.ComponentType<any>>}
                              >
                                {paper?.markdown_content || paper?.content || ''}
                              </ReactMarkdown>
                            )}

                            {/* Reading time estimate */}
                            {(paper?.markdown_content || paper?.content) && (
                              <div className="mt-8 pt-4 border-t border-gray-200 text-center text-sm text-gray-500">
                                Estimated reading time: {calculateReadingTime(paper?.markdown_content || paper?.content || '')} minutes
                              </div>
                            )}
                          </article>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center h-full">
                          <div className="text-center max-w-md">
                            <div className="mb-4">
                              {!paper.processed ? (
                                <Loader2 className="h-16 w-16 text-blue-500 mx-auto mb-6 animate-spin" />
                              ) : (
                                <FileCode className="h-16 w-16 text-gray-400 mx-auto mb-6" />
                              )}
                            </div>
                            <h3 className="text-xl font-semibold text-gray-700 mb-3">
                              {!paper.processed
                                ? "Processing Content..."
                                : "No Content Available"}
                            </h3>
                            <p className="text-gray-500 mb-6 leading-relaxed">
                              {!paper.processed
                                ? "The paper is being processed to extract readable content. This includes text extraction, formatting, and structure analysis."
                                : "No markdown content is available for this paper. Try processing it with an advanced method like Marker or MinerU for better text extraction."}
                            </p>
                            {!paper.processed ? (
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
                                      await axios.post(
                                        `http://localhost:8000/api/papers/${paperId}/process-with-marker`,
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
            </TabsContent>

            {/* Sections Tab with Markdown Rendering and Editing */}
            <TabsContent value="sections" className="flex-1 p-4">
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
                                  {section.section_type === "abstract" && "📄 "}
                                  {section.section_type === "conclusion" && "🎯 "}
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
                                      // Enhanced anchor links for internal navigation
                                      a: ({ node, href, children, ...props }) => {
                                        // Check if it's an internal anchor link
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
                                                  // Try to find spans with matching ID
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
                                        // External links
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
                                      // Support for superscript tags
                                      sup: ({ node, ...props }) => (
                                        <sup {...props} className="text-xs align-super" />
                                      ),
                                      // Support for subscript tags
                                      sub: ({ node, ...props }) => (
                                        <sub {...props} className="text-xs align-sub" />
                                      ),
                                      // Support for span elements with IDs (jump targets)
                                      span: ({ node, id, ...props }) => (
                                        <span {...props} id={id} />
                                      ),
                                      // Support for div elements with IDs (for section anchors)
                                      div: ({ node, id, className, ...props }) => (
                                        <div {...props} id={id} className={className} />
                                      ),
                                      // Handle <think> tags as literal text (for documentation about AI markup)
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
            </TabsContent>

            <TabsContent value="snippets" className="flex-1 p-4">
              <div className="h-full bg-white rounded-lg border">
                <ScrollArea className="h-full p-6">
                  {/* Snippet creation form */}
                  {selectedText && (
                    <Card className="mb-4">
                      <CardHeader>
                        <CardTitle className="text-sm">
                          Create Snippet
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div>
                          <label className="text-xs text-gray-500">
                            Selected Text
                          </label>
                          <div className="mt-1 p-2 bg-gray-50 rounded text-sm">
                            {selectedText}
                          </div>
                        </div>
                        <div>
                          <label className="text-xs text-gray-500">
                            Annotation
                          </label>
                          <Textarea
                            value={snippetAnnotation}
                            onChange={(e) =>
                              setSnippetAnnotation(e.target.value)
                            }
                            placeholder="Add your notes..."
                            className="mt-1"
                            rows={3}
                          />
                        </div>
                        <div>
                          <label className="text-xs text-gray-500">
                            Category
                          </label>
                          <Input
                            value={snippetCategory}
                            onChange={(e) => setSnippetCategory(e.target.value)}
                            placeholder="e.g., methodology, results"
                            className="mt-1"
                          />
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={handleCreateSnippet}
                            disabled={creatingSnippet}
                          >
                            {creatingSnippet ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              "Save Snippet"
                            )}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedText("");
                              setSnippetAnnotation("");
                              setSnippetCategory("");
                            }}
                          >
                            Cancel
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Existing snippets */}
                  {paper.snippets && paper.snippets.length > 0 ? (
                    <div className="space-y-3">
                      {paper.snippets.map((snippet) => (
                        <Card key={snippet.id}>
                          <CardContent className="pt-4">
                            <div className="space-y-2">
                              <p className="text-sm text-gray-700">
                                {snippet.content}
                              </p>
                              {snippet.annotation && (
                                <div className="pl-3 border-l-2 border-blue-200">
                                  <p className="text-sm text-gray-600">
                                    {snippet.annotation}
                                  </p>
                                </div>
                              )}
                              <div className="flex items-center gap-2">
                                {snippet.category && (
                                  <Badge
                                    variant="secondary"
                                    className="text-xs"
                                  >
                                    {snippet.category}
                                  </Badge>
                                )}
                                {snippet.page_number && (
                                  <span className="text-xs text-gray-500">
                                    Page {snippet.page_number}
                                  </span>
                                )}
                                <span className="text-xs text-gray-400">
                                  {new Date(
                                    snippet.created_at,
                                  ).toLocaleDateString()}
                                </span>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-500">No snippets yet</p>
                        <p className="text-sm text-gray-400 mt-2">
                          Select text from the PDF to create snippets
                        </p>
                      </div>
                    </div>
                  )}
                </ScrollArea>
              </div>
            </TabsContent>

            {/* Analyses Tab */}
            <TabsContent value="analyses" className="flex-1 p-4">
              <div className="h-full overflow-y-auto">
                <PaperAnalysisPanel
                  paperId={paperId}
                  paperTitle={paper.title}
                  onTagCreate={handleCreateTagFromPDF}
                  onSnippetCreate={(text) => {
                    setSelectedText(text);
                    setActiveTab("snippets");
                  }}
                />
              </div>
            </TabsContent>

            <TabsContent value="search" className="flex-1 p-4">
              <div className="h-full bg-white rounded-lg border p-6">
                <div className="space-y-4">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Search in paper..."
                      className="flex-1"
                    />
                    <Button>
                      <Search className="h-4 w-4 mr-2" />
                      Search
                    </Button>
                  </div>
                  <div className="text-center text-gray-500 mt-8">
                    Search functionality coming soon
                  </div>
                </div>
              </div>
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
                    // Reload paper data after metadata update
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
                  paperId={paper.id}
                  title={paper.title}
                  authors={paper.authors}
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
        </div>
      </div>

      {/* Markdown Context Menu Portal */}
      {showMarkdownContextMenu &&
        ReactDOM.createPortal(
          <div
            className="fixed z-[9999] bg-white rounded-lg shadow-2xl border border-gray-200 py-1 min-w-[180px]"
            style={{
              left: `${markdownContextMenuPosition.x}px`,
              top: `${markdownContextMenuPosition.y}px`,
            }}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-blue-50 flex items-center gap-2 transition-colors"
              onClick={() => handleMarkdownMenuAction("copy")}
            >
              <Copy className="h-4 w-4 text-blue-600" />
              <span>Copy Text</span>
            </button>

            <div className="border-t border-gray-100 my-1" />

            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-green-50 flex items-center gap-2 transition-colors"
              onClick={() => handleMarkdownMenuAction("snippet")}
            >
              <MessageSquare className="h-4 w-4 text-green-600" />
              <span>Create Snippet</span>
            </button>

            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-yellow-50 flex items-center gap-2 transition-colors"
              onClick={() => handleMarkdownMenuAction("highlight")}
            >
              <Highlighter className="h-4 w-4 text-yellow-600" />
              <span>Highlight</span>
            </button>

            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-purple-50 flex items-center gap-2 transition-colors"
              onClick={() => handleMarkdownMenuAction("tag")}
            >
              <TagIcon className="h-4 w-4 text-purple-600" />
              <span>Create Tag</span>
            </button>
          </div>,
          document.body,
        )}

      {/* Markdown Tag Creation Dialog */}
      <Dialog
        open={showMarkdownTagDialog}
        onOpenChange={handleMarkdownTagDialogClose}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <TagIcon className="h-5 w-5 text-purple-600" />
              Create Tag from Markdown
            </DialogTitle>
            <DialogDescription>
              Edit the selected text and create a tag for this paper.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label
                htmlFor="markdownTagText"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Tag Text
              </label>
              <Input
                id="markdownTagText"
                value={markdownTagText}
                onChange={(e) => setMarkdownTagText(e.target.value)}
                placeholder="Enter tag text..."
                className="w-full"
                onKeyPress={(e) => {
                  if (e.key === "Enter" && !creatingMarkdownTag) {
                    handleCreateMarkdownTag();
                  }
                }}
                disabled={creatingMarkdownTag}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={handleMarkdownTagDialogClose}
                disabled={creatingMarkdownTag}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateMarkdownTag}
                disabled={!markdownTagText.trim() || creatingMarkdownTag}
                className="bg-purple-600 hover:bg-purple-700"
              >
                {creatingMarkdownTag ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create Tag"
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Metadata Editing Dialog */}
      <Dialog open={editingMetadata} onOpenChange={setEditingMetadata}>
        <DialogContent className="max-w-3xl max-h-[90vh] sm:max-h-[80vh] overflow-y-auto p-4 sm:p-6">
          <DialogHeader>
            <DialogTitle>Edit Paper Metadata</DialogTitle>
            <DialogDescription>
              Update paper information and author details
            </DialogDescription>
          </DialogHeader>

          {editedMetadata && (
            <div className="space-y-6">
              {/* Title and Abstract Section */}
              <fieldset className="space-y-4">
                <legend className="text-base font-semibold sr-only">Basic Information</legend>
                
                {/* Title */}
                <div className="space-y-2">
                  <label htmlFor="paper-title" className="text-sm font-medium">
                    Title <span className="text-red-500">*</span>
                  </label>
                  <Input
                    id="paper-title"
                    value={editedMetadata.title}
                    onChange={(e) =>
                      setEditedMetadata({
                        ...editedMetadata,
                        title: e.target.value,
                      })
                    }
                    aria-required="true"
                    aria-describedby="title-help"
                  />
                  <p id="title-help" className="text-xs text-muted-foreground">
                    Enter the full paper title
                  </p>
                </div>

                {/* Abstract */}
                <div className="space-y-2">
                  <label htmlFor="paper-abstract" className="text-sm font-medium">
                    Abstract
                  </label>
                  <Textarea
                    id="paper-abstract"
                    value={editedMetadata.abstract}
                    onChange={(e) =>
                      setEditedMetadata({
                        ...editedMetadata,
                        abstract: e.target.value,
                      })
                    }
                    rows={4}
                    aria-describedby="abstract-help"
                    className="resize-y"
                  />
                  <p id="abstract-help" className="text-xs text-muted-foreground flex justify-between">
                    <span>Paper abstract or summary</span>
                    <span>{editedMetadata.abstract?.length || 0} characters</span>
                  </p>
                </div>
              </fieldset>

              {/* Publication Details Section */}
              <fieldset className="space-y-4 p-4 border rounded-lg">
                <legend className="text-base font-semibold px-2">Publication Details</legend>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label htmlFor="pub-date" className="text-sm font-medium">
                      Publication Date
                    </label>
                    <Input
                      id="pub-date"
                      type="date"
                      value={editedMetadata.publication_date}
                      onChange={(e) =>
                        setEditedMetadata({
                          ...editedMetadata,
                          publication_date: e.target.value,
                        })
                      }
                      aria-describedby="date-help"
                    />
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="conference" className="text-sm font-medium">
                      Conference
                    </label>
                    <Input
                      id="conference"
                      value={editedMetadata.conference}
                      onChange={(e) =>
                        setEditedMetadata({
                          ...editedMetadata,
                          conference: e.target.value,
                        })
                      }
                      placeholder="e.g., NeurIPS 2024"
                      aria-describedby="conference-help"
                    />
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="journal" className="text-sm font-medium">
                      Journal
                    </label>
                    <Input
                      id="journal"
                      value={editedMetadata.journal}
                      onChange={(e) =>
                        setEditedMetadata({
                          ...editedMetadata,
                          journal: e.target.value,
                        })
                      }
                      placeholder="e.g., Nature Machine Intelligence"
                      aria-describedby="journal-help"
                    />
                  </div>
                </div>
              </fieldset>

              {/* Identifiers Section */}
              <fieldset className="space-y-4 p-4 border rounded-lg">
                <legend className="text-base font-semibold px-2">Identifiers</legend>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label htmlFor="arxiv-id" className="text-sm font-medium">
                      ArXiv ID
                    </label>
                    <Input
                      id="arxiv-id"
                      value={editedMetadata.arxiv_id}
                      onChange={(e) =>
                        setEditedMetadata({
                          ...editedMetadata,
                          arxiv_id: e.target.value,
                        })
                      }
                      placeholder="e.g., 2301.12345"
                      aria-describedby="arxiv-help"
                    />
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="doi" className="text-sm font-medium">
                      DOI
                    </label>
                    <Input
                      id="doi"
                      value={editedMetadata.doi}
                      onChange={(e) =>
                        setEditedMetadata({
                          ...editedMetadata,
                          doi: e.target.value,
                        })
                      }
                      placeholder="e.g., 10.1234/journal.2024"
                      aria-describedby="doi-help"
                    />
                  </div>
                </div>
              </fieldset>

              {/* Authors Section */}
              <fieldset className="space-y-4 p-4 border rounded-lg">
                <legend className="text-base font-semibold px-2 flex items-center justify-between w-full">
                  <span>Authors</span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setEditedMetadata({
                        ...editedMetadata,
                        authors: [
                          ...editedMetadata.authors,
                          { name: "", affiliation: "", email: "" },
                        ],
                      });
                    }}
                    aria-label="Add new author"
                  >
                    <Plus className="h-3 w-3 mr-1" />
                    Add Author
                  </Button>
                </legend>

                <div className="space-y-3" role="list" aria-label="Author list">
                  {editedMetadata.authors.map((author: any, idx: number) => (
                    <div 
                      key={idx} 
                      className="p-4 border rounded-lg space-y-3 bg-gray-50/50"
                      role="listitem"
                      aria-label={`Author ${idx + 1}`}
                    >
                      <div className="flex items-center gap-3">
                        {/* Author order controls with better touch targets */}
                        <div className="flex flex-col gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-11 w-11 p-0 touch-manipulation hover:bg-gray-200"
                            onClick={() => {
                              if (idx > 0) {
                                const newAuthors = [...editedMetadata.authors];
                                [newAuthors[idx - 1], newAuthors[idx]] = [newAuthors[idx], newAuthors[idx - 1]];
                                setEditedMetadata({
                                  ...editedMetadata,
                                  authors: newAuthors,
                                });
                              }
                            }}
                            disabled={idx === 0}
                            aria-label={`Move ${author.name || 'author ' + (idx + 1)} up in order`}
                          >
                            <ChevronUp className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-11 w-11 p-0 touch-manipulation hover:bg-gray-200"
                            onClick={() => {
                              if (idx < editedMetadata.authors.length - 1) {
                                const newAuthors = [...editedMetadata.authors];
                                [newAuthors[idx], newAuthors[idx + 1]] = [newAuthors[idx + 1], newAuthors[idx]];
                                setEditedMetadata({
                                  ...editedMetadata,
                                  authors: newAuthors,
                                });
                              }
                            }}
                            disabled={idx === editedMetadata.authors.length - 1}
                            aria-label={`Move ${author.name || 'author ' + (idx + 1)} down in order`}
                          >
                            <ChevronDown className="h-4 w-4" />
                          </Button>
                        </div>
                        
                        {/* Author position indicator */}
                        <div 
                          className="text-lg font-bold text-blue-600 w-8 text-center"
                          aria-label={`Position ${idx + 1}`}
                        >
                          {idx + 1}
                        </div>
                        
                        <div className="flex-1 space-y-2">
                          <label htmlFor={`author-name-${idx}`} className="sr-only">
                            Author {idx + 1} name
                          </label>
                          <Input
                            id={`author-name-${idx}`}
                            value={author.name}
                            onChange={(e) => {
                              const newAuthors = [...editedMetadata.authors];
                              newAuthors[idx].name = e.target.value;
                              setEditedMetadata({
                                ...editedMetadata,
                                authors: newAuthors,
                              });
                            }}
                            placeholder="Author name"
                            aria-required="true"
                            aria-describedby={`author-${idx}-help`}
                          />
                        </div>
                        
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-11 w-11 p-0 touch-manipulation hover:bg-red-100"
                          onClick={() => {
                            const newAuthors = editedMetadata.authors.filter(
                              (_: any, i: number) => i !== idx,
                            );
                            setEditedMetadata({
                              ...editedMetadata,
                              authors: newAuthors,
                            });
                          }}
                          aria-label={`Remove ${author.name || 'author ' + (idx + 1)}`}
                        >
                          <X className="h-4 w-4 text-red-600" />
                        </Button>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pl-[104px]">
                        <div className="space-y-1">
                          <label htmlFor={`author-affiliation-${idx}`} className="text-xs font-medium text-gray-600">
                            Affiliation
                          </label>
                          <Input
                            id={`author-affiliation-${idx}`}
                            value={author.affiliation}
                            onChange={(e) => {
                              const newAuthors = [...editedMetadata.authors];
                              newAuthors[idx].affiliation = e.target.value;
                              setEditedMetadata({
                                ...editedMetadata,
                                authors: newAuthors,
                              });
                            }}
                            placeholder="Institution/Organization"
                            aria-describedby={`affiliation-${idx}-help`}
                          />
                        </div>
                        
                        <div className="space-y-1">
                          <label htmlFor={`author-email-${idx}`} className="text-xs font-medium text-gray-600">
                            Email (optional)
                          </label>
                          <Input
                            id={`author-email-${idx}`}
                            value={author.email}
                            onChange={(e) => {
                              const newAuthors = [...editedMetadata.authors];
                              newAuthors[idx].email = e.target.value;
                              setEditedMetadata({
                                ...editedMetadata,
                                authors: newAuthors,
                              });
                            }}
                            placeholder="author@example.com"
                            type="email"
                            aria-describedby={`email-${idx}-help`}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {editedMetadata.authors.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No authors added yet. Click "Add Author" to start.
                  </p>
                )}
              </fieldset>

              {/* Action Buttons with improved layout */}
              <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 pt-6 border-t">
                <Button
                  variant="outline"
                  onClick={() => {
                    setEditingMetadata(false);
                    setEditedMetadata(null);
                  }}
                  aria-label="Cancel and close dialog"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleSaveMetadata}
                  aria-label="Save metadata changes"
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Save Changes
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Tag Management Modal */}
      {paper && (
        <PaperTagSuggestionModal
          paper={paper}
          isOpen={showTagModal}
          onClose={() => setShowTagModal(false)}
          onTagsUpdated={(updatedTags: string[]) => {
            // Update tags in local state without reloading entire paper
            setPaper((prev) =>
              prev
                ? {
                    ...prev,
                    tags: updatedTags,
                  }
                : null,
            );

            // Notify parent component to update the paper tile
            if (onMetadataUpdate) {
              onMetadataUpdate();
            }
          }}
        />
      )}

      {/* Entity Annotation Modal */}
      {showEntityModal && paper && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-auto">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="text-lg font-semibold">
                Entity Annotation Review
              </h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowEntityModal(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="p-4">
              <PaperEntityAnnotationReview
                paperId={paper.id}
                onComplete={() => {
                  setShowEntityModal(false);
                  // Just reload tags without full paper reload - entity annotation adds tags
                  axios
                    .get(`http://localhost:8000/api/papers/${paper.id}`)
                    .then((response) => {
                      setPaper((prev) =>
                        prev
                          ? {
                              ...prev,
                              tags: response.data.tags,
                            }
                          : null,
                      );

                      // Notify parent component to update the paper tile
                      if (onMetadataUpdate) {
                        onMetadataUpdate();
                      }
                    })
                    .catch((err) =>
                      console.error("Error reloading tags:", err),
                    );
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* DBLP Search Modal */}
      {paper && (
        <DBLPSearchModal
          isOpen={showDBLPModal}
          onClose={() => {
            setShowDBLPModal(false);
            // Refresh paper data to show updated metadata
            loadPaperDetails();
            // Also notify parent about metadata update
            if (onMetadataUpdate) {
              onMetadataUpdate();
            }
          }}
          initialTitle={paper.title}
          paperId={paper.id}
          hasExistingMetadata={!!paper.dblp_key}
        />
      )}

      {/* Affiliation Extraction Dialog */}
      <Dialog open={showAffiliationDialog} onOpenChange={setShowAffiliationDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Review Extracted Affiliations</DialogTitle>
            <DialogDescription>
              The AI has extracted the following affiliations from the paper header. 
              Select which affiliations you want to apply to each author.
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="flex-1 pr-4">
            <div className="space-y-4">
              {affiliationSuggestions.map((suggestion, idx) => (
                <div 
                  key={idx} 
                  className="border rounded-lg p-4 space-y-2"
                >
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={selectedAffiliations.has(idx)}
                      onChange={() => toggleAffiliationSelection(idx)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-sm">
                        {suggestion.author_name}
                      </div>
                      {suggestion.current_affiliation && (
                        <div className="text-xs text-gray-500 mt-1">
                          Current: {suggestion.current_affiliation}
                        </div>
                      )}
                      <div className="text-sm text-blue-600 mt-2">
                        Suggested: {suggestion.suggested_affiliation}
                      </div>
                      <Badge 
                        variant={
                          suggestion.confidence === 'high' 
                            ? 'default' 
                            : suggestion.confidence === 'medium' 
                              ? 'secondary' 
                              : 'outline'
                        }
                        className="mt-2"
                      >
                        {suggestion.confidence} confidence
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
          <div className="flex justify-between items-center mt-4 pt-4 border-t">
            <div className="text-sm text-gray-500">
              {selectedAffiliations.size} of {affiliationSuggestions.length} selected
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setShowAffiliationDialog(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleApplyAffiliations}
                disabled={selectedAffiliations.size === 0}
              >
                Apply Selected
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Marker Progress Modal */}
      <MarkerProgressModal
        isOpen={showMarkerModal}
        onClose={() => setShowMarkerModal(false)}
        paperId={paperId}
        paperTitle={paper?.title}
        onSuccess={() => {
          setShowMarkerModal(false);
          loadPaperDetails(); // Refresh paper data
        }}
      />
      
      {/* Concept Edit Modal */}
      {editingConceptTag && (
        <ConceptEditModal
          tagName={editingConceptTag}
          isOpen={showConceptEditModal}
          onClose={() => {
            setShowConceptEditModal(false);
            setEditingConceptTag(null);
          }}
          onUpdate={() => {
            // Optionally refresh paper details if needed
            // loadPaperDetails();
          }}
        />
      )}
    </div>
  );
};

export default PaperViewerOptimized;
