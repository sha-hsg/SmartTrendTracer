import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export interface AffiliationDialogProps {
  showAffiliationDialog: boolean;
  setShowAffiliationDialog: (show: boolean) => void;
  affiliationSuggestions: any[];
  selectedAffiliations: Set<number>;
  toggleAffiliationSelection: (idx: number) => void;
  handleApplyAffiliations: () => void;
}

export function AffiliationDialog({
  showAffiliationDialog,
  setShowAffiliationDialog,
  affiliationSuggestions,
  selectedAffiliations,
  toggleAffiliationSelection,
  handleApplyAffiliations,
}: AffiliationDialogProps) {
  return (
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
  );
}
