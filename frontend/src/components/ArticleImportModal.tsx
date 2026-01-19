import React, { useState } from 'react'
import axios from 'axios'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Plus,
  Download
} from 'lucide-react'

interface ArticleImportModalProps {
  isOpen: boolean
  onClose: () => void
  onImportSuccess: () => void
}

export default function ArticleImportModal({ isOpen, onClose, onImportSuccess }: ArticleImportModalProps) {
  const [singleUrl, setSingleUrl] = useState('')
  const [batchUrls, setBatchUrls] = useState('')
  const [isImporting, setIsImporting] = useState(false)
  const [importResult, setImportResult] = useState<any>(null)
  const [batchResults, setBatchResults] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleSingleImport = async () => {
    if (!singleUrl.trim()) {
      setError('Please enter a URL')
      return
    }

    setIsImporting(true)
    setError(null)
    setImportResult(null)

    try {
      const response = await axios.post('http://localhost:8000/api/v2/articles/import-url', {
        url: singleUrl
      })

      if (response.data.success) {
        setImportResult(response.data)
        onImportSuccess()
        setTimeout(() => {
          setSingleUrl('')
          setImportResult(null)
        }, 3000)
      } else {
        setError(response.data.error || 'Failed to import article')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import article')
    } finally {
      setIsImporting(false)
    }
  }

  const handleBatchImport = async () => {
    const urls = batchUrls
      .split('\n')
      .map(url => url.trim())
      .filter(url => url.length > 0)

    if (urls.length === 0) {
      setError('Please enter at least one URL')
      return
    }

    setIsImporting(true)
    setError(null)
    setBatchResults([])

    try {
      const response = await axios.post('http://localhost:8000/api/v2/articles/import-batch', urls)
      setBatchResults(response.data.results)
      onImportSuccess()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import articles')
    } finally {
      setIsImporting(false)
    }
  }

  const handleClose = () => {
    if (!isImporting) {
      setSingleUrl('')
      setBatchUrls('')
      setImportResult(null)
      setBatchResults([])
      setError(null)
      onClose()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Import Articles from URL
          </DialogTitle>
          <DialogDescription>
            Import articles from Substack, Medium, blogs, or any web page
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="single" className="mt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="single">Single URL</TabsTrigger>
            <TabsTrigger value="batch">Batch Import</TabsTrigger>
          </TabsList>

          <TabsContent value="single" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="url">Article URL</Label>
              <div className="flex gap-2">
                <Input
                  id="url"
                  type="url"
                  placeholder="https://example.substack.com/p/article-title"
                  value={singleUrl}
                  onChange={(e) => setSingleUrl(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !isImporting) {
                      handleSingleImport()
                    }
                  }}
                  disabled={isImporting}
                />
                <Button 
                  onClick={handleSingleImport} 
                  disabled={isImporting || !singleUrl.trim()}
                >
                  {isImporting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {importResult && importResult.success && (
              <Alert className="border-green-200 bg-green-50">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  <div className="font-semibold">{importResult.title}</div>
                  <div className="text-sm mt-1">
                    By {importResult.author} • {importResult.word_count} words
                  </div>
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>

          <TabsContent value="batch" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="batch-urls">Article URLs (one per line)</Label>
              <Textarea
                id="batch-urls"
                placeholder="https://example.substack.com/p/article-1&#10;https://medium.com/@author/article-2&#10;https://blog.example.com/post-3"
                value={batchUrls}
                onChange={(e) => setBatchUrls(e.target.value)}
                rows={6}
                disabled={isImporting}
              />
              <div className="text-sm text-gray-500">
                Enter multiple URLs, one per line
              </div>
            </div>

            <Button 
              onClick={handleBatchImport} 
              disabled={isImporting || !batchUrls.trim()}
              className="w-full"
            >
              {isImporting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Importing...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Import All
                </>
              )}
            </Button>

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {batchResults.length > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-medium">Import Results:</div>
                <div className="max-h-64 overflow-y-auto space-y-2 border rounded-lg p-3">
                  {batchResults.map((result, idx) => (
                    <div 
                      key={idx} 
                      className={`flex items-start gap-2 p-2 rounded ${
                        result.success ? 'bg-green-50' : 'bg-red-50'
                      }`}
                    >
                      {result.success ? (
                        <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
                      )}
                      <div className="flex-1 text-sm">
                        <div className="font-medium">
                          {result.success ? result.title : result.url}
                        </div>
                        <div className="text-gray-600">
                          {result.success 
                            ? `${result.author} • ${result.word_count} words`
                            : result.error
                          }
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>

        <div className="mt-4 pt-4 border-t">
          <div className="text-sm text-gray-500">
            <div className="font-medium mb-2">Supported sites:</div>
            <ul className="space-y-1">
              <li>• Substack publications</li>
              <li>• Medium articles</li>
              <li>• Personal blogs</li>
              <li>• Most web articles with standard HTML structure</li>
            </ul>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}