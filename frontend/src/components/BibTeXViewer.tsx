import React, { useState, useMemo } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Copy, 
  Download, 
  CheckCircle, 
  BookOpen,
  Code,
  FileText,
  User,
  Calendar,
  Building,
  Link,
  Hash
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface BibTeXViewerProps {
  bibtex?: string | null
  paperId?: string
  title?: string
  authors?: string[] | string  // Allow both array and string formats
  year?: number | string
  conference?: string
  journal?: string
  doi?: string
  dblpKey?: string
  dblpUrl?: string
  className?: string
}

interface ParsedBibTeX {
  type: string
  key: string
  fields: { [key: string]: string }
}

function parseBibTeX(bibtex: string): ParsedBibTeX | null {
  try {
    // Extract entry type and citation key
    const typeMatch = bibtex.match(/@(\w+)\s*\{([^,]+),/)
    if (!typeMatch) return null

    const type = typeMatch[1]
    const key = typeMatch[2]
    const fields: { [key: string]: string } = {}

    // Find where fields start (after first comma following the key)
    const fieldsStart = bibtex.indexOf(',', bibtex.indexOf('{')) + 1
    const fieldsSection = bibtex.substring(fieldsStart)
    
    // Advanced regex that properly handles nested braces
    // Matches: fieldname = {content with {nested} braces}
    // This pattern handles multiple levels of nesting by recursively matching brace pairs
    const fieldPattern = /(\w+)\s*=\s*\{((?:[^{}]|\{(?:[^{}]|\{[^}]*\})*\})*)\}/g
    let match
    
    while ((match = fieldPattern.exec(fieldsSection)) !== null) {
      const fieldName = match[1].toLowerCase()
      const fieldValue = match[2].trim()
      fields[fieldName] = fieldValue
    }

    // Alternative: Handle quoted strings as well (some BibTeX uses "..." instead of {...})
    const quotedFieldPattern = /(\w+)\s*=\s*"([^"]*)"/g
    while ((match = quotedFieldPattern.exec(fieldsSection)) !== null) {
      const fieldName = match[1].toLowerCase()
      if (!fields[fieldName]) { // Don't override if already found with braces
        fields[fieldName] = match[2].trim()
      }
    }

    return { type, key, fields }
  } catch (error) {
    console.error('Error parsing BibTeX:', error)
    return null
  }
}

function formatFieldValue(value: string): string {
  // Remove excessive whitespace and newlines
  let formatted = value.replace(/\s+/g, ' ').trim()
  
  // For display purposes, we can optionally remove the protective braces
  // while keeping the content intact. This makes it more readable.
  // For example: "{IEEE} Trans. Knowl. Data Eng." -> "IEEE Trans. Knowl. Data Eng."
  // But we keep them in the raw view for accuracy
  
  // Only remove braces that are used for protection (single braced words)
  // Pattern: {WORD} -> WORD, but keep {multiple words together}
  formatted = formatted.replace(/\{([A-Z]+)\}/g, '$1')
  
  // If the entire value is wrapped in extra braces, remove them
  if (formatted.startsWith('{') && formatted.endsWith('}')) {
    // Count braces to ensure they're balanced and outer
    let depth = 0
    let isOuter = true
    for (let i = 0; i < formatted.length - 1; i++) {
      if (formatted[i] === '{') depth++
      else if (formatted[i] === '}') depth--
      if (depth === 0 && i < formatted.length - 1) {
        isOuter = false
        break
      }
    }
    if (isOuter) {
      formatted = formatted.slice(1, -1).trim()
    }
  }
  
  return formatted
}


function getEntryTypeLabel(type: string): string {
  const labels: { [key: string]: string } = {
    article: 'Journal Article',
    inproceedings: 'Conference Paper',
    book: 'Book',
    incollection: 'Book Chapter',
    phdthesis: 'PhD Thesis',
    mastersthesis: 'Master\'s Thesis',
    techreport: 'Technical Report',
    misc: 'Miscellaneous',
    proceedings: 'Proceedings'
  }
  return labels[type.toLowerCase()] || type
}

