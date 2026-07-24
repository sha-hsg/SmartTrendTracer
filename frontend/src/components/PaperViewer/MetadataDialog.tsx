import {
  Plus,
  X,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export interface MetadataDialogProps {
  editingMetadata: boolean;
  setEditingMetadata: (editing: boolean) => void;
  editedMetadata: any;
  setEditedMetadata: (metadata: any) => void;
  handleSaveMetadata: () => void;
}

export function MetadataDialog({
  editingMetadata,
  setEditingMetadata,
  editedMetadata,
  setEditedMetadata,
  handleSaveMetadata,
}: MetadataDialogProps) {
  return (
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
                  No authors added yet. Click &quot;Add Author&quot; to start.
                </p>
              )}
            </fieldset>

            {/* Action Buttons */}
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
  );
}
