import React, { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, RefreshCcw, Check, Plus, Sparkles, Hash, Tags, Info, LoaderCircle } from "lucide-react";

// shadcn/ui
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

// ------------------------------------------------------
// Types
// ------------------------------------------------------
interface TagSuggestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  tweet: {
    id: string;
    text: string;
    author_username: string;
    tags: { tag: string; type: string }[];
  } | null;
  onTagsApplied: (
    tweetId: string,
    tags: string[] | Array<{ tag: string; type: string }>
  ) => void;
}

interface TagSuggestion {
  tag: string;
  type: "existing" | "new";
  score?: number;
  usage_count?: number;
  model?: string;
}

// A friendly name for known model IDs
const prettyModelName = (raw?: string) => {
  switch (raw) {
    case "claude-sonnet-4-20250514":
      return "Claude 4 Sonnet";
    case "claude-opus-4-1-20250805":
      return "Claude Opus 4.1";
    case "claude-3-5-sonnet-20241022":
      return "Claude 3.5 Sonnet";
    case "claude-3-opus-20240229":
      return "Claude 3 Opus";
    case "gpt-4o-mini":
      return "GPT‑4o mini";
    case "spacy-fallback":
      return "SpaCy NLP (Fallback)";
    case "custom":
      return "Custom";
    default:
      return raw || "Unknown";
  }
};

// Lightweight spinner
const Spinner = ({ className = "" }: { className?: string }) => (
  <LoaderCircle className={`animate-spin ${className}`} aria-hidden />
);

