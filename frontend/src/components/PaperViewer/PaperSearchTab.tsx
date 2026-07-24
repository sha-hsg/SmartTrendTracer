import React, { useState } from "react";
import { Search, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export interface SearchMatch {
  /** 0-based occurrence index of this match within the content */
  index: number;
  /** Character offset in the raw content */
  position: number;
  before: string;
  match: string;
  after: string;
}

interface PaperSearchTabProps {
  content: string;
  onNavigateToMatch: (match: SearchMatch, query: string) => void;
}

const MAX_MATCHES = 300;
const CONTEXT_CHARS = 80;

/**
 * Simple client-side full-text search over the loaded markdown content.
 * Case-insensitive; shows context snippets and lets the user jump to a match
 * in the Content tab.
 */
const PaperSearchTab: React.FC<PaperSearchTabProps> = ({
  content,
  onNavigateToMatch,
}) => {
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState<SearchMatch[] | null>(null);
  const [searchedQuery, setSearchedQuery] = useState("");
  const [truncated, setTruncated] = useState(false);

  const runSearch = () => {
    const q = query.trim();
    if (q.length < 2) {
      setMatches(null);
      setSearchedQuery("");
      setTruncated(false);
      return;
    }

    const haystack = content.toLowerCase();
    const needle = q.toLowerCase();
    const found: SearchMatch[] = [];
    let pos = haystack.indexOf(needle);
    let wasTruncated = false;

    while (pos !== -1) {
      if (found.length >= MAX_MATCHES) {
        wasTruncated = true;
        break;
      }
      found.push({
        index: found.length,
        position: pos,
        before: content.slice(Math.max(0, pos - CONTEXT_CHARS), pos),
        match: content.slice(pos, pos + q.length),
        after: content.slice(pos + q.length, pos + q.length + CONTEXT_CHARS),
      });
      pos = haystack.indexOf(needle, pos + needle.length);
    }

    setMatches(found);
    setSearchedQuery(q);
    setTruncated(wasTruncated);
  };

  if (!content) {
    return (
      <div className="h-full bg-white rounded-lg border p-6 flex items-center justify-center">
        <div className="text-center text-gray-500">
          <FileText className="h-10 w-10 mx-auto mb-3 text-gray-300" />
          <p className="font-medium">No content available to search</p>
          <p className="text-sm mt-1">
            Process the paper first to enable full-text search.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-white rounded-lg border p-6 flex flex-col">
      <div className="space-y-4 flex-1 flex flex-col min-h-0">
        <div className="flex gap-2">
          <Input
            placeholder="Search in paper..."
            className="flex-1"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") runSearch();
            }}
          />
          <Button onClick={runSearch} disabled={query.trim().length < 2}>
            <Search className="h-4 w-4 mr-2" />
            Search
          </Button>
        </div>

        {matches !== null && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Badge variant="secondary">
              {matches.length}
              {truncated ? "+" : ""} match{matches.length !== 1 ? "es" : ""}
            </Badge>
            <span>for &ldquo;{searchedQuery}&rdquo;</span>
            {matches.length > 0 && (
              <span className="text-gray-400">
                &mdash; click a result to jump to it in the Content tab
              </span>
            )}
          </div>
        )}

        {matches === null ? (
          <div className="text-center text-gray-500 mt-8">
            Enter at least 2 characters and press Enter to search the paper
            content.
          </div>
        ) : matches.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            No matches found.
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
            {matches.map((m) => (
              <button
                key={`${m.position}`}
                onClick={() => onNavigateToMatch(m, searchedQuery)}
                className="w-full text-left p-3 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors text-sm"
              >
                <span className="text-gray-500">
                  &hellip;{m.before.replace(/\s+/g, " ")}
                </span>
                <mark className="bg-yellow-200 font-medium px-0.5 rounded">
                  {m.match}
                </mark>
                <span className="text-gray-500">
                  {m.after.replace(/\s+/g, " ")}&hellip;
                </span>
              </button>
            ))}
            {truncated && (
              <p className="text-xs text-gray-400 text-center py-2">
                Showing the first {MAX_MATCHES} matches. Refine your search to
                see more specific results.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PaperSearchTab;
