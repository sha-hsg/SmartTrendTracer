import React from "react";
import {
  User,
  Calendar,
  Building2,
  BookOpen,
  Tag as TagIcon,
  ExternalLink,
  Download,
  Search,
  CheckCircle,
  Loader2,
  Edit2,
  Star,
  Flag,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import PaperProcessingSection from "./PaperProcessingSection";
import type { Paper, PaperAuthor } from "./types";

const focusRingStyles =
  "focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2";

export interface PaperMetadataSectionProps {
  paper: Paper;
  paperId: string | number;
  isProcessing: boolean;
  setIsProcessing: (processing: boolean) => void;
  processingStartTime: Date | null;
  setProcessingStartTime: (time: Date | null) => void;
  processingError: string | null;
  setProcessingError: (error: string | null) => void;
  processingWithMarker: boolean;
  processingWithMinerU: boolean;
  processingWithAuto: boolean;
  isAnyProcessing: boolean;
  extractingAuthors: boolean;
  extractingAffiliations: boolean;
  editingImportUrl: boolean;
  setEditingImportUrl: (editing: boolean) => void;
  editedImportUrl: string;
  setEditedImportUrl: (url: string) => void;
  savingImportUrl: boolean;
  setPaper: React.Dispatch<React.SetStateAction<Paper | null>>;
  handleEditMetadata: () => void;
  handleToggleFlag: () => void;
  handleSetRating: (rating: number | null) => void;
  handleExtractAuthors: () => void;
  handleExtractAffiliations: () => void;
  handleSaveImportUrl: () => void;
  setShowDBLPModal: (show: boolean) => void;
  setShowMarkerModal: (show: boolean) => void;
  loadPaperDetails: () => void;
  pollProcessingStatus: () => Promise<ReturnType<typeof setInterval>>;
  pollingIntervalRef: React.MutableRefObject<ReturnType<typeof setInterval> | null>;
}

const renderAuthors = (paper: Paper) => {
  let authorsList: Array<PaperAuthor | { name: string; affiliation?: string; affiliation_index?: number }> = [];

  if (Array.isArray(paper.authors_detailed) && paper.authors_detailed.length > 0) {
    authorsList = paper.authors_detailed;
  } else if (typeof paper.authors === "string") {
    authorsList = paper.authors.split(",").map((name) => ({ name: name.trim() }));
  } else if (Array.isArray(paper.authors)) {
    authorsList = paper.authors;
  }

  const affiliations = paper.affiliations || [];
  const affiliationMap: Record<number, string> = {};
  if (Array.isArray(affiliations)) {
    affiliations.forEach((aff, idx) => {
      if (typeof aff === "string") affiliationMap[idx] = aff;
      else if (aff && aff.name) affiliationMap[idx] = aff.name;
    });
  }

  return authorsList.length > 0 ? (
    <div className="text-sm text-gray-700 space-y-1.5">
      {authorsList.map((author, idx) => {
        let authorName = "";
        if (typeof author === "string") authorName = author;
        else if (author && typeof author === "object") authorName = author.name || "";

        let affiliation = null;
        if (author && typeof author === "object") {
          if (author.affiliation) {
            affiliation = author.affiliation;
          } else if (author.affiliation_index !== undefined && affiliationMap[author.affiliation_index]) {
            affiliation = affiliationMap[author.affiliation_index];
          } else if (affiliations.length === 1) {
            affiliation = typeof affiliations[0] === "string" ? affiliations[0] : affiliations[0]?.name;
          }
        }

        if (!authorName) return <React.Fragment key={idx} />;

        return (
          <div key={idx} className="flex items-start gap-1">
            <span className="font-medium text-gray-800">{authorName}</span>
            {affiliation && (
              <span className="text-xs text-gray-500 italic">• {affiliation}</span>
            )}
          </div>
        );
      })}
    </div>
  ) : (
    <div className="text-sm text-gray-400 italic">
      No authors found. Click &quot;Extract&quot; to auto-detect.
    </div>
  );
};

const PaperMetadataSection: React.FC<PaperMetadataSectionProps> = ({
  paper,
  paperId,
  isProcessing,
  setIsProcessing,
  processingStartTime,
  setProcessingStartTime,
  processingError,
  setProcessingError,
  processingWithMarker,
  processingWithMinerU,
  processingWithAuto,
  isAnyProcessing,
  extractingAuthors,
  extractingAffiliations,
  editingImportUrl,
  setEditingImportUrl,
  editedImportUrl,
  setEditedImportUrl,
  savingImportUrl,
  setPaper,
  handleEditMetadata,
  handleToggleFlag,
  handleSetRating,
  handleExtractAuthors,
  handleExtractAffiliations,
  handleSaveImportUrl,
  setShowDBLPModal,
  setShowMarkerModal,
  loadPaperDetails,
  pollProcessingStatus,
  pollingIntervalRef,
}) => {
  return (
    <>
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
            <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-300">
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

        {/* Flag and Rating Controls */}
        <div className="flex items-center gap-3 mt-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleToggleFlag}
            className={`h-7 px-2 ${paper.flagged ? "text-red-600 bg-red-50 hover:bg-red-100" : "text-gray-400 hover:text-red-500 hover:bg-red-50"}`}
            title={paper.flagged ? "Remove flag" : "Flag this paper"}
          >
            <Flag className={`h-4 w-4 ${paper.flagged ? "fill-current" : ""}`} />
          </Button>
          <div className="flex items-center gap-0.5">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => handleSetRating(star)}
                className={`p-0.5 transition-colors ${
                  paper.rating && star <= paper.rating
                    ? "text-yellow-400"
                    : "text-gray-300 hover:text-yellow-300"
                }`}
                title={`Rate ${star} star${star > 1 ? "s" : ""}`}
              >
                <Star className={`h-4 w-4 ${paper.rating && star <= paper.rating ? "fill-current" : ""}`} />
              </button>
            ))}
            {paper.rating && (
              <button
                onClick={() => handleSetRating(null)}
                className="ml-1 text-xs text-gray-400 hover:text-gray-600"
                title="Clear rating"
              >
                ×
              </button>
            )}
          </div>
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
            {(!paper.authors || (typeof paper.authors === "string" && paper.authors.trim() === "")) && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleExtractAuthors}
                disabled={extractingAuthors || !paper.content}
                className="h-6 px-2 text-xs"
                title={!paper.content ? "Paper must be processed first" : "Extract authors from paper content"}
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
        {renderAuthors(paper)}
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
                    setEditedImportUrl(paper.import_url || "");
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
              {new Date(paper.publication_date).toLocaleDateString("en-US", {
                year: "numeric",
                month: "short",
                day: "numeric",
              })}
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
            <span className="text-gray-700">{paper.page_count} pages</span>
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

      <PaperProcessingSection
        paper={paper}
        paperId={paperId}
        isProcessing={isProcessing}
        setIsProcessing={setIsProcessing}
        processingStartTime={processingStartTime}
        setProcessingStartTime={setProcessingStartTime}
        processingError={processingError}
        setProcessingError={setProcessingError}
        processingWithMarker={processingWithMarker}
        processingWithMinerU={processingWithMinerU}
        processingWithAuto={processingWithAuto}
        isAnyProcessing={isAnyProcessing}
        setPaper={setPaper}
        setShowMarkerModal={setShowMarkerModal}
        loadPaperDetails={loadPaperDetails}
        pollProcessingStatus={pollProcessingStatus}
        pollingIntervalRef={pollingIntervalRef}
      />

      {/* External Links */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 mb-2">
          <ExternalLink className="h-4 w-4 text-blue-600" />
          <span className="text-sm font-medium text-gray-700">External Resources</span>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowDBLPModal(true)}
            className={cn("h-8 px-3 text-xs bg-gray-50 hover:bg-gray-100 border-gray-300", focusRingStyles)}
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
                focusRingStyles
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
                focusRingStyles
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
                focusRingStyles
              )}
            >
              <a href={paper.openreview_url} target="_blank" rel="noopener noreferrer" aria-label="Open in OpenReview">
                <ExternalLink className="h-3 w-3 mr-1" />
                OpenReview
              </a>
            </Button>
          )}
        </div>
      </div>
    </>
  );
};

export default PaperMetadataSection;
