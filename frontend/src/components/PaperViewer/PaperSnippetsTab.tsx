/**
 * PaperSnippetsTab - Renders the snippets/notes tab with snippet creation form
 * and existing snippets list.
 */
import React from "react";
import {
  MessageSquare,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { Paper } from "./types";

export interface PaperSnippetsTabProps {
  paper: Paper;
  selectedText: string;
  setSelectedText: React.Dispatch<React.SetStateAction<string>>;
  snippetAnnotation: string;
  setSnippetAnnotation: React.Dispatch<React.SetStateAction<string>>;
  snippetCategory: string;
  setSnippetCategory: React.Dispatch<React.SetStateAction<string>>;
  creatingSnippet: boolean;
  handleCreateSnippet: () => Promise<void>;
}

const PaperSnippetsTab: React.FC<PaperSnippetsTabProps> = ({
  paper,
  selectedText,
  setSelectedText,
  snippetAnnotation,
  setSnippetAnnotation,
  snippetCategory,
  setSnippetCategory,
  creatingSnippet,
  handleCreateSnippet,
}) => {
  return (
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
  );
};

export default PaperSnippetsTab;
