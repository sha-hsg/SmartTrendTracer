import React from 'react';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  ArrowUpDown,
  FileText,
  MessageSquare,
  BookOpen,
  Newspaper,
  X,
  ExternalLink,
  Loader2,
} from 'lucide-react';

export interface LifecycleItem {
  concept_id: string;
  display_name: string;
  first_seen: string;
  last_seen: string;
  duration: number;
  volume: number;
  color: string;
  velocity: number;
  isActive: boolean;
}

export interface DocumentItem {
  id: string;
  type: 'tweet' | 'article' | 'paper' | 'reddit';
  title: string;
  preview: string;
  date: string;
  author?: string;
  url?: string;
}

export type SortKey = 'firstSeen' | 'lastSeen' | 'duration' | 'volume' | 'name';
export type SortDirection = 'asc' | 'desc';

export const formatShortDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

export const formatFullDate = (date: Date): string => {
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

export const calculateDaysDiff = (startDate: string | Date, endDate: string | Date): number => {
  const start = typeof startDate === 'string' ? new Date(startDate) : startDate;
  const end = typeof endDate === 'string' ? new Date(endDate) : endDate;
  const diffTime = Math.abs(end.getTime() - start.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
};

const ContentTypeIcon: React.FC<{ type: string; className?: string }> = ({ type, className = "w-4 h-4" }) => {
  switch (type) {
    case 'tweet':
      return <MessageSquare className={className} />;
    case 'article':
      return <Newspaper className={className} />;
    case 'paper':
      return <BookOpen className={className} />;
    case 'reddit':
      return <FileText className={className} />;
    default:
      return <FileText className={className} />;
  }
};

interface SortButtonProps {
  column: SortKey;
  label: string;
  sortKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
}

const SortButton: React.FC<SortButtonProps> = ({ column, label, sortKey, sortDirection, onSort }) => (
  <button
    onClick={() => onSort(column)}
    className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1 ${
      sortKey === column
        ? 'bg-primary text-primary-foreground'
        : 'hover:bg-accent text-muted-foreground'
    }`}
  >
    {label}
    {sortKey === column && (
      <ArrowUpDown className={`w-3 h-3 ${sortDirection === 'desc' ? 'rotate-180' : ''}`} />
    )}
  </button>
);

interface LifecycleTableProps {
  sortedLifecycle: LifecycleItem[];
  selectedConcept: LifecycleItem | null;
  sortKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
  onConceptSelect: (item: LifecycleItem) => void;
}

export const LifecycleTable: React.FC<LifecycleTableProps> = ({
  sortedLifecycle,
  selectedConcept,
  sortKey,
  sortDirection,
  onSort,
  onConceptSelect,
}) => {
  return (
    <>
      {/* Sort Controls */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">Sort:</span>
        <SortButton column="lastSeen" label="Last Seen" sortKey={sortKey} sortDirection={sortDirection} onSort={onSort} />
        <SortButton column="firstSeen" label="First Seen" sortKey={sortKey} sortDirection={sortDirection} onSort={onSort} />
        <SortButton column="duration" label="Duration" sortKey={sortKey} sortDirection={sortDirection} onSort={onSort} />
        <SortButton column="volume" label="Volume" sortKey={sortKey} sortDirection={sortDirection} onSort={onSort} />
        <SortButton column="name" label="Name" sortKey={sortKey} sortDirection={sortDirection} onSort={onSort} />
      </div>

      {/* Lifecycle Table */}
      <div className="border rounded-lg overflow-hidden">
        <div className="max-h-[280px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted sticky top-0">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium w-8"></th>
                <th className="text-left px-4 py-2.5 font-medium">Concept</th>
                <th className="text-left px-4 py-2.5 font-medium">First Seen</th>
                <th className="text-left px-4 py-2.5 font-medium">Last Seen</th>
                <th className="text-right px-4 py-2.5 font-medium">Duration</th>
                <th className="text-right px-4 py-2.5 font-medium">Volume</th>
              </tr>
            </thead>
            <tbody>
              {sortedLifecycle.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                    No concepts found in the selected time range
                  </td>
                </tr>
              ) : (
                sortedLifecycle.map((item) => {
                  const isSelected = selectedConcept?.concept_id === item.concept_id;
                  return (
                    <tr
                      key={item.concept_id}
                      className={`border-t cursor-pointer transition-colors ${
                        isSelected
                          ? 'bg-primary/10 hover:bg-primary/15'
                          : 'hover:bg-accent/50'
                      }`}
                      onClick={() => onConceptSelect(item)}
                    >
                      <td className="px-4 py-2.5">
                        <span
                          className={`inline-block w-3 h-3 rounded-full ${
                            item.isActive ? 'bg-green-500' : 'bg-amber-500'
                          }`}
                          title={item.isActive ? 'Active (activity in last 3 days)' : 'Inactive (no activity in 3 days)'}
                        />
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <span
                            className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                            style={{ backgroundColor: item.color }}
                          />
                          <span className={`font-medium truncate max-w-[180px] ${isSelected ? 'text-primary' : ''}`}>
                            {item.display_name}
                          </span>
                          {item.velocity > 50 && (
                            <Badge variant="secondary" className="text-[10px] px-1 py-0 bg-green-100 text-green-700">
                              +{Math.round(item.velocity)}%
                            </Badge>
                          )}
                          {item.velocity < -30 && (
                            <Badge variant="secondary" className="text-[10px] px-1 py-0 bg-red-100 text-red-700">
                              {Math.round(item.velocity)}%
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-2.5 text-muted-foreground">
                        {formatShortDate(item.first_seen)}
                      </td>
                      <td className="px-4 py-2.5 text-muted-foreground">
                        {formatShortDate(item.last_seen)}
                      </td>
                      <td className="px-4 py-2.5 text-right">
                        <Badge
                          variant={item.isActive ? "default" : "secondary"}
                          className="text-xs"
                        >
                          {item.duration} {item.duration === 1 ? 'day' : 'days'}
                        </Badge>
                      </td>
                      <td className="px-4 py-2.5 text-right text-muted-foreground">
                        {item.volume}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
};

interface DocumentPreviewPanelProps {
  selectedConcept: LifecycleItem;
  documents: DocumentItem[];
  documentsLoading: boolean;
  onClose: () => void;
}

export const DocumentPreviewPanel: React.FC<DocumentPreviewPanelProps> = ({
  selectedConcept,
  documents,
  documentsLoading,
  onClose,
}) => {
  return (
    <div className="border rounded-lg overflow-hidden">
      <div className="bg-muted px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4" />
          <span className="font-medium text-sm">
            Documents tagged with "{selectedConcept.display_name}"
          </span>
          <Badge variant="secondary" className="text-xs">
            {documents.length} in range
          </Badge>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-accent rounded transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <ScrollArea className="h-[250px]">
        {documentsLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        ) : documents.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            No documents found in the selected time range
          </div>
        ) : (
          <div className="divide-y">
            {documents.map((doc) => (
              <div
                key={`${doc.type}-${doc.id}`}
                className="p-3 hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-md ${
                    doc.type === 'tweet' ? 'bg-blue-100 text-blue-600' :
                    doc.type === 'article' ? 'bg-orange-100 text-orange-600' :
                    doc.type === 'paper' ? 'bg-purple-100 text-purple-600' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    <ContentTypeIcon type={doc.type} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm truncate">
                        {doc.title}
                      </span>
                      {doc.url && (
                        <a
                          href={doc.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-muted-foreground hover:text-foreground"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {doc.preview}
                    </p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                      <span>{formatShortDate(doc.date)}</span>
                      {doc.author && (
                        <>
                          <span>•</span>
                          <span className="truncate max-w-[150px]">{doc.author}</span>
                        </>
                      )}
                      <Badge variant="outline" className="text-[10px]">
                        {doc.type}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
};
