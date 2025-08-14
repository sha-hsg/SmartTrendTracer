import React, { useState, useEffect } from 'react'
import axios from 'axios'
import {
  Brain,
  Download,
  GitBranch,
  Sparkles,
  FileText,
  Users,
  Link,
  Loader2,
  AlertCircle,
  ChevronRight,
  BookOpen,
  Target,
  MessageSquare,
  Github,
  ArrowUpRight,
  Plus
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import PaperKnowledgeGraph from './PaperKnowledgeGraph'

interface PaperRecommendation {
  id: number
  title: string
  abstract?: string
  similarity_score: number
  common_tags: string[]
  publication_date?: string
  authors: { name: string; affiliation?: string }[]
  reason: string
}

interface PaperSummary {
  paper_id: number
  title: string
  summary: string
  key_insights: string
  tags: string[]
  generated_at: string
  error?: string
}

interface PaperAdvancedDashboardProps {
  paperId?: number
}

const PaperAdvancedDashboard: React.FC<PaperAdvancedDashboardProps> = ({ paperId }) => {
  const [activeTab, setActiveTab] = useState('recommendations')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Data states
  const [recommendations, setRecommendations] = useState<PaperRecommendation[]>([])
  const [summary, setSummary] = useState<PaperSummary | null>(null)
  const [githubLinks, setGithubLinks] = useState<string[]>([])
  const [selectedPaperId, setSelectedPaperId] = useState<number | undefined>(paperId)
  
  // ArXiv import
  const [arxivDialogOpen, setArxivDialogOpen] = useState(false)
  const [arxivId, setArxivId] = useState('')
  const [importingArxiv, setImportingArxiv] = useState(false)

  useEffect(() => {
    if (selectedPaperId) {
      fetchRecommendations()
      fetchGithubLinks()
    }
  }, [selectedPaperId])

  const fetchRecommendations = async () => {
    if (!selectedPaperId) return
    
    setLoading(true)
    setError(null)
    
    try {
      const response = await axios.get(
        `http://localhost:8000/api/papers/advanced/recommendations/${selectedPaperId}`
      )
      setRecommendations(response.data.recommendations)
    } catch (err) {
      setError('Failed to fetch recommendations')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const generateSummary = async () => {
    if (!selectedPaperId) return
    
    setLoading(true)
    setError(null)
    
    try {
      const response = await axios.post(
        'http://localhost:8000/api/papers/advanced/summarize',
        { paper_id: selectedPaperId, include_insights: true }
      )
      setSummary(response.data)
    } catch (err) {
      setError('Failed to generate summary')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchGithubLinks = async () => {
    if (!selectedPaperId) return
    
    try {
      const response = await axios.get(
        `http://localhost:8000/api/papers/advanced/github-links/${selectedPaperId}`
      )
      setGithubLinks(response.data.github_links)
    } catch (err) {
      console.error('Error fetching GitHub links:', err)
    }
  }

  const importFromArxiv = async () => {
    if (!arxivId) return
    
    setImportingArxiv(true)
    
    try {
      const response = await axios.post(
        'http://localhost:8000/api/papers/advanced/import-arxiv',
        { arxiv_id: arxivId }
      )
      
      if (response.data.status === 'success') {
        setSelectedPaperId(response.data.paper_id)
        setArxivDialogOpen(false)
        setArxivId('')
        
        // Show success message
        alert(`Paper imported successfully: ${response.data.title}`)
      } else if (response.data.status === 'exists') {
        setSelectedPaperId(response.data.paper_id)
        setArxivDialogOpen(false)
        alert('Paper already exists in database')
      } else {
        alert(response.data.message || 'Import failed')
      }
    } catch (err) {
      alert('Failed to import from ArXiv')
      console.error('Error:', err)
    } finally {
      setImportingArxiv(false)
    }
  }

  const formatSummary = (text: string) => {
    return text.split('\n').map((line, idx) => {
      if (line.startsWith('**') && line.endsWith('**')) {
        return (
          <h4 key={idx} className="font-semibold mt-3 mb-1">
            {line.replace(/\*\*/g, '')}
          </h4>
        )
      }
      if (line.startsWith('•') || line.startsWith('-')) {
        return (
          <li key={idx} className="ml-4 text-sm text-gray-700">
            {line.substring(1).trim()}
          </li>
        )
      }
      if (line.trim()) {
        return <p key={idx} className="text-sm text-gray-700 mb-2">{line}</p>
      }
      return null
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-6 w-6" />
                Advanced Paper Analytics
              </CardTitle>
              <CardDescription>
                AI-powered insights, recommendations, and knowledge graphs
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={() => setArxivDialogOpen(true)}
              >
                <Download className="h-4 w-4 mr-2" />
                Import from ArXiv
              </Button>
              {selectedPaperId && (
                <Badge variant="outline">
                  Paper ID: {selectedPaperId}
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          <TabsTrigger value="summary">AI Summary</TabsTrigger>
          <TabsTrigger value="knowledge-graph">Knowledge Graph</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
        </TabsList>

        <TabsContent value="recommendations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Similar Papers
              </CardTitle>
              <CardDescription>
                Papers with similar topics and research areas
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!selectedPaperId ? (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Select a paper or import from ArXiv to see recommendations
                  </AlertDescription>
                </Alert>
              ) : loading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : recommendations.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No recommendations available
                </p>
              ) : (
                <ScrollArea className="h-[500px]">
                  <div className="space-y-4">
                    {recommendations.map((rec) => (
                      <Card key={rec.id} className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-medium text-sm flex-1">
                            {rec.title}
                          </h4>
                          <Badge className="ml-2">
                            {Math.round(rec.similarity_score * 100)}% match
                          </Badge>
                        </div>
                        
                        {rec.abstract && (
                          <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                            {rec.abstract}
                          </p>
                        )}
                        
                        <div className="flex items-center gap-2 mb-2">
                          {rec.common_tags.slice(0, 3).map((tag) => (
                            <Badge key={tag} variant="outline" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                          {rec.common_tags.length > 3 && (
                            <span className="text-xs text-gray-500">
                              +{rec.common_tags.length - 3} more
                            </span>
                          )}
                        </div>
                        
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>{rec.reason}</span>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setSelectedPaperId(rec.id)}
                          >
                            View
                            <ChevronRight className="h-3 w-3 ml-1" />
                          </Button>
                        </div>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="summary" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <BookOpen className="h-5 w-5" />
                    AI-Generated Summary
                  </CardTitle>
                  <CardDescription>
                    Key findings and insights extracted by AI
                  </CardDescription>
                </div>
                {selectedPaperId && !summary && (
                  <Button onClick={generateSummary} disabled={loading}>
                    {loading ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Sparkles className="h-4 w-4 mr-2" />
                    )}
                    Generate Summary
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {!selectedPaperId ? (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Select a paper to generate summary
                  </AlertDescription>
                </Alert>
              ) : !summary ? (
                <div className="text-center py-8 text-gray-500">
                  Click "Generate Summary" to create an AI summary
                </div>
              ) : summary.error ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{summary.error}</AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">Paper Title</h3>
                    <p className="text-sm text-gray-700">{summary.title}</p>
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <h3 className="font-semibold mb-2">Summary</h3>
                    <div className="prose prose-sm max-w-none">
                      {formatSummary(summary.summary)}
                    </div>
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <h3 className="font-semibold mb-2">Key Insights</h3>
                    <div className="prose prose-sm max-w-none">
                      {formatSummary(summary.key_insights)}
                    </div>
                  </div>
                  
                  {summary.tags.length > 0 && (
                    <>
                      <Separator />
                      <div>
                        <h3 className="font-semibold mb-2">Research Topics</h3>
                        <div className="flex flex-wrap gap-2">
                          {summary.tags.map((tag) => (
                            <Badge key={tag} variant="secondary">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </>
                  )}
                  
                  <div className="text-xs text-gray-500 mt-4">
                    Generated: {new Date(summary.generated_at).toLocaleString()}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="knowledge-graph">
          <PaperKnowledgeGraph 
            paperId={selectedPaperId}
            onNodeClick={(node) => {
              if (node.id?.startsWith('paper_')) {
                const id = parseInt(node.id.replace('paper_', ''))
                setSelectedPaperId(id)
              }
            }}
          />
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Link className="h-5 w-5" />
                External Resources
              </CardTitle>
              <CardDescription>
                Code repositories and external links
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!selectedPaperId ? (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Select a paper to see resources
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-4">
                  {/* GitHub Links */}
                  <div>
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Github className="h-4 w-4" />
                      GitHub Repositories
                    </h4>
                    {githubLinks.length === 0 ? (
                      <p className="text-sm text-gray-500">
                        No GitHub links found in paper
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {githubLinks.map((link, idx) => (
                          <div key={idx} className="flex items-center gap-2">
                            <a
                              href={link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                            >
                              {link}
                              <ArrowUpRight className="h-3 w-3" />
                            </a>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <Separator />
                  
                  {/* Other Resources */}
                  <div>
                    <h4 className="font-medium mb-2">Additional Resources</h4>
                    <div className="space-y-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full justify-start"
                        onClick={() => {
                          // Would integrate with Semantic Scholar API
                          alert('Semantic Scholar integration coming soon')
                        }}
                      >
                        <Target className="h-4 w-4 mr-2" />
                        View on Semantic Scholar
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full justify-start"
                        onClick={() => {
                          // Would search for paper on Google Scholar
                          alert('Google Scholar integration coming soon')
                        }}
                      >
                        <BookOpen className="h-4 w-4 mr-2" />
                        Search on Google Scholar
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* ArXiv Import Dialog */}
      <Dialog open={arxivDialogOpen} onOpenChange={setArxivDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Import Paper from ArXiv</DialogTitle>
            <DialogDescription>
              Enter an ArXiv ID to import the paper into your database
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">ArXiv ID</label>
              <Input
                placeholder="e.g., 2301.12345 or https://arxiv.org/abs/2301.12345"
                value={arxivId}
                onChange={(e) => setArxivId(e.target.value)}
              />
              <p className="text-xs text-gray-500 mt-1">
                Enter the ArXiv ID or full URL
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setArxivDialogOpen(false)}
              disabled={importingArxiv}
            >
              Cancel
            </Button>
            <Button
              onClick={importFromArxiv}
              disabled={!arxivId || importingArxiv}
            >
              {importingArxiv ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Importing...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Import
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}

export default PaperAdvancedDashboard