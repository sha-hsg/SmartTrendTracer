import React, { useState, useEffect } from 'react';
import { 
  FileText, Brain, Target, AlertTriangle, Rocket, 
  Lightbulb, Link, Settings, BarChart3, Plus, Star, RefreshCw,
  Loader2, Copy, Check
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Analysis {
  id: number;
  type: string;
  name: string;
  content: string;
  model: string;
  word_count: number;
  created_at: string;
  user_rating?: number;
  user_notes?: string;
}

interface PaperAnalysisViewerProps {
  paperId: number;
  paperTitle?: string;
}

const ANALYSIS_ICONS: Record<string, any> = {
  summary: FileText,
  key_contributions: Target,
  methodology: Brain,
  limitations: AlertTriangle,
  future_work: Rocket,
  practical_applications: Lightbulb,
  related_work: Link,
  technical_depth: Settings,
  impact_assessment: BarChart3,
  custom: Plus
};

const ANALYSIS_COLORS: Record<string, string> = {
  summary: 'blue',
  key_contributions: 'green',
  methodology: 'purple',
  limitations: 'orange',
  future_work: 'teal',
  practical_applications: 'yellow',
  related_work: 'indigo',
  technical_depth: 'gray',
  impact_assessment: 'red',
  custom: 'pink'
};

export const PaperAnalysisViewer: React.FC<PaperAnalysisViewerProps> = ({
  paperId,
  paperTitle
}) => {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [showCustomPrompt, setShowCustomPrompt] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');
  const [customName, setCustomName] = useState('Custom Analysis');

  useEffect(() => {
    fetchAnalyses();
  }, [paperId]);

  const fetchAnalyses = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/papers/repository/${paperId}/analyses`);
      if (response.ok) {
        const data = await response.json();
        setAnalyses(data.analyses || []);
        if (data.analyses?.length > 0 && !selectedAnalysis) {
          setSelectedAnalysis(data.analyses[0]);
        }
      }
    } catch (error) {
      console.error('Failed to fetch analyses:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateAnalysis = async (analysisType: string) => {
    setIsGenerating(analysisType);
    try {
      const response = await fetch('/api/papers/repository/generate-analyses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          paper_id: paperId,
          analysis_types: [analysisType],
          regenerate: false
        })
      });

      if (response.ok) {
        await fetchAnalyses();
      }
    } catch (error) {
      console.error('Failed to generate analysis:', error);
    } finally {
      setIsGenerating(null);
    }
  };

  const generateCustomAnalysis = async () => {
    if (!customPrompt.trim()) return;

    setIsGenerating('custom');
    try {
      const response = await fetch('/api/papers/repository/custom-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          paper_id: paperId,
          prompt: customPrompt,
          name: customName
        })
      });

      if (response.ok) {
        setCustomPrompt('');
        setCustomName('Custom Analysis');
        setShowCustomPrompt(false);
        await fetchAnalyses();
      }
    } catch (error) {
      console.error('Failed to generate custom analysis:', error);
    } finally {
      setIsGenerating(null);
    }
  };

  const copyToClipboard = (text: string, id: number) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleSection = (type: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(type)) {
      newExpanded.delete(type);
    } else {
      newExpanded.add(type);
    }
    setExpandedSections(newExpanded);
  };

  const updateRating = async (analysisId: number, rating: number) => {
    try {
      await fetch(`/api/papers/repository/${paperId}/analysis/${analysisId}/rating`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating })
      });
      
      // Update local state
      setAnalyses(prev => prev.map(a => 
        a.id === analysisId ? { ...a, user_rating: rating } : a
      ));
      if (selectedAnalysis?.id === analysisId) {
        setSelectedAnalysis({ ...selectedAnalysis, user_rating: rating });
      }
    } catch (error) {
      console.error('Failed to update rating:', error);
    }
  };

  const availableAnalysisTypes = [
    'summary', 'key_contributions', 'methodology', 'limitations',
    'future_work', 'practical_applications', 'related_work',
    'technical_depth', 'impact_assessment'
  ];

  const missingAnalyses = availableAnalysisTypes.filter(
    type => !analyses.some(a => a.type === type)
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <div className="w-80 border-r bg-gray-50 overflow-y-auto">
        <div className="p-4">
          <h3 className="font-semibold text-lg mb-4">Paper Analyses</h3>
          
          {/* Existing Analyses */}
          {analyses.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-600 mb-2">Available Analyses</h4>
              <div className="space-y-2">
                {analyses.map(analysis => {
                  const Icon = ANALYSIS_ICONS[analysis.type] || FileText;
                  const color = ANALYSIS_COLORS[analysis.type] || 'gray';
                  const isSelected = selectedAnalysis?.id === analysis.id;

                  return (
                    <button
                      key={analysis.id}
                      onClick={() => setSelectedAnalysis(analysis)}
                      className={`w-full text-left p-3 rounded-lg transition-all ${
                        isSelected
                          ? `bg-${color}-100 border-2 border-${color}-300`
                          : 'bg-white border border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-start">
                        <Icon className={`w-5 h-5 mr-3 mt-0.5 text-${color}-600`} />
                        <div className="flex-1">
                          <div className="font-medium">{analysis.name}</div>
                          <div className="text-xs text-gray-500 mt-1">
                            {analysis.word_count} words • {analysis.model}
                          </div>
                          {analysis.user_rating && (
                            <div className="flex items-center mt-1">
                              {[...Array(5)].map((_, i) => (
                                <Star
                                  key={i}
                                  className={`w-3 h-3 ${
                                    i < analysis.user_rating!
                                      ? 'fill-yellow-400 text-yellow-400'
                                      : 'text-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Generate Missing Analyses */}
          {missingAnalyses.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-600 mb-2">Generate New Analysis</h4>
              <div className="space-y-2">
                {missingAnalyses.map(type => {
                  const Icon = ANALYSIS_ICONS[type];
                  const color = ANALYSIS_COLORS[type];
                  const name = type.split('_').map(w => 
                    w.charAt(0).toUpperCase() + w.slice(1)
                  ).join(' ');

                  return (
                    <button
                      key={type}
                      onClick={() => generateAnalysis(type)}
                      disabled={isGenerating === type}
                      className={`w-full text-left p-3 rounded-lg border border-dashed border-gray-300 
                        hover:bg-gray-50 transition-all ${
                        isGenerating === type ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                    >
                      <div className="flex items-center">
                        {isGenerating === type ? (
                          <Loader2 className="w-5 h-5 mr-3 animate-spin text-gray-600" />
                        ) : (
                          <Icon className={`w-5 h-5 mr-3 text-${color}-600`} />
                        )}
                        <span className="text-gray-700">{name}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Custom Analysis */}
          <div>
            <button
              onClick={() => setShowCustomPrompt(!showCustomPrompt)}
              className="w-full p-3 rounded-lg border border-dashed border-gray-300 
                hover:bg-gray-50 transition-all flex items-center justify-center"
            >
              <Plus className="w-5 h-5 mr-2 text-gray-600" />
              <span className="text-gray-700">Custom Analysis</span>
            </button>

            {showCustomPrompt && (
              <div className="mt-3 p-3 bg-white rounded-lg border">
                <input
                  type="text"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  placeholder="Analysis name"
                  className="w-full px-3 py-2 border rounded mb-2 text-sm"
                />
                <textarea
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="Enter your custom analysis prompt..."
                  className="w-full px-3 py-2 border rounded text-sm"
                  rows={4}
                />
                <button
                  onClick={generateCustomAnalysis}
                  disabled={!customPrompt.trim() || isGenerating === 'custom'}
                  className={`mt-2 w-full py-2 rounded font-medium text-sm ${
                    !customPrompt.trim() || isGenerating === 'custom'
                      ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {isGenerating === 'custom' ? (
                    <span className="flex items-center justify-center">
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generating...
                    </span>
                  ) : (
                    'Generate'
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        {selectedAnalysis ? (
          <div className="p-6">
            {/* Header */}
            <div className="mb-6 pb-4 border-b">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold mb-2">{selectedAnalysis.name}</h2>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span>Model: {selectedAnalysis.model}</span>
                    <span>{selectedAnalysis.word_count} words</span>
                    <span>{new Date(selectedAnalysis.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {/* Rating */}
                  <div className="flex items-center">
                    {[1, 2, 3, 4, 5].map(rating => (
                      <button
                        key={rating}
                        onClick={() => updateRating(selectedAnalysis.id, rating)}
                        className="p-1"
                      >
                        <Star
                          className={`w-5 h-5 ${
                            rating <= (selectedAnalysis.user_rating || 0)
                              ? 'fill-yellow-400 text-yellow-400'
                              : 'text-gray-300 hover:text-yellow-400'
                          }`}
                        />
                      </button>
                    ))}
                  </div>
                  
                  {/* Copy Button */}
                  <button
                    onClick={() => copyToClipboard(selectedAnalysis.content, selectedAnalysis.id)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    {copiedId === selectedAnalysis.id ? (
                      <Check className="w-5 h-5 text-green-600" />
                    ) : (
                      <Copy className="w-5 h-5 text-gray-600" />
                    )}
                  </button>

                  {/* Regenerate Button */}
                  <button
                    onClick={() => generateAnalysis(selectedAnalysis.type)}
                    disabled={isGenerating === selectedAnalysis.type}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <RefreshCw className={`w-5 h-5 text-gray-600 ${
                      isGenerating === selectedAnalysis.type ? 'animate-spin' : ''
                    }`} />
                  </button>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="prose prose-lg max-w-none prose-headings:text-gray-900 prose-h1:text-3xl prose-h2:text-2xl prose-h3:text-xl prose-strong:text-gray-900 prose-ul:list-disc prose-ol:list-decimal prose-li:text-gray-700 prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-4 prose-blockquote:italic prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100">
              <ReactMarkdown
                components={{
                  h1: ({children}) => <h1 className="text-3xl font-bold mt-6 mb-4 text-gray-900">{children}</h1>,
                  h2: ({children}) => <h2 className="text-2xl font-semibold mt-5 mb-3 text-gray-800">{children}</h2>,
                  h3: ({children}) => <h3 className="text-xl font-semibold mt-4 mb-2 text-gray-800">{children}</h3>,
                  h4: ({children}) => <h4 className="text-lg font-semibold mt-3 mb-2 text-gray-700">{children}</h4>,
                  p: ({children}) => <p className="mb-4 text-gray-700 leading-relaxed">{children}</p>,
                  ul: ({children}) => <ul className="list-disc pl-6 mb-4 space-y-2">{children}</ul>,
                  ol: ({children}) => <ol className="list-decimal pl-6 mb-4 space-y-2">{children}</ol>,
                  li: ({children}) => <li className="text-gray-700">{children}</li>,
                  strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
                  em: ({children}) => <em className="italic text-gray-700">{children}</em>,
                  blockquote: ({children}) => (
                    <blockquote className="border-l-4 border-blue-500 pl-4 py-2 my-4 italic bg-blue-50 rounded-r">
                      {children}
                    </blockquote>
                  ),
                  code: ({inline, children}) => {
                    if (inline) {
                      return <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800">{children}</code>;
                    }
                    return (
                      <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto mb-4">
                        <code className="text-sm font-mono">{children}</code>
                      </pre>
                    );
                  },
                  hr: () => <hr className="my-6 border-gray-300" />,
                  a: ({href, children}) => (
                    <a href={href} className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">
                      {children}
                    </a>
                  ),
                  table: ({children}) => (
                    <div className="overflow-x-auto mb-4">
                      <table className="min-w-full border border-gray-300">{children}</table>
                    </div>
                  ),
                  th: ({children}) => <th className="border border-gray-300 px-4 py-2 bg-gray-100 font-semibold text-left">{children}</th>,
                  td: ({children}) => <td className="border border-gray-300 px-4 py-2">{children}</td>,
                }}
              >
                {selectedAnalysis.content}
              </ReactMarkdown>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <Brain className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-lg">Select or generate an analysis to view</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};