function getEntryTypeColor(type: string): string {
  const colors: { [key: string]: string } = {
    article: 'bg-green-100 text-green-800',
    inproceedings: 'bg-blue-100 text-blue-800',
    book: 'bg-purple-100 text-purple-800',
    incollection: 'bg-indigo-100 text-indigo-800',
    phdthesis: 'bg-yellow-100 text-yellow-800',
    mastersthesis: 'bg-orange-100 text-orange-800',
    techreport: 'bg-gray-100 text-gray-800',
    misc: 'bg-slate-100 text-slate-800',
    proceedings: 'bg-cyan-100 text-cyan-800'
  }
  return colors[type.toLowerCase()] || 'bg-gray-100 text-gray-800'
}

export default function BibTeXViewer({
  bibtex,
  paperId,
  title,
  authors = [],
  year,
  conference,
  journal,
  doi,
  dblpKey,
  dblpUrl,
  className
}: BibTeXViewerProps) {
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState<'formatted' | 'raw'>('formatted')

  const parsedBibTeX = useMemo(() => {
    if (!bibtex) return null
    return parseBibTeX(bibtex)
  }, [bibtex])

  const handleCopyBibTeX = () => {
    if (bibtex) {
      navigator.clipboard.writeText(bibtex)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleDownloadBibTeX = () => {
    if (bibtex) {
      const blob = new Blob([bibtex], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const filename = parsedBibTeX?.key || paperId || 'paper'
      a.download = `${filename}.bib`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  // Generate BibTeX if not available but we have metadata
  const generatedBibTeX = useMemo(() => {
    if (bibtex) return null
    if (!title) return null

    const entryType = journal ? 'article' : conference ? 'inproceedings' : 'misc'
    const key = `paper${paperId || new Date().getTime()}`

    let bib = `@${entryType}{${key},\n`

    if (title) {
      bib += `  title = {${title}},\n`
    }

    if (authors && authors.length > 0) {
      // Handle both string and array formats for authors
      let authorArray: string[]
      if (Array.isArray(authors)) {
        authorArray = authors
      } else if (typeof authors === 'string') {
        // Split comma-separated string into array
        authorArray = authors.split(',').map(a => a.trim())
      } else {
        authorArray = []
      }

      if (authorArray.length > 0) {
        const authorString = authorArray.join(' and ')
        bib += `  author = {${authorString}},\n`
      }
    }

    if (year) {
      bib += `  year = {${year}},\n`
    }

    if (journal) {
      bib += `  journal = {${journal}},\n`
    } else if (conference) {
      bib += `  booktitle = {${conference}},\n`
    }

    if (doi) {
      bib += `  doi = {${doi}},\n`
    }

    // Remove trailing comma and newline
    bib = bib.slice(0, -2) + '\n}'

    return bib
  }, [bibtex, title, authors, year, journal, conference, doi, paperId])

  const displayBibTeX = bibtex || generatedBibTeX

  if (!displayBibTeX) {
    return (
      <Card className={cn("w-full", className)}>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center text-gray-500 py-8">
            <FileText className="h-5 w-5 mr-2" />
            <span>No BibTeX citation available for this paper.</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn("w-full", className)}>
      <CardContent className="pt-6">
        <div className="space-y-4">
          {/* Header with title and actions */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-gray-600" />
              <h3 className="text-lg font-semibold">BibTeX Citation</h3>
              {parsedBibTeX && (
                <Badge className={cn("ml-2", getEntryTypeColor(parsedBibTeX.type))}>
                  {getEntryTypeLabel(parsedBibTeX.type)}
                </Badge>
              )}
              {!bibtex && generatedBibTeX && (
                <Badge variant="outline" className="ml-2">
                  Generated
                </Badge>
              )}
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={handleDownloadBibTeX}
              >
                <Download className="h-4 w-4 mr-1" />
                Download
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleCopyBibTeX}
              >
                {copied ? (
                  <>
                    <CheckCircle className="h-4 w-4 mr-1 text-green-600" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4 mr-1" />
                    Copy
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Citation preview */}
          <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
            Use this BibTeX entry to cite this paper in your research
          </div>

          {/* Tabs for formatted and raw view */}
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'formatted' | 'raw')}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="formatted">
                <FileText className="h-4 w-4 mr-2" />
                Formatted
              </TabsTrigger>
              <TabsTrigger value="raw">
                <Code className="h-4 w-4 mr-2" />
                Raw BibTeX
              </TabsTrigger>
            </TabsList>

            <TabsContent value="formatted" className="mt-4">
              {parsedBibTeX ? (
                <div className="space-y-3">
                  {/* Entry key */}
                  <div className="flex items-start gap-3">
                    <Hash className="h-4 w-4 text-gray-400 mt-0.5" />
                    <div className="flex-1">
                      <div className="text-xs text-gray-500 uppercase">Citation Key</div>
                      <div className="font-mono text-sm">{parsedBibTeX.key}</div>
                    </div>
                  </div>

                  {/* Title */}
                  {parsedBibTeX.fields.title && (
                    <div className="flex items-start gap-3">
                      <FileText className="h-4 w-4 text-gray-400 mt-0.5" />
                      <div className="flex-1">
                        <div className="text-xs text-gray-500 uppercase">Title</div>
                        <div className="text-sm">{formatFieldValue(parsedBibTeX.fields.title)}</div>
                      </div>
                    </div>
                  )}

                  {/* Authors */}
                  {parsedBibTeX.fields.author && (
                    <div className="flex items-start gap-3">
                      <User className="h-4 w-4 text-gray-400 mt-0.5" />
                      <div className="flex-1">
                        <div className="text-xs text-gray-500 uppercase">Authors</div>
                        <div className="text-sm">
                          {formatFieldValue(parsedBibTeX.fields.author)
                            .split(' and ')
                            .map((author, idx) => (
                              <span key={idx}>
                                {idx > 0 && <span className="text-gray-400"> • </span>}
                                {author.trim()}
                              </span>
                            ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Year */}
                  {parsedBibTeX.fields.year && (
                    <div className="flex items-start gap-3">
                      <Calendar className="h-4 w-4 text-gray-400 mt-0.5" />
                      <div className="flex-1">
                        <div className="text-xs text-gray-500 uppercase">Year</div>
                        <div className="text-sm">{parsedBibTeX.fields.year}</div>
                      </div>
                    </div>
                  )}

                  {/* Venue */}
                  {(parsedBibTeX.fields.journal || parsedBibTeX.fields.booktitle) && (
                    <div className="flex items-start gap-3">
                      <Building className="h-4 w-4 text-gray-400 mt-0.5" />
                      <div className="flex-1">
                        <div className="text-xs text-gray-500 uppercase">
                          {parsedBibTeX.fields.journal ? 'Journal' : 'Conference/Book'}
                        </div>
                        <div className="text-sm">
                          {formatFieldValue(parsedBibTeX.fields.journal || parsedBibTeX.fields.booktitle)}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* DOI */}
                  {parsedBibTeX.fields.doi && (
                    <div className="flex items-start gap-3">
                      <Link className="h-4 w-4 text-gray-400 mt-0.5" />
                      <div className="flex-1">
                        <div className="text-xs text-gray-500 uppercase">DOI</div>
                        <a 
                          href={`https://doi.org/${parsedBibTeX.fields.doi}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:underline"
                        >
                          {parsedBibTeX.fields.doi}
                        </a>
                      </div>
                    </div>
                  )}

                  {/* Additional fields */}
                  {parsedBibTeX.fields.volume && (
                    <div className="flex items-start gap-3">
                      <BookOpen className="h-4 w-4 text-gray-400 mt-0.5" />
                      <div className="flex-1">
                        <div className="text-xs text-gray-500 uppercase">Volume</div>
                        <div className="text-sm">
                          {parsedBibTeX.fields.volume}
                          {parsedBibTeX.fields.number && ` (${parsedBibTeX.fields.number})`}
                          {parsedBibTeX.fields.pages && `, pp. ${parsedBibTeX.fields.pages}`}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <pre className="bg-gray-50 p-4 rounded-lg text-xs font-mono overflow-x-auto">
                  {displayBibTeX}
                </pre>
              )}
            </TabsContent>

            <TabsContent value="raw" className="mt-4">
              <pre className="bg-gray-50 p-4 rounded-lg text-xs font-mono overflow-x-auto">
                {displayBibTeX}
              </pre>
            </TabsContent>
          </Tabs>

          {/* DBLP Link if available */}
          {(dblpKey || dblpUrl) && (
            <div className="pt-2 border-t">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-500">Source:</span>
                {dblpUrl ? (
                  <a 
                    href={dblpUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline flex items-center gap-1"
                  >
                    DBLP
                    <Link className="h-3 w-3" />
                  </a>
                ) : (
                  <span className="font-mono text-xs">{dblpKey}</span>
                )}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}