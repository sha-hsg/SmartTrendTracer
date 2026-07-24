import { Copy, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Progress } from '@/components/ui/progress'

interface BibtexDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  bibtex: string
}

export function BibtexDialog({ open, onOpenChange, bibtex }: BibtexDialogProps) {
  const copyBibtex = () => {
    navigator.clipboard.writeText(bibtex)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>BibTeX Citation</DialogTitle>
          <DialogDescription>
            Copy this BibTeX entry to use in your LaTeX documents
          </DialogDescription>
        </DialogHeader>

        <Textarea
          value={bibtex}
          readOnly
          className="font-mono text-sm h-64"
        />

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button onClick={copyBibtex}>
            <Copy className="h-4 w-4 mr-2" />
            Copy to Clipboard
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface ImportProgressDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  progress: number
  importing: boolean
}

export function ImportProgressDialog({ open, onOpenChange, progress, importing }: ImportProgressDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Importing References</DialogTitle>
          <DialogDescription>
            Importing selected references as papers...
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <Progress value={progress} className="mb-2" />
          <p className="text-sm text-center text-gray-500">
            {Math.round(progress)}% complete
          </p>
        </div>

        {!importing && progress === 100 && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              Import completed successfully!
            </AlertDescription>
          </Alert>
        )}
      </DialogContent>
    </Dialog>
  )
}
