import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  RefreshCw,
  Download,
  Upload,
  AlertCircle,
  Hash,
} from 'lucide-react'

interface ImportExportTabProps {
  handleExportOntology: () => void
  setImportDialogOpen: (open: boolean) => void
}

export default function ImportExportTab({
  handleExportOntology,
  setImportDialogOpen,
}: ImportExportTabProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Export Ontology</CardTitle>
            <CardDescription>
              Download the complete concept hierarchy and metadata
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Export Options</Label>
              <div className="space-y-2">
                <label className="flex items-center space-x-2">
                  <input type="checkbox" defaultChecked />
                  <span className="text-sm">Include concept hierarchy</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input type="checkbox" defaultChecked />
                  <span className="text-sm">Include aliases</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input type="checkbox" />
                  <span className="text-sm">Include usage statistics</span>
                </label>
              </div>
            </div>
            <Button onClick={handleExportOntology} className="w-full">
              <Download className="h-4 w-4 mr-2" />
              Export to JSON
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Import Ontology</CardTitle>
            <CardDescription>
              Upload a JSON file to import concepts and hierarchy
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Warning</AlertTitle>
              <AlertDescription>
                Importing will merge with existing concepts. Duplicates will be skipped.
              </AlertDescription>
            </Alert>
            <Button
              variant="outline"
              className="w-full"
              onClick={() => setImportDialogOpen(true)}
            >
              <Upload className="h-4 w-4 mr-2" />
              Select File to Import
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Maintenance Tools</CardTitle>
          <CardDescription>
            Administrative tools for managing the concept system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Rebuild Index
            </Button>
            <Button variant="outline">
              <Hash className="h-4 w-4 mr-2" />
              Recalculate Stats
            </Button>
            <Button variant="outline">
              <AlertCircle className="h-4 w-4 mr-2" />
              Find Orphans
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
