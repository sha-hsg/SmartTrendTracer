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
  Link, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  FileText,
  Download,
  Lock,
  Cookie,
  Info,
  ExternalLink,
  Shield
} from 'lucide-react'

interface ArticleImportEnhancedModalProps {
  isOpen: boolean
  onClose: () => void
  onImportSuccess: () => void
}

interface ImportResult {
  success: boolean
  article_id?: number
  title?: string
  author?: string
  word_count?: number
  content_increase?: string
  error?: string
  requires_auth?: boolean
}

export default function ArticleImportEnhancedModal({ 
  isOpen, 
  onClose, 
  onImportSuccess 
}: ArticleImportEnhancedModalProps) {
  const [url, setUrl] = useState('')
  const [cookieString, setCookieString] = useState('')
  const [curlCommand, setCurlCommand] = useState('')
  const [cookieJson, setCookieJson] = useState('')
  const [isImporting, setIsImporting] = useState(false)
  const [isCheckingPaywall, setIsCheckingPaywall] = useState(false)
  const [importResult, setImportResult] = useState<ImportResult | null>(null)
  const [paywallStatus, setPaywallStatus] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('basic')

  const checkPaywall = async () => {
    if (!url.trim()) {
      setError('Please enter a URL')
      return
    }

    setIsCheckingPaywall(true)
    setError(null)
    setPaywallStatus(null)

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v2/articles/enhanced/check-paywall',
        null,
        { params: { url } }
      )
      
      setPaywallStatus(response.data)
      
      // If paywalled, switch to authentication tab
      if (response.data.has_paywall || response.data.needs_subscription) {
        setActiveTab('cookies')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to check article')
    } finally {
      setIsCheckingPaywall(false)
    }
  }

  const handleBasicImport = async () => {
    if (!url.trim()) {
      setError('Please enter a URL')
      return
    }

    setIsImporting(true)
    setError(null)
    setImportResult(null)

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v2/articles/enhanced/import-basic',
        { url }
      )

      setImportResult(response.data)
      
      if (response.data.success) {
        onImportSuccess()
        setTimeout(() => {
          setUrl('')
          setImportResult(null)
        }, 3000)
      } else if (response.data.requires_auth) {
        setActiveTab('cookies')
        setError('This article requires authentication. Please use the Cookie Authentication tab.')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import article')
    } finally {
      setIsImporting(false)
    }
  }

  const handleCookieImport = async () => {
    if (!url.trim() || !cookieString.trim()) {
      setError('Please enter both URL and cookies')
      return
    }

    setIsImporting(true)
    setError(null)
    setImportResult(null)

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v2/articles/enhanced/import-with-cookie-string',
        { 
          url,
          cookies: cookieString 
        }
      )

      setImportResult(response.data)
      
      if (response.data.success) {
        onImportSuccess()
        setTimeout(() => {
          setUrl('')
          setCookieString('')
          setImportResult(null)
        }, 3000)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import article with cookies')
    } finally {
      setIsImporting(false)
    }
  }

  // Extract URL from cURL command
  const extractUrlFromCurl = (curl: string): string | null => {
    // Try to find URL in cURL command
    const urlMatch = curl.match(/['"]?(https?:\/\/[^\s'"]+)['"]?/)
    return urlMatch ? urlMatch[1] : null
  }

  const handleCurlImport = async () => {
    if (!curlCommand.trim()) {
      setError('Please enter a cURL command')
      return
    }

    // Use provided URL or extract from cURL
    const importUrl = url.trim() || extractUrlFromCurl(curlCommand)

    if (!importUrl) {
      setError('Could not find URL in cURL command. Please check the command.')
      return
    }

    console.log('Starting cURL import with:', { url: importUrl, curlCommandLength: curlCommand.length })

    setIsImporting(true)
    setError(null)
    setImportResult(null)

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v2/articles/enhanced/import-with-cookies',
        {
          url: importUrl,
          curl_command: curlCommand
        }
      )

      console.log('Import response:', response.data)
      setImportResult(response.data)
      
      if (response.data.success) {
        onImportSuccess()
        setTimeout(() => {
          setUrl('')
          setCurlCommand('')
          setImportResult(null)
        }, 3000)
      } else if (response.data.error) {
        setError(response.data.error)
      }
    } catch (err: any) {
      console.error('Import error:', err)
      const errorMessage = err.response?.data?.error || err.response?.data?.detail || 'Failed to import article with cURL'
      setError(errorMessage)
    } finally {
      setIsImporting(false)
    }
  }

  const handleJsonImport = async () => {
    if (!url.trim() || !cookieJson.trim()) {
      setError('Please enter both URL and JSON cookies')
      return
    }

    console.log('Starting JSON cookie import with:', { url })

    setIsImporting(true)
    setError(null)
    setImportResult(null)

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v2/articles/enhanced/import-with-cookies',
        { 
          url,
          cookie_json: cookieJson 
        }
      )

      console.log('Import response:', response.data)
      setImportResult(response.data)
      
      if (response.data.success) {
        onImportSuccess()
        setTimeout(() => {
          setUrl('')
          setCookieJson('')
          setImportResult(null)
        }, 3000)
      } else if (response.data.error) {
        setError(response.data.error)
      }
    } catch (err: any) {
      console.error('Import error:', err)
      const errorMessage = err.response?.data?.error || err.response?.data?.detail || 'Failed to import article with JSON cookies'
      setError(errorMessage)
    } finally {
      setIsImporting(false)
    }
  }

  const handleClose = () => {
    if (!isImporting) {
      setUrl('')
      setCookieString('')
      setCurlCommand('')
      setCookieJson('')
      setImportResult(null)
      setPaywallStatus(null)
      setError(null)
      setActiveTab('basic')
      onClose()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Enhanced Article Import
          </DialogTitle>
          <DialogDescription>
            Import articles with support for subscriber-only content
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* URL Input - Common across all tabs */}
          <div className="space-y-2">
            <Label htmlFor="article-url">Article URL</Label>
            <div className="flex gap-2">
              <Input
                id="article-url"
                type="url"
                placeholder="https://example.substack.com/p/article-title"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isImporting || isCheckingPaywall}
              />
              <Button
                variant="outline"
                onClick={checkPaywall}
                disabled={isCheckingPaywall || !url.trim()}
              >
                {isCheckingPaywall ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Shield className="h-4 w-4" />
                )}
              </Button>
            </div>
            {url && paywallStatus && (
              <div className="text-sm">
                {paywallStatus.has_paywall || paywallStatus.needs_subscription ? (
                  <div className="flex items-center gap-1 text-amber-600">
                    <Lock className="h-3 w-3" />
                    This article requires authentication
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-green-600">
                    <CheckCircle className="h-3 w-3" />
                    This article is publicly accessible
                  </div>
                )}
              </div>
            )}
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="basic">Basic</TabsTrigger>
              <TabsTrigger value="cookies">Cookie String</TabsTrigger>
              <TabsTrigger value="json">JSON Cookies</TabsTrigger>
              <TabsTrigger value="curl">cURL</TabsTrigger>
            </TabsList>

            <TabsContent value="basic" className="space-y-4">
              <div className="rounded-lg bg-blue-50 p-4">
                <div className="flex gap-3">
                  <Info className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div className="text-sm">
                    <p className="font-medium text-blue-900">Basic Import</p>
                    <p className="text-blue-700 mt-1">
                      Use this for publicly accessible articles. If the article is behind a paywall,
                      you'll be prompted to use authentication.
                    </p>
                  </div>
                </div>
              </div>

              <Button 
                onClick={handleBasicImport} 
                disabled={isImporting || !url.trim()}
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
                    Import Article
                  </>
                )}
              </Button>
            </TabsContent>

            <TabsContent value="cookies" className="space-y-4">
              <div className="rounded-lg bg-amber-50 p-4">
                <div className="flex gap-3">
                  <Cookie className="h-5 w-5 text-amber-600 mt-0.5" />
                  <div className="text-sm space-y-2">
                    <p className="font-medium text-amber-900">How to get cookies:</p>
                    <ol className="list-decimal list-inside space-y-1 text-amber-700">
                      <li>Open the article in your browser and sign in</li>
                      <li>Open Developer Tools (F12 or right-click → Inspect)</li>
                      <li>Go to Application/Storage → Cookies</li>
                      <li>Find cookies for the publication domain</li>
                      <li>Copy the cookie string (name=value; name2=value2)</li>
                    </ol>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="cookie-string">Cookie String</Label>
                <Textarea
                  id="cookie-string"
                  placeholder="cookie_name=value; another_cookie=value2; session_id=xyz123"
                  value={cookieString}
                  onChange={(e) => setCookieString(e.target.value)}
                  rows={4}
                  disabled={isImporting}
                  className="font-mono text-xs"
                />
                <div className="text-xs text-gray-500">
                  Paste your browser cookies in the format: name=value; name2=value2
                </div>
              </div>

              <Button 
                onClick={handleCookieImport} 
                disabled={isImporting || !url.trim() || !cookieString.trim()}
                className="w-full"
              >
                {isImporting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Importing with Cookies...
                  </>
                ) : (
                  <>
                    <Cookie className="h-4 w-4 mr-2" />
                    Import with Authentication
                  </>
                )}
              </Button>
            </TabsContent>

            <TabsContent value="json" className="space-y-4">
              <div className="rounded-lg bg-green-50 p-4">
                <div className="flex gap-3">
                  <FileText className="h-5 w-5 text-green-600 mt-0.5" />
                  <div className="text-sm space-y-2">
                    <p className="font-medium text-green-900">Using Copy Cookie Extension:</p>
                    <ol className="list-decimal list-inside space-y-1 text-green-700">
                      <li>Install "Copy Cookie" browser extension</li>
                      <li>Go to the article and sign in</li>
                      <li>Click the extension icon</li>
                      <li>Click "Copy All" to copy cookies as JSON</li>
                      <li>Paste the JSON array here</li>
                    </ol>
                    <p className="text-xs text-green-600 mt-2">
                      ✨ This method is faster and more reliable than cURL!
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="cookie-json">JSON Cookie Array</Label>
                <Textarea
                  id="cookie-json"
                  placeholder='[{"domain":".magazine.sebastianraschka.com","name":"cookie_name","value":"cookie_value",...}]'
                  value={cookieJson}
                  onChange={(e) => setCookieJson(e.target.value)}
                  rows={6}
                  disabled={isImporting}
                  className="font-mono text-xs"
                />
                <div className="text-xs text-gray-500">
                  Paste the JSON array from Copy Cookie extension
                </div>
              </div>

              <Button
                onClick={handleJsonImport}
                disabled={isImporting || !url || !cookieJson}
                className="w-full"
              >
                {isImporting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <Link className="mr-2 h-4 w-4" />
                    Import with JSON Cookies
                  </>
                )}
              </Button>
            </TabsContent>

            <TabsContent value="curl" className="space-y-4">
              <div className="rounded-lg bg-purple-50 p-4">
                <div className="flex gap-3">
                  <FileText className="h-5 w-5 text-purple-600 mt-0.5" />
                  <div className="text-sm space-y-2">
                    <p className="font-medium text-purple-900">How to get cURL command:</p>
                    <ol className="list-decimal list-inside space-y-1 text-purple-700">
                      <li>Open the article in your browser and sign in</li>
                      <li>Open Developer Tools (F12)</li>
                      <li>Go to Network tab and refresh the page</li>
                      <li>Find the main article request</li>
                      <li>Right-click → Copy → Copy as cURL</li>
                    </ol>
                    <p className="text-xs text-purple-600 mt-2">
                      ✨ URL is extracted automatically from the cURL command!
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="curl-command">cURL Command</Label>
                <Textarea
                  id="curl-command"
                  placeholder="curl 'https://example.substack.com/p/article' -H 'cookie: ...'"
                  value={curlCommand}
                  onChange={(e) => setCurlCommand(e.target.value)}
                  rows={6}
                  disabled={isImporting}
                  className="font-mono text-xs"
                />
                <div className="text-xs text-gray-500">
                  Paste the complete cURL command - URL will be extracted automatically
                </div>
                {curlCommand && extractUrlFromCurl(curlCommand) && (
                  <div className="text-xs text-green-600 flex items-center gap-1">
                    <CheckCircle className="h-3 w-3" />
                    URL detected: {extractUrlFromCurl(curlCommand)?.substring(0, 60)}...
                  </div>
                )}
              </div>

              <Button
                onClick={handleCurlImport}
                disabled={isImporting || !curlCommand.trim()}
                className="w-full"
              >
                {isImporting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Importing with cURL...
                  </>
                ) : (
                  <>
                    <FileText className="h-4 w-4 mr-2" />
                    Import with cURL
                  </>
                )}
              </Button>
            </TabsContent>
          </Tabs>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Success Display */}
          {importResult && importResult.success && (
            <Alert className="border-green-200 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                <div className="font-semibold">{importResult.title}</div>
                <div className="text-sm mt-1">
                  By {importResult.author} • {importResult.word_count} words
                  {importResult.content_increase && (
                    <span className="ml-2 font-medium text-green-700">
                      ({importResult.content_increase})
                    </span>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          )}
        </div>

        <div className="mt-6 pt-4 border-t">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              <span>Your cookies are sent directly to fetch content and are not stored</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => window.open('https://github.com/yourusername/smarttrendtracer/wiki/article-import', '_blank')}
            >
              <ExternalLink className="h-3 w-3 mr-1" />
              Help
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}