// ------------------------------------------------------
// Component
// ------------------------------------------------------
export default function TagSuggestionModal({
  isOpen,
  onClose,
  tweet,
  onTagsApplied,
}: TagSuggestionModalProps) {
  const [existingSuggestions, setExistingSuggestions] = useState<TagSuggestion[]>([]);
  const [newSuggestions, setNewSuggestions] = useState<TagSuggestion[]>([]);
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [customTag, setCustomTag] = useState("");
  const [modelUsed, setModelUsed] = useState<string>("");

  // Reset state on open/tweet change
  useEffect(() => {
    if (isOpen && tweet) {
      setSelectedTags(new Set());
      void fetchSuggestions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, tweet?.id]);

  const existingTagSet = useMemo(() => new Set(tweet?.tags.map((t) => t.tag) || []), [tweet]);

  async function fetchSuggestions() {
    if (!tweet) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/api/tags/suggest/${tweet.id}`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Failed to get suggestions");
      const data = await res.json();
      setExistingSuggestions(data.existing_suggestions || []);
      setNewSuggestions(data.new_suggestions || []);
      setModelUsed(data.model_used || "Unknown");
    } catch (e: any) {
      setError(e?.message || "An error occurred");
      setExistingSuggestions([]);
      setNewSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  }

  function toggleTag(tag: string) {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      next.has(tag) ? next.delete(tag) : next.add(tag);
      return next;
    });
  }

  function addCustomTag() {
    const raw = customTag.trim();
    if (!raw) return;
    const tag = raw.replace(/\s+/g, "-");
    setSelectedTags((prev) => new Set(prev).add(tag));
    setNewSuggestions((prev) => {
      if (!prev.some((s) => s.tag === tag)) {
        return [...prev, { tag, type: "new", model: "custom" }];
      }
      return prev;
    });
    setCustomTag("");
  }

  function applyTags() {
    if (!tweet) return;
    const tagsToApply = Array.from(selectedTags)
      .filter((t) => !existingTagSet.has(t))
      .map((t) => ({ tag: t, type: newSuggestions.some((s) => s.tag === t && s.model === "custom") ? "custom" : "ai-suggested" }));

    if (tagsToApply.length > 0) {
      onTagsApplied(tweet.id, tagsToApply);
    }
    onClose();
  }

  function regenerate() {
    setExistingSuggestions([]);
    setNewSuggestions([]);
    setSelectedTags(new Set());
    void fetchSuggestions();
  }

  function decodeHTMLEntities(text: string) {
    const el = document.createElement("textarea");
    el.innerHTML = text;
    return el.value;
  }

  const hasNoData = !isLoading && !error && existingSuggestions.length === 0 && newSuggestions.length === 0;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => (!open ? onClose() : null)}>
      <DialogContent className="max-w-3xl p-0 overflow-hidden">
        <DialogHeader className="px-6 pt-6 pb-3">
          <DialogTitle className="flex items-center gap-3 text-xl">
            <Tags className="h-5 w-5" /> Tag Suggestions
          </DialogTitle>
          <DialogDescription className="sr-only">
            Suggest and apply tags to categorize this tweet for better organization and discovery
          </DialogDescription>
        </DialogHeader>

        {/* Tweet preview */}
        {tweet && (
          <div className="px-6 py-3 border-b bg-muted/40">
            <div className="text-sm text-muted-foreground">@{tweet.author_username}</div>
            <div className="text-sm mt-1 line-clamp-3">
              {decodeHTMLEntities(tweet.text)}
            </div>
          </div>
        )}

        {/* Model info */}
        {modelUsed && (
          <div className="px-6 pt-4">
            <div className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-500 to-violet-600 px-3 py-2 text-white">
              <Sparkles className="h-4 w-4" />
              <span className="text-sm">Powered by <strong>{prettyModelName(modelUsed)}</strong></span>
            </div>
          </div>
        )}

        <ScrollArea className="max-h-[60vh] px-6 py-4">
          {/* Loading */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center gap-3 py-12">
              <Spinner className="h-6 w-6" />
              <p className="text-sm text-muted-foreground">Getting AI suggestions…</p>
            </div>
          )}

          {/* Error */}
          {!isLoading && error && (
            <Alert variant="destructive" className="mb-4">
              <AlertTitle>Couldn’t fetch suggestions</AlertTitle>
              <AlertDescription className="flex items-center justify-between gap-3">
                <span className="text-sm">{error}</span>
                <Button variant="secondary" size="sm" onClick={fetchSuggestions}>
                  Retry
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {/* Existing suggestions */}
          {!isLoading && !error && existingSuggestions.length > 0 && (
            <section className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                <Hash className="h-4 w-4" />
                <h3 className="text-sm font-medium">Similar Existing Tags</h3>
                <Separator className="ml-2 flex-1" />
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {existingSuggestions.map((s) => {
                  const isSelected = selectedTags.has(s.tag);
                  const usage = s.usage_count ? ` · ${s.usage_count}×` : "";
                  const sim = s.score ? ` · ${(s.score * 100).toFixed(1)}%` : "";
                  return (
                    <TooltipProvider key={s.tag}>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <motion.button
                            whileTap={{ scale: 0.98 }}
                            onClick={() => toggleTag(s.tag)}
                            className={`group inline-flex items-center justify-between rounded-full border px-3 py-2 text-sm transition focus:outline-none focus:ring-2 focus:ring-ring ${
                              isSelected
                                ? "border-emerald-600 bg-emerald-600 text-emerald-50"
                                : "border-emerald-300/60 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-900 dark:text-emerald-100"
                            }`}
                            aria-pressed={isSelected}
                            aria-label={`Select tag ${s.tag}`}
                          >
                            <span className="truncate pr-2">{s.tag}</span>
                            <span className={`ml-2 inline-flex h-5 w-5 items-center justify-center rounded-full text-xs font-semibold ${
                              isSelected ? "bg-white/20" : "bg-emerald-200/80 dark:bg-emerald-900/60"
                            }`}>
                              {isSelected ? <Check className="h-3.5 w-3.5" /> : <Plus className="h-3.5 w-3.5" />}
                            </span>
                          </motion.button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Used info{usage || " — n/a"}</p>
                          <p>Similarity{sim || " — n/a"}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  );
                })}
              </div>
            </section>
          )}

          {/* New suggestions */}
          {!isLoading && !error && newSuggestions.length > 0 && (
            <section className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="h-4 w-4" />
                <h3 className="text-sm font-medium">New Tag Suggestions</h3>
                <Separator className="ml-2 flex-1" />
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {newSuggestions.map((s) => {
                  const isSelected = selectedTags.has(s.tag);
                  const isCustom = s.model === "custom";
                  return (
                    <motion.button
                      key={s.tag}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => toggleTag(s.tag)}
                      className={`group inline-flex items-center justify-between rounded-full border px-3 py-2 text-sm transition focus:outline-none focus:ring-2 focus:ring-ring ${
                        isSelected
                          ? "border-violet-600 bg-violet-600 text-violet-50"
                          : "border-violet-300/60 bg-violet-50 dark:bg-violet-950/30 text-violet-900 dark:text-violet-100"
                      }`}
                      aria-pressed={isSelected}
                      aria-label={`Select tag ${s.tag}`}
                    >
                      <span className="truncate pr-2">
                        {s.tag}
                        {isCustom && (
                          <Badge variant="secondary" className="ml-2 h-5">custom</Badge>
                        )}
                      </span>
                      <span className={`ml-2 inline-flex h-5 w-5 items-center justify-center rounded-full text-xs font-semibold ${
                        isSelected ? "bg-white/20" : "bg-violet-200/80 dark:bg-violet-900/60"
                      }`}>
                        {isSelected ? <Check className="h-3.5 w-3.5" /> : <Plus className="h-3.5 w-3.5" />}
                      </span>
                    </motion.button>
                  );
                })}
              </div>
            </section>
          )}

          {hasNoData && (
            <div className="flex items-center justify-center rounded-md border p-8 text-sm text-muted-foreground">
              No suggestions available.
            </div>
          )}

          {/* Current tags */}
          <section className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <Info className="h-4 w-4" />
              <h3 className="text-sm font-medium">Current Tags</h3>
              <Separator className="ml-2 flex-1" />
            </div>
            <div className="flex flex-wrap gap-2">
              {tweet?.tags?.length ? (
                tweet!.tags.map((t) => (
                  <Badge key={t.tag} variant="outline" className="gap-1">
                    {t.tag}
                    {t.type === "llm" && <span className="ml-1 text-[10px]">AI</span>}
                  </Badge>
                ))
              ) : (
                <span className="text-sm text-muted-foreground">No tags yet</span>
              )}
            </div>
          </section>

          {/* Custom tag */}
          <section className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <Plus className="h-4 w-4" />
              <h3 className="text-sm font-medium">Add Custom Tag</h3>
              <Separator className="ml-2 flex-1" />
            </div>
            <div className="flex items-center gap-2">
              <Input
                value={customTag}
                onChange={(e) => setCustomTag(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") addCustomTag();
                }}
                placeholder="Enter custom tag"
                aria-label="Custom tag"
              />
              <Button onClick={addCustomTag}>
                <Plus className="mr-2 h-4 w-4" /> Add
              </Button>
            </div>
          </section>

          {/* Selected summary */}
          <section>
            <div className="flex items-center gap-2 mb-2">
              <Check className="h-4 w-4" />
              <h3 className="text-sm font-medium">Tags to Apply ({selectedTags.size})</h3>
              <Separator className="ml-2 flex-1" />
            </div>
            <AnimatePresence initial={false}>
              <div className="flex flex-wrap gap-2">
                {Array.from(selectedTags).map((tag) => (
                  <motion.button
                    key={tag}
                    layout
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.95, opacity: 0 }}
                    onClick={() => toggleTag(tag)}
                    className="rounded-full bg-primary text-primary-foreground px-3 py-1 text-sm hover:bg-primary/90"
                    aria-label={`Remove ${tag}`}
                  >
                    {tag} <span className="ml-1">×</span>
                  </motion.button>
                ))}
                {selectedTags.size === 0 && (
                  <span className="text-sm text-muted-foreground">Nothing selected yet</span>
                )}
              </div>
            </AnimatePresence>
          </section>
        </ScrollArea>

        {/* Footer */}
        <div className="flex items-center justify-between gap-2 border-t px-6 py-4">
          <Button variant="secondary" onClick={regenerate} disabled={isLoading}>
            <RefreshCcw className="mr-2 h-4 w-4" /> Regenerate
          </Button>
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={onClose}>Cancel</Button>
            <Button onClick={applyTags} disabled={isLoading || selectedTags.size === 0}>
              Apply {selectedTags.size} {selectedTags.size === 1 ? "Tag" : "Tags"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
