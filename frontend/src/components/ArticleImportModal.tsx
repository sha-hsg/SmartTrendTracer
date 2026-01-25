import { useState, useEffect } from 'react'
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
  Download,
  Key,
  Shield,
  ShieldCheck,
  ShieldX,
  ExternalLink,
  Terminal,
  Copy,
  Check
} from 'lucide-react'

interface AuthSite {
  key: string
  name: string
  login_url: string
  has_session: boolean
  session_info?: {
    created_at?: string
    last_used?: string
    cookie_count?: number
    is_valid?: boolean
  }
}

interface ArticleImportModalProps {
  isOpen: boolean
  onClose: () => void
  onImportSuccess: () => void
}

export default function ArticleImportModal({ isOpen, onClose, onImportSuccess }: ArticleImportModalProps) {
  const [singleUrl, setSingleUrl] = useState('')
  const [batchUrls, setBatchUrls] = useState('')
  const [authUrl, setAuthUrl] = useState('')
  const [isImporting, setIsImporting] = useState(false)
  const [importResult, setImportResult] = useState<any>(null)
  const [batchResults, setBatchResults] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  // Authentication states
  const [authSites, setAuthSites] = useState<AuthSite[]>([])
  const [loadingAuthSites, setLoadingAuthSites] = useState(false)
  const [playwrightInstalled, setPlaywrightInstalled] = useState(true)
  const [authInstructions, setAuthInstructions] = useState<{
    site: string
    name: string
    instructions: string
    cli_command: string
  } | null>(null)
  const [copiedCommand, setCopiedCommand] = useState<string | null>(null)
  const [authenticatingSite, setAuthenticatingSite] = useState<string | null>(null)

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedCommand(id)
      setTimeout(() => setCopiedCommand(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleStartAuth = async (siteKey: string) => {
    setAuthenticatingSite(siteKey)
    setError(null)
    try {
      const response = await axios.post(`http://localhost:8000/api/v2/articles/start-auth/${siteKey}`)
      if (response.data.success) {
        // Reload auth sites to show updated status
        await loadAuthSites()
      } else {
        setError(response.data.message || 'Authentication failed')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start authentication')
    } finally {
      setAuthenticatingSite(null)
    }
  }

  // Load auth sites when modal opens
  useEffect(() => {
    if (isOpen) {
      loadAuthSites()
    }
  }, [isOpen])

  const loadAuthSites = async () => {
    setLoadingAuthSites(true)
    try {
      const response = await axios.get('http://localhost:8000/api/v2/articles/auth-sites')
      setAuthSites(response.data.sites || [])
      setPlaywrightInstalled(response.data.playwright_installed ?? true)
    } catch (err) {
      console.error('Failed to load auth sites:', err)
    } finally {
      setLoadingAuthSites(false)
    }
  }

  const handleAuthImport = async () => {
    if (!authUrl.trim()) {
      setError('Please enter a URL')
      return
    }

    setIsImporting(true)
    setError(null)
    setImportResult(null)
    setAuthInstructions(null)

    try {
      // Use Playwright-based endpoint for authenticated imports
      const response = await axios.post('http://localhost:8000/api/v2/articles/import-url-playwright', {
        url: authUrl
      })

      if (response.data.success) {
        setImportResult(response.data)
        onImportSuccess()
        setTimeout(() => {
          setAuthUrl('')
          setImportResult(null)
        }, 3000)
      } else if (response.data.requires_auth) {
        // Show auth instructions
        const site = response.data.site
        const instrResponse = await axios.post(`http://localhost:8000/api/v2/articles/start-auth/${site}`)
        setAuthInstructions(instrResponse.data)
        setError(`Authentication required for ${site}`)
      } else {
        setError(response.data.error || 'Failed to import article')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import article')
    } finally {
      setIsImporting(false)
    }
  }

  const handleClearSession = async (site: string) => {
    try {
      await axios.delete(`http://localhost:8000/api/v2/articles/auth/${site}`)
      loadAuthSites()
    } catch (err) {
      console.error('Failed to clear session:', err)
    }
  }

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
      setAuthUrl('')
      setImportResult(null)
      setBatchResults([])
      setError(null)
      setAuthInstructions(null)
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
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="single">Single URL</TabsTrigger>
            <TabsTrigger value="batch">Batch Import</TabsTrigger>
            <TabsTrigger value="auth" className="flex items-center gap-1">
              <Key className="h-3 w-3" />
              Authenticated
            </TabsTrigger>
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

          <TabsContent value="auth" className="space-y-4">
            {/* Playwright not installed warning */}
            {!playwrightInstalled && (
              <Alert className="border-amber-200 bg-amber-50">
                <Terminal className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-800">
                  <div className="font-semibold">Playwright not installed</div>
                  <div className="text-sm mt-1">
                    Run in terminal: <code className="bg-amber-100 px-1 rounded">pip install playwright && playwright install chromium</code>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {/* Auth Sites Status */}
            {loadingAuthSites ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                <span className="ml-2 text-sm text-gray-500">Loading sessions...</span>
              </div>
            ) : (
              <div className="space-y-3">
                <Label className="text-sm font-medium">Authentication Status</Label>
                <div className="grid gap-2">
                  {authSites.map((site) => {
                    const authCommand = `cd backend && python -m app.collectors.playwright_article_collector --auth ${site.key}`
                    return (
                      <div key={site.key} className="p-3 border rounded-lg bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {site.has_session ? (
                              <ShieldCheck className="h-4 w-4 text-green-600" />
                            ) : (
                              <ShieldX className="h-4 w-4 text-gray-400" />
                            )}
                            <span className="font-medium">{site.name}</span>
                            {site.has_session && (
                              <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                                Authenticated
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            {site.has_session && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleClearSession(site.key)}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              >
                                Clear
                              </Button>
                            )}
                            <a
                              href={site.login_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                            >
                              <ExternalLink className="h-3 w-3" />
                              Login
                            </a>
                          </div>
                        </div>
                        {!site.has_session && (
                          <div className="mt-2 space-y-2">
                            {/* Authenticate Button */}
                            <Button
                              onClick={() => handleStartAuth(site.key)}
                              disabled={authenticatingSite !== null}
                              className="w-full bg-green-600 hover:bg-green-700"
                            >
                              {authenticatingSite === site.key ? (
                                <>
                                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                  Opening browser... Please log in
                                </>
                              ) : (
                                <>
                                  <Key className="h-4 w-4 mr-2" />
                                  Authenticate Now
                                </>
                              )}
                            </Button>
                            {/* Alternative: CLI command */}
                            <div className="flex items-center gap-2">
                              <code className="flex-1 text-xs bg-gray-200 px-2 py-1.5 rounded font-mono overflow-x-auto">
                                {authCommand}
                              </code>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => copyToClipboard(authCommand, site.key)}
                                className="shrink-0"
                              >
                                {copiedCommand === site.key ? (
                                  <Check className="h-3 w-3 text-green-600" />
                                ) : (
                                  <Copy className="h-3 w-3" />
                                )}
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
                <p className="text-xs text-gray-500">
                  Click "Authenticate Now" to open a browser window for login. Alternatively, run the CLI command in terminal.
                </p>
              </div>
            )}

            {/* URL Input for authenticated import */}
            <div className="space-y-2 pt-2 border-t">
              <Label htmlFor="auth-url">Article URL (requires authentication)</Label>
              <div className="flex gap-2">
                <Input
                  id="auth-url"
                  type="url"
                  placeholder="https://example.substack.com/p/subscriber-only-article"
                  value={authUrl}
                  onChange={(e) => setAuthUrl(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !isImporting) {
                      handleAuthImport()
                    }
                  }}
                  disabled={isImporting || !playwrightInstalled}
                />
                <Button
                  onClick={handleAuthImport}
                  disabled={isImporting || !authUrl.trim() || !playwrightInstalled}
                >
                  {isImporting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Shield className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Auth Instructions */}
            {authInstructions && (
              <Alert className="border-blue-200 bg-blue-50">
                <Terminal className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  <div className="font-semibold">Authentication required for {authInstructions.name}</div>
                  <div className="mt-2 space-y-2">
                    <Button
                      onClick={() => handleStartAuth(authInstructions.site)}
                      disabled={authenticatingSite !== null}
                      className="w-full bg-blue-600 hover:bg-blue-700"
                    >
                      {authenticatingSite === authInstructions.site ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Opening browser... Please log in
                        </>
                      ) : (
                        <>
                          <Key className="h-4 w-4 mr-2" />
                          Authenticate with {authInstructions.name}
                        </>
                      )}
                    </Button>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 text-xs bg-blue-100 px-2 py-1.5 rounded font-mono">
                        cd backend && {authInstructions.cli_command}
                      </code>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(`cd backend && ${authInstructions.cli_command}`, 'auth-instr')}
                        className="shrink-0 bg-white"
                      >
                        {copiedCommand === 'auth-instr' ? (
                          <Check className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </div>
                  <div className="text-xs mt-2">
                    After logging in, try importing again.
                  </div>
                </AlertDescription>
              </Alert>
            )}

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
                    By {importResult.author} {importResult.word_count} words
                    {importResult.has_paywall && <span className="text-amber-600"> (partial - paywall)</span>}
                  </div>
                </AlertDescription>
              </Alert>
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