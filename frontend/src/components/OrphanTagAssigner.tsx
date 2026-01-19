import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  AlertCircle, 
  CheckCircle, 
  RefreshCw, 
  Tag,
  Sparkles,
  Info,
  ChevronRight,
  Shuffle
} from 'lucide-react';
import axios from 'axios';

interface OrphanTag {
  id: number;
  tag: string;
  display_name: string;
  usage_count: number;
  description?: string;
}

interface AssignmentResult {
  tag: string;
  action: string;
  parent?: string;
  synonym_of?: string;
  confidence: number;
  reasoning: string;
}

interface AssignmentSummary {
  total_processed: number;
  assigned: number;
  synonyms_created: number;
  new_categories: number;
  unassigned: number;
}

export const OrphanTagAssigner: React.FC = () => {
  const [orphanTags, setOrphanTags] = useState<OrphanTag[]>([]);
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [isAssigning, setIsAssigning] = useState(false);
  const [results, setResults] = useState<AssignmentResult[]>([]);
  const [summary, setSummary] = useState<AssignmentSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [minUsage, setMinUsage] = useState(2);
  const [isDryRun, setIsDryRun] = useState(true);
  const [activeTab, setActiveTab] = useState('preview');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    loadOrphanTags();
  }, [minUsage]);

  const loadOrphanTags = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/tags/orphans/preview', {
        params: { min_usage: minUsage, limit: 100 }
      });
      setOrphanTags(response.data.orphan_tags || []);
    } catch (err) {
      setError('Failed to load orphan tags');
      console.error('Error loading orphan tags:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAssignOrphans = async () => {
    setIsAssigning(true);
    setError(null);
    setProgress(0);
    setResults([]);
    setSummary(null);

    try {
      const tagsToProcess = selectedTags.size > 0 
        ? Array.from(selectedTags)
        : undefined;

      const response = await axios.post('/api/tags/orphans/assign', {
        min_usage: minUsage,
        batch_size: 20,
        dry_run: isDryRun,
        specific_tags: tagsToProcess
      });

      if (response.data.success) {
        setResults(response.data.results?.assignments || []);
        setSummary(response.data.summary);
        setActiveTab('results');
        
        // Reload orphan tags if not dry run
        if (!isDryRun) {
          await loadOrphanTags();
        }
      } else {
        setError(response.data.error || 'Assignment failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to assign orphan tags');
      console.error('Error assigning orphan tags:', err);
    } finally {
      setIsAssigning(false);
      setProgress(100);
    }
  };

  const toggleTagSelection = (tag: string) => {
    const newSelection = new Set(selectedTags);
    if (newSelection.has(tag)) {
      newSelection.delete(tag);
    } else {
      newSelection.add(tag);
    }
    setSelectedTags(newSelection);
  };

  const selectAll = () => {
    setSelectedTags(new Set(orphanTags.map(t => t.tag)));
  };

  const clearSelection = () => {
    setSelectedTags(new Set());
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Tag className="h-5 w-5" />
              Orphan Tag Assignment
            </CardTitle>
            <CardDescription>
              Assign uncategorized tags to existing taxonomy categories using AI
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.location.href = '/tags/reorganize'}
              className="flex items-center gap-2"
            >
              <Shuffle className="h-4 w-4" />
              Full Reorganization
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="preview">Preview</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
            <TabsTrigger value="results">Results</TabsTrigger>
          </TabsList>

          <TabsContent value="preview" className="space-y-4">
            {/* Controls */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  Min Usage:
                </span>
                <input
                  type="number"
                  min="0"
                  value={minUsage}
                  onChange={(e) => setMinUsage(parseInt(e.target.value) || 0)}
                  className="w-20 px-2 py-1 border rounded"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadOrphanTags}
                  disabled={isLoading}
                >
                  <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                </Button>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={selectAll}>
                  Select All
                </Button>
                <Button variant="outline" size="sm" onClick={clearSelection}>
                  Clear
                </Button>
                <Badge variant="secondary">
                  {selectedTags.size} / {orphanTags.length} selected
                </Badge>
              </div>
            </div>

            {/* Orphan Tags List */}
            <div className="border rounded-lg p-4 max-h-96 overflow-y-auto">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : orphanTags.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No orphan tags found with usage ≥ {minUsage}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {orphanTags.map(tag => (
                    <div
                      key={tag.id}
                      className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-colors ${
                        selectedTags.has(tag.tag)
                          ? 'bg-primary/10 border-primary'
                          : 'hover:bg-muted/50'
                      }`}
                      onClick={() => toggleTagSelection(tag.tag)}
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={selectedTags.has(tag.tag)}
                          onChange={() => {}}
                          className="pointer-events-none"
                        />
                        <div>
                          <div className="font-medium text-sm">
                            {tag.display_name}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {tag.tag}
                          </div>
                        </div>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {tag.usage_count}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="dryRun"
                  checked={isDryRun}
                  onChange={(e) => setIsDryRun(e.target.checked)}
                />
                <label htmlFor="dryRun" className="text-sm">
                  Dry Run (preview changes without applying)
                </label>
              </div>
              <Button
                onClick={handleAssignOrphans}
                disabled={isAssigning || (selectedTags.size === 0 && orphanTags.length === 0)}
                className="flex items-center gap-2"
              >
                {isAssigning ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Assigning...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Assign {selectedTags.size > 0 ? `${selectedTags.size} Tags` : 'All Tags'}
                  </>
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                This tool uses Gemini 2.5 Pro to intelligently assign orphan tags to your existing taxonomy.
                Unlike full reorganization, this preserves your current structure and only assigns uncategorized tags.
              </AlertDescription>
            </Alert>

            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-2">Assignment Mode</h3>
                <div className="space-y-2">
                  <label className="flex items-center gap-2">
                    <input type="radio" checked={!isDryRun} onChange={() => setIsDryRun(false)} />
                    <span>Apply Changes</span>
                    <span className="text-sm text-muted-foreground">
                      (Permanently assigns tags to categories)
                    </span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="radio" checked={isDryRun} onChange={() => setIsDryRun(true)} />
                    <span>Dry Run</span>
                    <span className="text-sm text-muted-foreground">
                      (Preview assignments without making changes)
                    </span>
                  </label>
                </div>
              </div>

              <div>
                <h3 className="font-medium mb-2">Processing Options</h3>
                <div className="space-y-2">
                  <div>
                    <label className="text-sm">Minimum Usage Count</label>
                    <input
                      type="number"
                      min="0"
                      value={minUsage}
                      onChange={(e) => setMinUsage(parseInt(e.target.value) || 0)}
                      className="w-full px-3 py-2 border rounded mt-1"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Only process tags used at least this many times
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="results" className="space-y-4">
            {isAssigning && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Processing orphan tags...</span>
                  <span>{progress}%</span>
                </div>
                <Progress value={progress} />
              </div>
            )}

            {summary && (
              <Alert className="border-green-200 bg-green-50">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription>
                  <div className="font-medium text-green-900 mb-2">
                    Assignment Complete {isDryRun && '(Dry Run)'}
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                    <div>
                      <span className="text-muted-foreground">Processed:</span>
                      <span className="ml-1 font-medium">{summary.total_processed}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Assigned:</span>
                      <span className="ml-1 font-medium text-green-600">{summary.assigned}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Synonyms:</span>
                      <span className="ml-1 font-medium">{summary.synonyms_created || 0}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Unassigned:</span>
                      <span className="ml-1 font-medium text-orange-600">{summary.unassigned}</span>
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {results.length > 0 && (
              <div className="border rounded-lg p-4 max-h-96 overflow-y-auto">
                <h3 className="font-medium mb-3">Assignment Details</h3>
                <div className="space-y-2">
                  {results.map((result, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 border rounded-lg">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{result.tag}</Badge>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        <Badge variant="default">{result.parent || result.synonym_of}</Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge 
                          variant={result.action === 'assign' ? 'default' : 'secondary'}
                          className="text-xs"
                        >
                          {result.action}
                        </Badge>
                        <Badge 
                          variant="outline" 
                          className={`text-xs ${
                            result.confidence > 0.8 ? 'text-green-600' :
                            result.confidence > 0.6 ? 'text-yellow-600' :
                            'text-red-600'
                          }`}
                        >
                          {Math.round(result.confidence * 100)}%
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};