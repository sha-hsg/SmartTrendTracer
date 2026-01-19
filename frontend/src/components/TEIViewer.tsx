import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { FileCode, Download, Copy, CheckCircle, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'

interface TEIViewerProps {
  paperId: number
  paperTitle?: string
}

export default function TEIViewer({ paperId, paperTitle }: TEIViewerProps) {
  const [teiXml, setTeiXml] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [viewMode, setViewMode] = useState<'raw' | 'formatted'>('formatted')

  const loadTeiXml = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await axios.get(
        `http://localhost:8000/api/papers/${paperId}/tei`,
        { responseType: 'text' }
      )
      setTeiXml(response.data)
    } catch (err: any) {
      if (err.response?.status === 404) {
        setError('TEI XML not available. Process the paper with GROBID first.')
        // Don't log 404 errors as they're expected for papers without TEI
      } else {
        setError('Failed to load TEI XML')
        console.error('Error loading TEI XML:', err)
      }
    } finally {
      setLoading(false)
    }
  }

  const formatXml = (xml: string): string => {
    // Basic XML formatting for better readability
    const PADDING = '  '
    const reg = /(>)(<)(\/*)/g
    let formatted = ''
    let pad = 0

    xml = xml.replace(reg, '$1\r\n$2$3')
    const lines = xml.split('\r\n')

    lines.forEach(line => {
      let indent = 0
      if (line.match(/.+<\/\w[^>]*>$/)) {
        indent = 0
      } else if (line.match(/^<\/\w/)) {
        if (pad !== 0) {
          pad -= 1
        }
      } else if (line.match(/^<\w[^>]*[^\/]>.*$/)) {
        indent = 1
      } else {
        indent = 0
      }

      formatted += PADDING.repeat(pad) + line + '\r\n'
      pad += indent
    })

    return formatted
  }

  const extractSections = (xml: string) => {
    // Extract key sections from TEI XML for formatted view
    const sections: { title: string; content: string }[] = []
    
    // Extract title
    const titleMatch = xml.match(/<title[^>]*>(.*?)<\/title>/s)
    if (titleMatch) {
      sections.push({ title: 'Title', content: titleMatch[1].trim() })
    }
    
    // Extract authors
    const authorsMatch = xml.match(/<sourceDesc>(.*?)<\/sourceDesc>/s)
    if (authorsMatch) {
      const authorNames: string[] = []
      const authorRegex = /<persName[^>]*>.*?<forename[^>]*>(.*?)<\/forename>.*?<surname[^>]*>(.*?)<\/surname>.*?<\/persName>/gs
      let match
      while ((match = authorRegex.exec(authorsMatch[1])) !== null) {
        authorNames.push(`${match[1]} ${match[2]}`)
      }
      if (authorNames.length > 0) {
        sections.push({ title: 'Authors', content: authorNames.join(', ') })
      }
    }
    
    // Extract abstract
    const abstractMatch = xml.match(/<abstract[^>]*>(.*?)<\/abstract>/s)
    if (abstractMatch) {
      const cleanAbstract = abstractMatch[1].replace(/<[^>]+>/g, '').trim()
      sections.push({ title: 'Abstract', content: cleanAbstract })
    }
    
    // Extract keywords
    const keywordsMatch = xml.match(/<keywords[^>]*>(.*?)<\/keywords>/s)
    if (keywordsMatch) {
      const keywords: string[] = []
      const termRegex = /<term[^>]*>(.*?)<\/term>/g
      let match
      while ((match = termRegex.exec(keywordsMatch[1])) !== null) {
        keywords.push(match[1])
      }
      if (keywords.length > 0) {
        sections.push({ title: 'Keywords', content: keywords.join(', ') })
      }
    }
    
    return sections
  }

  const copyToClipboard = () => {
    if (teiXml) {
      navigator.clipboard.writeText(teiXml)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const downloadXml = () => {
    if (teiXml) {
      const blob = new Blob([teiXml], { type: 'application/xml' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `paper_${paperId}_tei.xml`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  useEffect(() => {
    loadTeiXml()
  }, [paperId])

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileCode className="h-5 w-5" />
              TEI XML Viewer
            </CardTitle>
            <CardDescription>
              Structured XML representation from GROBID processing
            </CardDescription>
          </div>
          {teiXml && (
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={copyToClipboard}
              >
                {copied ? (
                  <>
                    <CheckCircle className="h-4 w-4 mr-1 text-green-600" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4 mr-1" />
                    Copy
                  </>
                )}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={downloadXml}
              >
                <Download className="h-4 w-4 mr-1" />
                Download
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      
      <CardContent>
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
            <span className="ml-2 text-gray-600">Loading TEI XML...</span>
          </div>
        )}
        
        {error && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {teiXml && !loading && !error && (
          <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'raw' | 'formatted')}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="formatted">Formatted View</TabsTrigger>
              <TabsTrigger value="raw">Raw XML</TabsTrigger>
            </TabsList>
            
            <TabsContent value="formatted" className="mt-4">
              <div className="space-y-4">
                {extractSections(teiXml).map((section, idx) => (
                  <div key={idx} className="border-l-4 border-blue-200 pl-4">
                    <h3 className="font-semibold text-sm text-gray-700 mb-1">
                      {section.title}
                    </h3>
                    <p className="text-sm text-gray-600 whitespace-pre-wrap">
                      {section.content}
                    </p>
                  </div>
                ))}
              </div>
            </TabsContent>
            
            <TabsContent value="raw" className="mt-4">
              <ScrollArea className="h-[500px] w-full rounded-md border p-4">
                <pre className="text-xs font-mono text-gray-700">
                  {formatXml(teiXml)}
                </pre>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        )}
      </CardContent>
    </Card>
  )
}