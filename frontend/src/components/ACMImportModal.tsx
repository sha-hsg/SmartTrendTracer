import React, { useState } from 'react'
import axios from 'axios'
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogDescription 
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Upload, CheckCircle, AlertCircle, GraduationCap } from 'lucide-react'

interface ACMImportModalProps {
  isOpen: boolean
  onClose: () => void
  onImportSuccess?: (paperId: string) => void
}

export const ACMImportModal: React.FC<ACMImportModalProps> = ({ 
  isOpen, 
  onClose, 
  onImportSuccess 
}) => {
  const [url, setUrl] = useState('')
  const [tags, setTags] = useState('')
  const [importing, setImporting] = useState(false)
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState<string>('')
  const [validatedDOI, setValidatedDOI] = useState<string>('')

  const validateUrl = async (inputUrl: string) => {
    if (!inputUrl) {
      setValidatedDOI('')
      return
    }

    try {
      const response = await axios.get('http://localhost:8000/api/acm/validate-url', {
        params: { url: inputUrl }
      })
      
      if (response.data.valid) {
        setValidatedDOI(response.data.doi)
        setError('')
      } else {
        setValidatedDOI('')
        setError('Invalid ACM URL. Please enter a valid dl.acm.org URL.')
      }
    } catch (err) {
      setValidatedDOI('')
      // Don't show error for validation, just silently fail
    }
  }

  const handleImport = async () => {
    if (!url.trim()) {
      setError('Please enter an ACM URL')
      return
    }

    setImporting(true)
    setError('')
    setSuccess('')

    try {
      // Parse tags
      const tagList = tags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0)

      const response = await axios.post('http://localhost:8000/api/acm/import', {
        url,
        add_tags: tagList.length > 0 ? tagList : undefined,
        process_pdf: false
      })

      if (response.data.success) {
        const { paper_id, title, authors, doi, year, venue } = response.data
        
        let successMsg = `Successfully imported: "${title}"`
        if (authors) {
          successMsg += ` by ${authors}`
        }
        if (venue && year) {
          successMsg += ` (${venue} ${year})`
        } else if (year) {
          successMsg += ` (${year})`
        }
        
        setSuccess(successMsg)
        
        // Clear form
        setUrl('')
        setTags('')
        setValidatedDOI('')
        
        // Notify parent and close after delay
        if (onImportSuccess) {
          onImportSuccess(paper_id)
        }
        
        setTimeout(() => {
          onClose()
          setSuccess('')
        }, 2000)
      }
    } catch (err: any) {
      console.error('Import error:', err)
      const errorMsg = err.response?.data?.detail || 'Failed to import paper. Please check the URL and try again.'
      setError(errorMsg)
    } finally {
      setImporting(false)
    }
  }

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newUrl = e.target.value
    setUrl(newUrl)
    
    // Validate URL if it looks like an ACM URL
    if (newUrl.includes('dl.acm.org')) {
      validateUrl(newUrl)
    } else {
      setValidatedDOI('')
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GraduationCap className="h-5 w-5 text-blue-600" />
            Import from ACM Digital Library
          </DialogTitle>
          <DialogDescription>
            Import papers from ACM Digital Library using DOI or direct URLs.
            Supports automatic metadata extraction via BibTeX.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* URL Input */}
          <div className="space-y-2">
            <Label htmlFor="url">ACM Paper URL</Label>
            <Input
              id="url"
              type="url"
              placeholder="https://dl.acm.org/doi/10.1145/3677389.3702588"
              value={url}
              onChange={handleUrlChange}
              disabled={importing}
            />
            {validatedDOI && (
              <p className="text-sm text-green-600 flex items-center gap-1">
                <CheckCircle className="h-3 w-3" />
                Valid DOI detected: {validatedDOI}
              </p>
            )}
            <p className="text-xs text-gray-500">
              Accepts both DOI URLs (e.g., /doi/10.1145/...) and PDF URLs (e.g., /doi/pdf/10.1145/...)
            </p>
          </div>

          {/* Tags Input */}
          <div className="space-y-2">
            <Label htmlFor="tags">Tags (optional)</Label>
            <Textarea
              id="tags"
              placeholder="machine-learning, deep-learning, computer-vision"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              disabled={importing}
              rows={2}
            />
            <p className="text-xs text-gray-500">
              Comma-separated tags to apply to the imported paper
            </p>
          </div>

          {/* Example URLs */}
          <div className="bg-gray-50 p-3 rounded-md space-y-1">
            <p className="text-xs font-medium text-gray-700">Example URLs:</p>
            <p className="text-xs text-gray-600 font-mono">
              https://dl.acm.org/doi/10.1145/3677389.3702588
            </p>
            <p className="text-xs text-gray-600 font-mono">
              https://dl.acm.org/doi/pdf/10.1145/3677389.3702588
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Success Alert */}
          {success && (
            <Alert className="border-green-500 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                {success}
              </AlertDescription>
            </Alert>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={importing}
            >
              Cancel
            </Button>
            <Button
              onClick={handleImport}
              disabled={importing || !url.trim()}
            >
              {importing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Importing...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Import Paper
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}