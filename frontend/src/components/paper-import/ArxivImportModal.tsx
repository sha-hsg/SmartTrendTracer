import React, { useState } from 'react';
import { X, Download, Search, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { API_BASE_URL } from '@/config/api';

interface ArxivImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess: (paperId: string) => void;  // MongoDB ObjectId as string
}

// Removed analyses - papers are imported without auto-processing
// Users can generate analyses manually after import if needed

export const ArxivImportModal: React.FC<ArxivImportModalProps> = ({
  isOpen,
  onClose,
  onImportSuccess
}) => {
  const [arxivInput, setArxivInput] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [activeTab, setActiveTab] = useState<'import' | 'search'>('import');

  if (!isOpen) return null;

  const handleImport = async () => {
    if (!arxivInput.trim()) {
      setError('Please enter an ArXiv ID or URL');
      return;
    }

    setIsImporting(true);
    setError(null);
    setSuccess(null);

    try {
      // Import without analyses (user can generate them manually later)
      const response = await fetch(`${API_BASE_URL}/api/arxiv/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url_or_id: arxivInput,
          process_pdf: false,  // Don't auto-process, user can click "Process PDF" later
          add_to_database: true
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Import failed');
      }

      const data = await response.json();
      
      if (data.success) {
        // Paper is imported and ready for manual processing
        setSuccess(`✅ Paper imported! "${data.title}" - PDF is ready. Use 'Process PDF' button to extract content when needed.`);
        
        // Notify parent with the paper_id (MongoDB ObjectId string)
        if (data.paper_id) {
          onImportSuccess(data.paper_id);
        }
        
        // Close modal after brief message
        setTimeout(() => {
          setArxivInput('');
          onClose();
        }, 3000);
      } else {
        // Import failed
        throw new Error(data.error || 'Import failed');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to import paper');
    } finally {
      setIsImporting(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setIsSearching(true);
    setError(null);
    setSearchResults([]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/arxiv/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          max_results: 10
        })
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (err: any) {
      setError(err.message || 'Failed to search ArXiv');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectPaper = (arxivId: string) => {
    setArxivInput(arxivId);
    setActiveTab('import');
    setSearchResults([]);
    setSearchQuery('');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold">Import from ArXiv</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('import')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'import'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Download className="w-4 h-4 inline mr-2" />
            Direct Import
          </button>
          <button
            onClick={() => setActiveTab('search')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'search'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Search className="w-4 h-4 inline mr-2" />
            Search ArXiv
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 200px)' }}>
          {activeTab === 'import' ? (
            <>
              {/* Import Input */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ArXiv ID or URL
                </label>
                <input
                  type="text"
                  value={arxivInput}
                  onChange={(e) => setArxivInput(e.target.value)}
                  placeholder="e.g., 2508.17669, https://arxiv.org/abs/2508.17669, or https://arxiv.org/pdf/2508.17669"
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isImporting}
                />
                <div className="mt-2 space-y-1">
                  <p className="text-sm text-gray-600 font-medium">Supported formats:</p>
                  <ul className="text-sm text-gray-500 space-y-0.5 ml-4">
                    <li>• Paper ID: <code className="bg-gray-100 px-1 py-0.5 rounded">2508.17669</code></li>
                    <li>• Abstract URL: <code className="bg-gray-100 px-1 py-0.5 rounded">https://arxiv.org/abs/2508.17669</code></li>
                    <li>• PDF URL: <code className="bg-gray-100 px-1 py-0.5 rounded">https://arxiv.org/pdf/2508.17669</code></li>
                    <li>• With version: <code className="bg-gray-100 px-1 py-0.5 rounded">2508.17669v2</code></li>
                  </ul>
                </div>
              </div>

              {/* Import Info */}
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="text-sm font-semibold text-blue-900 mb-2">How it works:</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Paper metadata and PDF will be downloaded immediately</li>
                  <li>• You can view the PDF right away after import</li>
                  <li>• Click "Process PDF" button when you want to extract content with Marker/MinerU</li>
                  <li>• Generate analyses manually from the paper viewer when needed</li>
                </ul>
              </div>

              {/* Status Messages */}
              {error && (
                <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
                  <AlertCircle className="w-5 h-5 text-red-600 mr-3 mt-0.5" />
                  <span className="text-red-800">{error}</span>
                </div>
              )}

              {success && (
                <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start">
                  <CheckCircle className="w-5 h-5 text-green-600 mr-3 mt-0.5" />
                  <span className="text-green-800">{success}</span>
                </div>
              )}

              {/* Import Button */}
              <button
                onClick={handleImport}
                disabled={isImporting || !arxivInput.trim()}
                className={`w-full py-3 px-4 rounded-lg font-medium transition-colors flex items-center justify-center ${
                  isImporting || !arxivInput.trim()
                    ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {isImporting ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <Download className="w-5 h-5 mr-2" />
                    Import Paper
                  </>
                )}
              </button>
            </>
          ) : (
            <>
              {/* Search Input */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search Query
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    placeholder="e.g., large language models, transformer architecture"
                    className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isSearching}
                  />
                  <button
                    onClick={handleSearch}
                    disabled={isSearching || !searchQuery.trim()}
                    className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                      isSearching || !searchQuery.trim()
                        ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                  >
                    {isSearching ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Search className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>

              {/* Search Results */}
              {searchResults.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold">Search Results</h3>
                  {searchResults.map((paper: any) => (
                    <div
                      key={paper.arxiv_id}
                      className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                      onClick={() => handleSelectPaper(paper.arxiv_id)}
                    >
                      <h4 className="font-medium text-blue-600 hover:underline mb-1">
                        {paper.title}
                      </h4>
                      <p className="text-sm text-gray-600 mb-2">
                        {paper.authors.slice(0, 3).join(', ')}
                        {paper.authors.length > 3 && ` +${paper.authors.length - 3} more`}
                      </p>
                      <p className="text-sm text-gray-500 line-clamp-2">
                        {paper.summary}
                      </p>
                      <div className="mt-2 flex items-center text-xs text-gray-500">
                        <span className="mr-4">ID: {paper.arxiv_id}</span>
                        <span>Published: {paper.published?.substring(0, 10)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Error Message */}
              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
                  <AlertCircle className="w-5 h-5 text-red-600 mr-3 mt-0.5" />
                  <span className="text-red-800">{error}</span>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};