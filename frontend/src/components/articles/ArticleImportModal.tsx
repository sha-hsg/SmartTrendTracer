import { useState, useEffect } from 'react'
import http from '@/services/http'
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
  Check,
  Cookie,
  FileText,
  Lock
} from 'lucide-react'
import type { AuthSite, ArticleImportModalProps } from './ArticleImportModal.types'

export default function ArticleImportModal({ isOpen, onClose, onImportSuccess }: ArticleImportModalProps) {
  const [activeTab, setActiveTab] = useState<string>('single')
  const [singleUrl, setSingleUrl] = useState('')
  const [batchUrls, setBatchUrls] = useState('')
  const [authUrl, setAuthUrl] = useState('')
  const [isImporting, setIsImporting] = useState(false)
  const [importResult, setImportResult] = useState<any>(null)
  const [batchResults, setBatchResults] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  // Authentication states (Playwright)
  const [authSites, setAuthSites] = useState<AuthSite[]>([])
  const [loadingAuthSites, setLoadingAuthSites] = useState(false)
  const [playwrightInstalled, setPlaywrightInstalled] = useState(true)
  const [authInstructions, setAuthInstructions] = useState<{
    site: string
    name: string
    instructions: string
    cli_command: string
  } | null>(null)
  // Hint shown in Auth tab after smart-dispatch redirect from Single tab
  const [authRequiredHint, setAuthRequiredHint] = useState<{
    site: string
    site_name: string
    message: string
  } | null>(null)
  const [copiedCommand, setCopiedCommand] = useState<string | null>(null)
  const [authenticatingSite, setAuthenticatingSite] = useState<string | null>(null)

  // Cookie/cURL import states
  const [cookieUrl, setCookieUrl] = useState('')
  const [cookieString, setCookieString] = useState('')
  const [curlCommand, setCurlCommand] = useState('')
  const [cookieJson, setCookieJson] = useState('')
  const [isCheckingPaywall, setIsCheckingPaywall] = useState(false)
  const [paywallStatus, setPaywallStatus] = useState<any>(null)

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
      const response = await http.post(`/api/v2/articles/start-auth/${siteKey}`)
      if (response.data.success) {
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

  useEffect(() => {
    if (isOpen) {
      loadAuthSites()
    }
  }, [isOpen])

  const loadAuthSites = async () => {
    setLoadingAuthSites(true)
    try {
      const response = await http.get(`/api/v2/articles/auth-sites`)
      setAuthSites(response.data.sites || [])
      setPlaywrightInstalled(response.data.playwright_installed ?? true)
    } catch (err) {
      console.error('Failed to load auth sites:', err)
    } finally {
      setLoadingAuthSites(false)
    }
  }

  const handleAuthImport = async () => {
    if (!authUrl.trim()) { setError('Please enter a URL'); return }
    setIsImporting(true); setError(null); setImportResult(null); setAuthInstructions(null)
    try {
      const response = await http.post(`/api/v2/articles/import-url-playwright`, { url: authUrl })
      if (response.data.success) {
        setImportResult(response.data)
        onImportSuccess()
        setTimeout(() => { setAuthUrl(''); setImportResult(null) }, 3000)
      } else if (response.data.requires_auth) {
        const site = response.data.site
        const instrResponse = await http.post(`/api/v2/articles/start-auth/${site}`)
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
      await http.delete(`/api/v2/articles/auth/${site}`)
      loadAuthSites()
    } catch (err) {
      console.error('Failed to clear session:', err)
    }
  }

  const handleSingleImport = async () => {
    if (!singleUrl.trim()) { setError('Please enter a URL'); return }
    setIsImporting(true); setError(null); setImportResult(null); setAuthRequiredHint(null)
    try {
      const response = await http.post(`/api/v2/articles/import-url`, { url: singleUrl })
      if (response.data.success) {
        setImportResult(response.data)
        onImportSuccess()
        setTimeout(() => { setSingleUrl(''); setImportResult(null) }, 3000)
      } else if (response.data.requires_auth) {
        // Smart-dispatch: backend recognized an auth-site without a saved session.
        // Switch to Auth tab, pre-fill URL, and explain the next step.
        const siteName = response.data.site_name || 'this site'
        setAuthUrl(singleUrl)
        await loadAuthSites()
        setAuthRequiredHint({
          site: response.data.site,
          site_name: siteName,
          message: `Diese URL benötigt Login bei ${siteName}. Melde dich einmal an — danach laufen alle weiteren Imports automatisch.`,
        })
        setActiveTab('auth')
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
    const urls = batchUrls.split('\n').map(url => url.trim()).filter(url => url.length > 0)
    if (urls.length === 0) { setError('Please enter at least one URL'); return }
    setIsImporting(true); setError(null); setBatchResults([])
    try {
      const response = await http.post(`/api/v2/articles/import-batch`, urls)
      setBatchResults(response.data.results)
      onImportSuccess()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import articles')
    } finally {
      setIsImporting(false)
    }
  }

  const checkPaywall = async () => {
    if (!cookieUrl.trim()) { setError('Please enter a URL'); return }
    setIsCheckingPaywall(true); setError(null); setPaywallStatus(null)
    try {
      const response = await http.post(`/api/v2/articles/enhanced/check-paywall`, null, { params: { url: cookieUrl } })
      setPaywallStatus(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to check article')
    } finally {
      setIsCheckingPaywall(false)
    }
  }

  const handleCookieImport = async () => {
    if (!cookieUrl.trim() || !cookieString.trim()) { setError('Please enter both URL and cookies'); return }
    setIsImporting(true); setError(null); setImportResult(null)
    try {
      const response = await http.post(`/api/v2/articles/enhanced/import-with-cookie-string`, { url: cookieUrl, cookies: cookieString })
      setImportResult(response.data)
      if (response.data.success) {
        onImportSuccess()
        setTimeout(() => { setCookieUrl(''); setCookieString(''); setImportResult(null) }, 3000)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import article with cookies')
    } finally {
      setIsImporting(false)
    }
  }

  const extractUrlFromCurl = (curl: string): string | null => {
    const urlMatch = curl.match(/['"]?(https?:\/\/[^\s'"]+)['"]?/)
    return urlMatch ? urlMatch[1] : null
  }

  const handleCurlImport = async () => {
    if (!curlCommand.trim()) { setError('Please enter a cURL command'); return }
    const importUrl = cookieUrl.trim() || extractUrlFromCurl(curlCommand)
    if (!importUrl) { setError('Could not find URL in cURL command'); return }
    setIsImporting(true); setError(null); setImportResult(null)
    try {
      const response = await http.post(`/api/v2/articles/enhanced/import-with-cookies`, { url: importUrl, curl_command: curlCommand })
      setImportResult(response.data)
      if (response.data.success) {
        onImportSuccess()
        setTimeout(() => { setCookieUrl(''); setCurlCommand(''); setImportResult(null) }, 3000)
      } else if (response.data.error) {
        setError(response.data.error)
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to import with cURL')
    } finally {
      setIsImporting(false)
    }
  }

  const handleJsonImport = async () => {
    if (!cookieUrl.trim() || !cookieJson.trim()) { setError('Please enter both URL and JSON cookies'); return }
    setIsImporting(true); setError(null); setImportResult(null)
    try {
      const response = await http.post(`/api/v2/articles/enhanced/import-with-cookies`, { url: cookieUrl, cookie_json: cookieJson })
      setImportResult(response.data)
      if (response.data.success) {
        onImportSuccess()
        setTimeout(() => { setCookieUrl(''); setCookieJson(''); setImportResult(null) }, 3000)
      } else if (response.data.error) {
        setError(response.data.error)
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to import with JSON cookies')
    } finally {
      setIsImporting(false)
    }
  }

  const handleClose = () => {
    if (!isImporting) {
      setActiveTab('single')
      setSingleUrl(''); setBatchUrls(''); setAuthUrl('')
      setCookieUrl(''); setCookieString(''); setCurlCommand(''); setCookieJson('')
      setImportResult(null); setBatchResults([]); setError(null)
      setAuthInstructions(null); setAuthRequiredHint(null); setPaywallStatus(null)
      onClose()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Import Articles
          </DialogTitle>
          <DialogDescription>
            Import articles from Substack, Medium, blogs, or any web page
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4">
          <TabsList className="grid w-full grid-cols-3 lg:grid-cols-6">
            <TabsTrigger value="single">Single</TabsTrigger>
            <TabsTrigger value="batch">Batch</TabsTrigger>
            <TabsTrigger value="auth"><Key className="h-3 w-3 mr-1" />Auth</TabsTrigger>
            <TabsTrigger value="cookies"><Cookie className="h-3 w-3 mr-1" />Cookie</TabsTrigger>
            <TabsTrigger value="json">JSON</TabsTrigger>
            <TabsTrigger value="curl">cURL</TabsTrigger>
          </TabsList>

          {/* Single URL Tab */}
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
                  onKeyDown={(e) => { if (e.key === 'Enter' && !isImporting) handleSingleImport() }}
                  disabled={isImporting}
                />
                <Button onClick={handleSingleImport} disabled={isImporting || !singleUrl.trim()}>
                  {isImporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                </Button>
              </div>
            </div>
            {renderError()}
            {renderSuccess()}
          </TabsContent>

          {/* Batch Tab */}
          <TabsContent value="batch" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="batch-urls">Article URLs (one per line)</Label>
              <Textarea
                id="batch-urls"
                placeholder={"https://example.substack.com/p/article-1\nhttps://medium.com/@author/article-2"}
                value={batchUrls}
                onChange={(e) => setBatchUrls(e.target.value)}
                rows={6}
                disabled={isImporting}
              />
            </div>
            <Button onClick={handleBatchImport} disabled={isImporting || !batchUrls.trim()} className="w-full">
              {isImporting ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Importing...</> : <><Download className="h-4 w-4 mr-2" />Import All</>}
            </Button>
            {renderError()}
            {batchResults.length > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-medium">Import Results:</div>
                <div className="max-h-64 overflow-y-auto space-y-2 border rounded-lg p-3">
                  {batchResults.map((result, idx) => (
                    <div key={idx} className={`flex items-start gap-2 p-2 rounded ${result.success ? 'bg-green-50' : 'bg-red-50'}`}>
                      {result.success ? <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" /> : <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />}
                      <div className="flex-1 text-sm">
                        <div className="font-medium">{result.success ? result.title : result.url}</div>
                        <div className="text-gray-600">{result.success ? `${result.author} - ${result.word_count} words` : result.error}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>

          {/* Playwright Auth Tab */}
          <TabsContent value="auth" className="space-y-4">
            {authRequiredHint && (
              <Alert className="border-blue-300 bg-blue-50">
                <Lock className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-900">
                  <div className="font-semibold">Login bei {authRequiredHint.site_name} erforderlich</div>
                  <div className="text-sm mt-1">{authRequiredHint.message}</div>
                </AlertDescription>
              </Alert>
            )}
            {!playwrightInstalled && (
              <Alert className="border-amber-200 bg-amber-50">
                <Terminal className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-800">
                  <div className="font-semibold">Playwright not installed</div>
                  <div className="text-sm mt-1">
                    Run: <code className="bg-amber-100 px-1 rounded">pip install playwright && playwright install chromium</code>
                  </div>
                </AlertDescription>
              </Alert>
            )}
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
                            {site.has_session ? <ShieldCheck className="h-4 w-4 text-green-600" /> : <ShieldX className="h-4 w-4 text-gray-400" />}
                            <span className="font-medium">{site.name}</span>
                            {site.has_session && <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Authenticated</span>}
                          </div>
                          <div className="flex items-center gap-2">
                            {site.has_session && (
                              <Button variant="ghost" size="sm" onClick={() => handleClearSession(site.key)} className="text-red-600 hover:text-red-700 hover:bg-red-50">Clear</Button>
                            )}
                            <a href={site.login_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline flex items-center gap-1">
                              <ExternalLink className="h-3 w-3" />Login
                            </a>
                          </div>
                        </div>
                        {!site.has_session && (
                          <div className="mt-2 space-y-2">
                            <Button onClick={() => handleStartAuth(site.key)} disabled={authenticatingSite !== null} className="w-full bg-green-600 hover:bg-green-700">
                              {authenticatingSite === site.key ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Opening browser...</> : <><Key className="h-4 w-4 mr-2" />Authenticate Now</>}
                            </Button>
                            <div className="flex items-center gap-2">
                              <code className="flex-1 text-xs bg-gray-200 px-2 py-1.5 rounded font-mono overflow-x-auto">{authCommand}</code>
                              <Button variant="outline" size="sm" onClick={() => copyToClipboard(authCommand, site.key)} className="shrink-0">
                                {copiedCommand === site.key ? <Check className="h-3 w-3 text-green-600" /> : <Copy className="h-3 w-3" />}
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
            <div className="space-y-2 pt-2 border-t">
              <Label htmlFor="auth-url">Article URL (requires authentication)</Label>
              <div className="flex gap-2">
                <Input id="auth-url" type="url" placeholder="https://example.substack.com/p/subscriber-only-article"
                  value={authUrl} onChange={(e) => setAuthUrl(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !isImporting) handleAuthImport() }}
                  disabled={isImporting || !playwrightInstalled}
                />
                <Button onClick={handleAuthImport} disabled={isImporting || !authUrl.trim() || !playwrightInstalled}>
                  {isImporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Shield className="h-4 w-4" />}
                </Button>
              </div>
            </div>
            {authInstructions && (
              <Alert className="border-blue-200 bg-blue-50">
                <Terminal className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  <div className="font-semibold">Authentication required for {authInstructions.name}</div>
                  <div className="mt-2 space-y-2">
                    <Button onClick={() => handleStartAuth(authInstructions.site)} disabled={authenticatingSite !== null} className="w-full bg-blue-600 hover:bg-blue-700">
                      {authenticatingSite === authInstructions.site ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Opening browser...</> : <><Key className="h-4 w-4 mr-2" />Authenticate with {authInstructions.name}</>}
                    </Button>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 text-xs bg-blue-100 px-2 py-1.5 rounded font-mono">cd backend && {authInstructions.cli_command}</code>
                      <Button variant="outline" size="sm" onClick={() => copyToClipboard(`cd backend && ${authInstructions.cli_command}`, 'auth-instr')} className="shrink-0 bg-white">
                        {copiedCommand === 'auth-instr' ? <Check className="h-3 w-3 text-green-600" /> : <Copy className="h-3 w-3" />}
                      </Button>
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
            )}
            {renderError()}
            {renderSuccess()}
          </TabsContent>

          {/* Cookie String Tab */}
          <TabsContent value="cookies" className="space-y-4">
            {renderCookieUrlInput()}
            <div className="rounded-lg bg-amber-50 p-3">
              <div className="flex gap-2">
                <Cookie className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                <div className="text-xs space-y-1">
                  <p className="font-medium text-amber-900">How to get cookies:</p>
                  <ol className="list-decimal list-inside space-y-0.5 text-amber-700">
                    <li>Open article in browser and sign in</li>
                    <li>Open DevTools (F12) → Application → Cookies</li>
                    <li>Copy cookie string (name=value; name2=value2)</li>
                  </ol>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="cookie-string">Cookie String</Label>
              <Textarea id="cookie-string" placeholder="cookie_name=value; another_cookie=value2; session_id=xyz123"
                value={cookieString} onChange={(e) => setCookieString(e.target.value)} rows={3} disabled={isImporting} className="font-mono text-xs" />
            </div>
            <Button onClick={handleCookieImport} disabled={isImporting || !cookieUrl.trim() || !cookieString.trim()} className="w-full">
              {isImporting ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Importing...</> : <><Cookie className="h-4 w-4 mr-2" />Import with Cookies</>}
            </Button>
            {renderError()}
            {renderSuccess()}
          </TabsContent>

          {/* JSON Cookies Tab */}
          <TabsContent value="json" className="space-y-4">
            {renderCookieUrlInput()}
            <div className="rounded-lg bg-green-50 p-3">
              <div className="flex gap-2">
                <FileText className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                <div className="text-xs space-y-1">
                  <p className="font-medium text-green-900">Using Copy Cookie Extension:</p>
                  <ol className="list-decimal list-inside space-y-0.5 text-green-700">
                    <li>Install "Copy Cookie" browser extension</li>
                    <li>Sign in to the article</li>
                    <li>Click extension → "Copy All" as JSON</li>
                  </ol>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="cookie-json">JSON Cookie Array</Label>
              <Textarea id="cookie-json" placeholder={'[{"domain":".example.com","name":"cookie_name","value":"cookie_value",...}]'}
                value={cookieJson} onChange={(e) => setCookieJson(e.target.value)} rows={4} disabled={isImporting} className="font-mono text-xs" />
            </div>
            <Button onClick={handleJsonImport} disabled={isImporting || !cookieUrl || !cookieJson} className="w-full">
              {isImporting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Importing...</> : <><FileText className="mr-2 h-4 w-4" />Import with JSON Cookies</>}
            </Button>
            {renderError()}
            {renderSuccess()}
          </TabsContent>

          {/* cURL Tab */}
          <TabsContent value="curl" className="space-y-4">
            {renderCookieUrlInput()}
            <div className="rounded-lg bg-purple-50 p-3">
              <div className="flex gap-2">
                <Terminal className="h-4 w-4 text-purple-600 mt-0.5 shrink-0" />
                <div className="text-xs space-y-1">
                  <p className="font-medium text-purple-900">How to get cURL command:</p>
                  <ol className="list-decimal list-inside space-y-0.5 text-purple-700">
                    <li>Open DevTools (F12) → Network tab</li>
                    <li>Refresh the article page</li>
                    <li>Right-click request → Copy as cURL</li>
                  </ol>
                  <p className="text-purple-600 mt-1">URL is extracted automatically from the cURL command</p>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="curl-command">cURL Command</Label>
              <Textarea id="curl-command" placeholder="curl 'https://example.substack.com/p/article' -H 'cookie: ...'"
                value={curlCommand} onChange={(e) => setCurlCommand(e.target.value)} rows={4} disabled={isImporting} className="font-mono text-xs" />
              {curlCommand && extractUrlFromCurl(curlCommand) && (
                <div className="text-xs text-green-600 flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  URL detected: {extractUrlFromCurl(curlCommand)?.substring(0, 60)}...
                </div>
              )}
            </div>
            <Button onClick={handleCurlImport} disabled={isImporting || !curlCommand.trim()} className="w-full">
              {isImporting ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Importing...</> : <><Terminal className="h-4 w-4 mr-2" />Import with cURL</>}
            </Button>
            {renderError()}
            {renderSuccess()}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )

  function renderCookieUrlInput() {
    return (
      <div className="space-y-2">
        <Label>Article URL</Label>
        <div className="flex gap-2">
          <Input type="url" placeholder="https://example.substack.com/p/article-title"
            value={cookieUrl} onChange={(e) => setCookieUrl(e.target.value)} disabled={isImporting || isCheckingPaywall} />
          <Button variant="outline" onClick={checkPaywall} disabled={isCheckingPaywall || !cookieUrl.trim()} title="Check paywall status">
            {isCheckingPaywall ? <Loader2 className="h-4 w-4 animate-spin" /> : <Shield className="h-4 w-4" />}
          </Button>
        </div>
        {cookieUrl && paywallStatus && (
          <div className="text-sm">
            {paywallStatus.has_paywall || paywallStatus.needs_subscription ? (
              <div className="flex items-center gap-1 text-amber-600"><Lock className="h-3 w-3" />This article requires authentication</div>
            ) : (
              <div className="flex items-center gap-1 text-green-600"><CheckCircle className="h-3 w-3" />This article is publicly accessible</div>
            )}
          </div>
        )}
      </div>
    )
  }

  function renderError() {
    if (!error) return null
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  function renderSuccess() {
    if (!importResult?.success) return null
    return (
      <Alert className="border-green-200 bg-green-50">
        <CheckCircle className="h-4 w-4 text-green-600" />
        <AlertDescription className="text-green-800">
          <div className="font-semibold">{importResult.title}</div>
          <div className="text-sm mt-1">
            By {importResult.author} {importResult.word_count && `- ${importResult.word_count} words`}
            {importResult.content_increase && <span className="ml-2 font-medium text-green-700">({importResult.content_increase})</span>}
          </div>
        </AlertDescription>
      </Alert>
    )
  }
}
