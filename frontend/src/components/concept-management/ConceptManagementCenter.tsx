import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import {
  AlertCircle,
  CheckCircle,
  GitBranch,
} from 'lucide-react'
import ConceptTreePanel from './ConceptTreePanel'
import ConceptDetailPanel from './ConceptDetailPanel'
import ConceptDialogs from './ConceptDialogs'
import OrganizeTab from './OrganizeTab'
import ImportExportTab from './ImportExportTab'
import useConceptManagement from './useConceptManagement'

export default function ConceptManagementCenter() {
  const cm = useConceptManagement()

  return (
    <div className="space-y-4">
      {/* Header with stats */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <GitBranch className="h-5 w-5" />
                Concept Management Center
              </CardTitle>
              <CardDescription>
                Manage concept hierarchy and organize new concepts
              </CardDescription>
            </div>
            {cm.stats && (
              <div className="flex gap-4 text-sm">
                <div>
                  <span className="font-medium">{cm.stats.concepts.total}</span>
                  <span className="text-muted-foreground"> concepts</span>
                </div>
                <div>
                  <span className="font-medium">{cm.stats.aliases.total}</span>
                  <span className="text-muted-foreground"> aliases</span>
                </div>
                <div>
                  <span className="font-medium">{cm.stats.instances.total}</span>
                  <span className="text-muted-foreground"> instances</span>
                </div>
              </div>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Main content tabs */}
      <Tabs value={cm.activeTab} onValueChange={cm.setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="browse">Browse & Edit</TabsTrigger>
          <TabsTrigger value="organize">Organize New</TabsTrigger>
          <TabsTrigger value="import-export">Import/Export</TabsTrigger>
        </TabsList>

        {/* Browse & Edit Tab */}
        <TabsContent value="browse" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <ConceptTreePanel
              treeData={cm.treeData}
              selectedConceptId={cm.selectedConcept?.id ?? null}
              searchQuery={cm.searchQuery}
              expandedNodes={cm.expandedNodes}
              loading={cm.loading}
              onSearchChange={cm.setSearchQuery}
              onToggleNode={cm.toggleNode}
              onSelectConcept={cm.handleConceptSelect}
              onRefresh={cm.fetchTreeData}
            />

            <ConceptDetailPanel
              selectedConcept={cm.selectedConcept}
              onEdit={cm.openEditDialog}
              onAddChild={cm.openCreateChildDialog}
              onDelete={() => cm.setDeleteDialogOpen(true)}
            />
          </div>
        </TabsContent>

        {/* Organize New Tab */}
        <TabsContent value="organize" className="space-y-4">
          <OrganizeTab
            organizationStats={cm.organizationStats}
            unorganizedConcepts={cm.unorganizedConcepts}
            selectedUnorganized={cm.selectedUnorganized}
            setSelectedUnorganized={cm.setSelectedUnorganized}
            organizationSuggestion={cm.organizationSuggestion}
            setOrganizationSuggestion={cm.setOrganizationSuggestion}
            loading={cm.loading}
            fetchOrganizationSuggestion={cm.fetchOrganizationSuggestion}
            handleApplyOrganization={cm.handleApplyOrganization}
            handleBatchReorganize={cm.handleBatchReorganize}
            setReorganizerDialogOpen={cm.setReorganizerDialogOpen}
          />
        </TabsContent>

        {/* Import/Export Tab */}
        <TabsContent value="import-export" className="space-y-4">
          <ImportExportTab
            handleExportOntology={cm.handleExportOntology}
            setImportDialogOpen={cm.setImportDialogOpen}
          />
        </TabsContent>
      </Tabs>

      {/* Alerts */}
      {cm.error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{cm.error}</AlertDescription>
        </Alert>
      )}

      {cm.success && (
        <Alert className="bg-green-50 border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{cm.success}</AlertDescription>
        </Alert>
      )}

      {/* Dialogs */}
      <ConceptDialogs
        editDialogOpen={cm.editDialogOpen}
        setEditDialogOpen={cm.setEditDialogOpen}
        handleUpdateConcept={cm.handleUpdateConcept}
        createDialogOpen={cm.createDialogOpen}
        setCreateDialogOpen={cm.setCreateDialogOpen}
        handleCreateConcept={cm.handleCreateConcept}
        deleteDialogOpen={cm.deleteDialogOpen}
        setDeleteDialogOpen={cm.setDeleteDialogOpen}
        handleDeleteConcept={cm.handleDeleteConcept}
        selectedConcept={cm.selectedConcept}
        reorganizerDialogOpen={cm.reorganizerDialogOpen}
        setReorganizerDialogOpen={cm.setReorganizerDialogOpen}
        formData={cm.formData}
        setFormData={cm.setFormData}
      />
    </div>
  )
}
