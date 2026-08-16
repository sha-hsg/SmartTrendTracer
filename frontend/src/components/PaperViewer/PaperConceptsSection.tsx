import React from "react";
import {
  Tag as TagIcon,
  Plus,
  X,
  Loader2,
  Brain,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import type { Paper } from "./types";

export interface PaperConceptsSectionProps {
  paper: Paper;
  newTag: string;
  setNewTag: (tag: string) => void;
  addingTag: boolean;
  handleAddTag: () => void;
  handleRemoveTag: (tag: string) => void;
  setShowTagModal: (show: boolean) => void;
  setShowEntityModal: (show: boolean) => void;
  setEditingConceptTag: (tag: string | null) => void;
  setShowConceptEditModal: (show: boolean) => void;
}

const PaperConceptsSection: React.FC<PaperConceptsSectionProps> = ({
  paper,
  newTag,
  setNewTag,
  addingTag,
  handleAddTag,
  handleRemoveTag,
  setShowTagModal,
  setShowEntityModal,
  setEditingConceptTag,
  setShowConceptEditModal,
}) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <TagIcon className="h-4 w-4 text-purple-600" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Tags & Analysis</span>
        </div>
      </div>

      {/* Primary Action Buttons */}
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowTagModal(true)}
          disabled={!paper?.content}
          className="h-8 text-xs bg-purple-50 dark:bg-purple-950 hover:bg-purple-100 dark:hover:bg-purple-900 text-purple-700 dark:text-purple-300 border-purple-300 dark:border-purple-900 disabled:opacity-60"
          title={!paper?.content ? "Paper must be processed first" : "Suggest concept tags using AI"}
        >
          <Sparkles className="h-3 w-3 mr-2" />
          Suggest Concept Tags
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowEntityModal(true)}
          disabled={!paper?.content}
          className="h-8 text-xs bg-blue-50 dark:bg-blue-950 hover:bg-blue-100 dark:hover:bg-blue-900 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-900 disabled:opacity-60"
          title={!paper?.content ? "Paper must be processed first" : "Extract entities and add them as tags"}
        >
          <Brain className="h-3 w-3 mr-2" />
          Entity Extraction
        </Button>
      </div>

      {/* Tags Display */}
      <div className="space-y-2">
        {(paper.tags || []).length > 0 ? (
          <>
            <div className="text-xs text-gray-500 dark:text-gray-400">{paper.tags?.length || 0} tags assigned (click to edit)</div>
            <div className="flex flex-wrap gap-1">
              {(paper.tags || []).map((tag) => (
                <Badge
                  key={tag}
                  variant="outline"
                  className="text-xs group border-blue-200 dark:border-blue-900 text-blue-800 dark:text-blue-300 bg-blue-50 dark:bg-blue-950 hover:bg-blue-100 dark:hover:bg-blue-900 transition-all hover:shadow-sm cursor-pointer inline-flex items-center max-w-full"
                  onClick={() => {
                    setEditingConceptTag(tag);
                    setShowConceptEditModal(true);
                  }}
                  title={`Click to edit: ${tag}`}
                >
                  <span className="break-words">{tag}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveTag(tag);
                    }}
                    className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 hover:bg-red-100 dark:hover:bg-red-900 rounded-full p-0.5"
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
          <div className="text-xs text-gray-400 dark:text-gray-500 italic">No tags assigned yet</div>
        )}
      </div>

      {/* Add New Tag */}
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
          className="h-8 px-3 bg-blue-50 dark:bg-blue-950 hover:bg-blue-100 dark:hover:bg-blue-900 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-900 disabled:opacity-60"
          title="Add tag"
        >
          {addingTag ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
        </Button>
      </div>
    </div>
  );
};

export default PaperConceptsSection;
