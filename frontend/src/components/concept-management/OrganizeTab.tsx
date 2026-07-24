import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  X,
  AlertCircle,
  CheckCircle,
  Sparkles,
  Loader2,
  Brain,
} from 'lucide-react'
import type { UnorganizedConcept, OrganizationSuggestion } from './types'

interface OrganizeTabProps {
  organizationStats: any
  unorganizedConcepts: UnorganizedConcept[]
  selectedUnorganized: UnorganizedConcept | null
  setSelectedUnorganized: (concept: UnorganizedConcept | null) => void
  organizationSuggestion: OrganizationSuggestion | null
  setOrganizationSuggestion: (suggestion: OrganizationSuggestion | null) => void
  loading: boolean
  fetchOrganizationSuggestion: (conceptId: string) => void
  handleApplyOrganization: () => void
  handleBatchReorganize: (limit: number, autoApply: boolean) => void
  setReorganizerDialogOpen: (open: boolean) => void
}

function OrganizationStatsCards({ stats }: { stats: any }) {
  return (
    <div className="grid grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Unorganized</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.unorganized_concepts}</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Organized</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.organized_concepts}</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Total Concepts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total_concepts}</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Organized %</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {typeof stats.organization_percentage === 'number'
              ? `${stats.organization_percentage.toFixed(0)}%`
              : '—'}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default function OrganizeTab({
  organizationStats,
  unorganizedConcepts,
  selectedUnorganized,
  setSelectedUnorganized,
  organizationSuggestion,
  setOrganizationSuggestion,
  loading,
  fetchOrganizationSuggestion,
  handleApplyOrganization,
  handleBatchReorganize,
  setReorganizerDialogOpen,
}: OrganizeTabProps) {
  return (
    <div className="space-y-4">
      {organizationStats && <OrganizationStatsCards stats={organizationStats} />}

      {/* Batch Organization Actions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Batch Organization</CardTitle>
              <CardDescription>
                Use AI to automatically organize multiple concepts at once
              </CardDescription>
            </div>
            <Button
              variant="default"
              size="sm"
              onClick={() => setReorganizerDialogOpen(true)}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
            >
              <Brain className="h-4 w-4 mr-2" />
              Advanced AI Reorganization
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button
              onClick={() => handleBatchReorganize(10, false)}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Organize 10 Concepts
                </>
              )}
            </Button>

            <Button
              variant="outline"
              onClick={() => {
                if (!confirm('This will automatically apply AI suggestions to 10 concepts. Continue?')) return
                handleBatchReorganize(10, true)
              }}
              disabled={loading}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Organize & Apply (10)
            </Button>

            <Button
              variant="destructive"
              onClick={() => {
                if (!confirm('This will process ALL unorganized concepts. This may take a while. Continue?')) return
                handleBatchReorganize(50, true)
              }}
              disabled={loading}
            >
              <AlertCircle className="h-4 w-4 mr-2" />
              Organize All (Max 50)
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Unorganized concepts list */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Unorganized Concepts</CardTitle>
            <CardDescription>
              Concepts that need to be organized into the hierarchy
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              {unorganizedConcepts.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
                  <p>All concepts are organized!</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {unorganizedConcepts.map(concept => (
                    <div
                      key={concept._id}
                      className={`p-3 rounded-lg border cursor-pointer hover:bg-accent ${
                        selectedUnorganized?._id === concept._id ? 'bg-accent' : ''
                      }`}
                      onClick={() => {
                        setSelectedUnorganized(concept)
                        setOrganizationSuggestion(null)
                      }}
                    >
                      <div className="font-medium">{concept.display_name}</div>
                      <div className="text-sm text-muted-foreground">
                        Usage: {concept.usage_count}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Organization suggestion */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">
              {selectedUnorganized ? 'Organization Suggestion' : 'Select a concept'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {selectedUnorganized ? (
              <div className="space-y-4">
                <div>
                  <Label>Selected Concept</Label>
                  <p className="text-lg font-medium">{selectedUnorganized.display_name}</p>
                  {selectedUnorganized.description && (
                    <p className="text-sm text-muted-foreground mt-1">
                      {selectedUnorganized.description}
                    </p>
                  )}
                </div>

                {!organizationSuggestion && (
                  <Button
                    onClick={() => fetchOrganizationSuggestion(selectedUnorganized._id)}
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Getting AI Suggestion...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4 mr-2" />
                        Get AI Suggestion
                      </>
                    )}
                  </Button>
                )}

                {organizationSuggestion && (
                  <div className="space-y-4">
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>AI Suggestion</AlertTitle>
                      <AlertDescription className="mt-2">
                        {organizationSuggestion.is_alias ? (
                          <div>
                            <p>This appears to be an alias of:</p>
                            <p className="font-medium mt-1">
                              {organizationSuggestion.alias_of}
                            </p>
                          </div>
                        ) : (
                          <div>
                            <p>Suggested parent concept{(organizationSuggestion.parent_concepts?.length || 0) > 1 ? 's' : ''}:</p>
                            <p className="font-medium mt-1">
                              {organizationSuggestion.parent_concepts?.length
                                ? organizationSuggestion.parent_concepts.join(', ')
                                : 'Root level'}
                            </p>
                          </div>
                        )}
                        <p className="mt-2 text-sm">{organizationSuggestion.reasoning}</p>
                        {organizationSuggestion.entity_type && (
                          <div className="mt-2">
                            <Badge variant="outline">
                              Entity type: {organizationSuggestion.entity_type}
                            </Badge>
                          </div>
                        )}
                      </AlertDescription>
                    </Alert>

                    <div className="flex gap-2">
                      <Button onClick={handleApplyOrganization} disabled={loading}>
                        <CheckCircle className="h-4 w-4 mr-2" />
                        Apply Suggestion
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => setOrganizationSuggestion(null)}
                      >
                        <X className="h-4 w-4 mr-2" />
                        Reject
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                Select an unorganized concept to get AI suggestions
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
