import React, { useState } from 'react'
import axios from 'axios'
import './OntologyAISuggestions.css'

interface Proposal {
  type: string
  action: string
  details: any
}

interface TagProposals {
  tag: string
  proposals: Proposal[]
  reasoning: string
}

interface BulkSuggestion {
  tag: string
  action: string
  parent?: string
  merge_with?: string
  create_synonym_for?: string
  reasoning: string
}

interface OntologyAISuggestionsProps {
  onProposalApplied: () => void
  onClose?: () => void
}

function OntologyAISuggestions({ onProposalApplied, onClose }: OntologyAISuggestionsProps) {
  const [selectedTag, setSelectedTag] = useState('')
  const [proposals, setProposals] = useState<TagProposals | null>(null)
  const [bulkSuggestions, setBulkSuggestions] = useState<BulkSuggestion[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'single' | 'bulk'>('single')
  const [uncategorizedTags, setUncategorizedTags] = useState<any[]>([])
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<number>>(new Set())
  const [applyingBulk, setApplyingBulk] = useState(false)

  const [bulkLimit, setBulkLimit] = React.useState(100)  // Default to 100 tags
  const [_showResetConfirm, setShowResetConfirm] = useState(false)

  const fetchUncategorizedTags = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/ontology/ai/uncategorized?limit=${bulkLimit}`)
      setUncategorizedTags(response.data.tags)
    } catch (error) {
      console.error('Error fetching uncategorized tags:', error)
    }
  }

  const generateProposalsForTag = async () => {
    if (!selectedTag) return
    
    setLoading(true)
    try {
      const response = await axios.post('http://localhost:8000/api/ontology/ai/suggest/tag', {
        tag: selectedTag
      })
      setProposals(response.data)
    } catch (error: any) {
      alert(`Error generating proposals: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const generateBulkProposals = async () => {
    setLoading(true)
    setSelectedSuggestions(new Set())  // Reset selections
    try {
      const response = await axios.post('http://localhost:8000/api/ontology/ai/suggest/bulk', {
        limit: bulkLimit
      })
      console.log('Bulk suggestions response:', response.data)
      setBulkSuggestions(response.data.suggestions || [])
      
      // Also handle new_categories if present
      if (response.data.new_categories) {
        console.log('New categories suggested:', response.data.new_categories)
      }
    } catch (error: any) {
      console.error('Error generating bulk proposals:', error)
      alert(`Error generating bulk proposals: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const applyProposal = async (proposal: Proposal) => {
    if (!confirm(`Apply this proposal: ${proposal.action}?`)) return
    
    try {
      const response = await axios.post('http://localhost:8000/api/ontology/ai/apply', {
        proposal: proposal
      })
      
      if (response.data.success) {
        alert('Proposal applied successfully!')
        onProposalApplied()
        
        // Remove from proposals list
        if (proposals) {
          setProposals({
            ...proposals,
            proposals: proposals.proposals.filter(p => p !== proposal)
          })
        }
      } else {
        alert(`Failed to apply: ${response.data.message}`)
      }
    } catch (error: any) {
      alert(`Error applying proposal: ${error.response?.data?.detail || error.message}`)
    }
  }

  const toggleSuggestionSelection = (index: number) => {
    const newSelected = new Set(selectedSuggestions)
    if (newSelected.has(index)) {
      newSelected.delete(index)
    } else {
      newSelected.add(index)
    }
    setSelectedSuggestions(newSelected)
  }

  const toggleSelectAll = () => {
    if (selectedSuggestions.size === bulkSuggestions.length) {
      setSelectedSuggestions(new Set())
    } else {
      setSelectedSuggestions(new Set(bulkSuggestions.map((_, index) => index)))
    }
  }

  const convertSuggestionToProposal = (suggestion: BulkSuggestion): Proposal | null => {
    if (suggestion.action === 'categorize' && suggestion.parent) {
      return {
        type: 'set_hierarchy',
        action: `Place '${suggestion.tag}' under '${suggestion.parent}'`,
        details: {
          child: suggestion.tag,
          parent: suggestion.parent
        }
      }
    } else if (suggestion.action === 'merge' && suggestion.merge_with) {
      return {
        type: 'add_synonym',
        action: `Add '${suggestion.tag}' as synonym to '${suggestion.merge_with}'`,
        details: {
          concept: suggestion.merge_with,
          synonym: suggestion.tag
        }
      }
    } else if (suggestion.action === 'create_synonym' && suggestion.create_synonym_for) {
      return {
        type: 'add_synonym',
        action: `Add '${suggestion.tag}' as synonym to '${suggestion.create_synonym_for}'`,
        details: {
          concept: suggestion.create_synonym_for,
          synonym: suggestion.tag
        }
      }
    }
    return null
  }

  const applySelectedSuggestions = async () => {
    const selectedList = Array.from(selectedSuggestions).map(index => bulkSuggestions[index])
    const count = selectedList.length
    
    if (count === 0) {
      alert('Please select at least one suggestion to apply')
      return
    }

    if (!confirm(`Apply ${count} selected suggestion${count > 1 ? 's' : ''}?`)) {
      return
    }

    setApplyingBulk(true)
    let successCount = 0
    let failedCount = 0
    const failedReasons: string[] = []

    for (const suggestion of selectedList) {
      const proposal = convertSuggestionToProposal(suggestion)
      if (!proposal) {
        failedCount++
        failedReasons.push(`${suggestion.tag}: Invalid action`)
        continue
      }

      try {
        const response = await axios.post('http://localhost:8000/api/ontology/ai/apply', {
          proposal: proposal
        })
        
        if (response.data.success) {
          successCount++
        } else {
          failedCount++
          failedReasons.push(`${suggestion.tag}: ${response.data.message}`)
        }
      } catch (error: any) {
        failedCount++
        failedReasons.push(`${suggestion.tag}: ${error.response?.data?.detail || error.message}`)
      }
    }

    setApplyingBulk(false)
    
    // Remove successfully applied suggestions
    const remainingSuggestions = bulkSuggestions.filter((_, index) => !selectedSuggestions.has(index))
    setBulkSuggestions(remainingSuggestions)
    setSelectedSuggestions(new Set())
    
    // Show results
    let message = `Applied ${successCount} suggestion${successCount !== 1 ? 's' : ''} successfully.`
    if (failedCount > 0) {
      message += `\n${failedCount} failed:\n${failedReasons.slice(0, 5).join('\n')}`
      if (failedReasons.length > 5) {
        message += `\n... and ${failedReasons.length - 5} more`
      }
    }
    alert(message)
    
    if (successCount > 0) {
      onProposalApplied()
    }
  }

  React.useEffect(() => {
    fetchUncategorizedTags()
  }, [bulkLimit])  // Re-fetch when bulk limit changes

  return (
    <div className="ontology-ai-suggestions">
      <div className="ai-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
          <div style={{ flex: 1 }}>
            <h3>🤖 AI-Powered Ontology Assistant</h3>
            <p>Using Claude 4 Sonnet to suggest semantic relationships (200K context, 64K output)</p>
          </div>
          {onClose && (
            <button 
              onClick={onClose}
              style={{
                background: 'transparent',
                border: '1px solid #666',
                color: '#999',
                padding: '5px 10px',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
                marginLeft: '10px'
              }}
              title="Close AI Assistant"
            >
              ✕ Close
            </button>
          )}
        </div>
      </div>

      <div className="ai-tabs">
        <button 
          className={activeTab === 'single' ? 'active' : ''}
          onClick={() => setActiveTab('single')}
        >
          Single Tag Analysis
        </button>
        <button 
          className={activeTab === 'bulk' ? 'active' : ''}
          onClick={() => setActiveTab('bulk')}
        >
          Bulk Organization
        </button>
      </div>

      {activeTab === 'single' ? (
        <div className="single-tag-section">
          <div className="tag-selector">
            <input
              type="text"
              placeholder="Enter tag to analyze..."
              value={selectedTag}
              onChange={(e) => setSelectedTag(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && generateProposalsForTag()}
            />
            <button 
              onClick={generateProposalsForTag}
              disabled={!selectedTag || loading}
            >
              {loading ? 'Analyzing...' : 'Analyze Tag'}
            </button>
          </div>

          {uncategorizedTags.length > 0 && !loading && (
            <div className="quick-select">
              <p>Or select an uncategorized tag:</p>
              <div className="tag-chips">
                {uncategorizedTags.slice(0, 10).map(tag => (
                  <button
                    key={tag.id}
                    className="tag-chip"
                    onClick={() => setSelectedTag(tag.tag)}
                  >
                    {tag.display_name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {loading && (
            <div className="loading-container">
              <div className="spinner"></div>
              <div className="loading-text">Analyzing with Claude 4 Sonnet...</div>
              <div className="loading-subtext">Finding semantic relationships for "{selectedTag}"</div>
            </div>
          )}

          {proposals && !loading && (
            <div className="proposals-container">
              <h4>AI Suggestions for "{proposals.tag}"</h4>
              
              {proposals.reasoning && (
                <div className="ai-reasoning">
                  <strong>AI Reasoning:</strong> {proposals.reasoning}
                </div>
              )}

              <div className="proposals-list">
                {proposals.proposals.length === 0 ? (
                  <p>No suggestions generated for this tag.</p>
                ) : (
                  proposals.proposals.map((proposal, index) => (
                    <div key={index} className="proposal-card">
                      <div className="proposal-type">
                        {proposal.type.replace('_', ' ').toUpperCase()}
                      </div>
                      <div className="proposal-action">
                        {proposal.action}
                      </div>
                      <div className="proposal-details">
                        <code>{JSON.stringify(proposal.details, null, 2)}</code>
                      </div>
                      <button 
                        className="apply-button"
                        onClick={() => applyProposal(proposal)}
                      >
                        Apply This Suggestion
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bulk-section">
          <div className="bulk-controls">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <div>
                <label htmlFor="bulk-limit" style={{ marginRight: '10px' }}>
                  Number of tags to analyze:
                </label>
              <select 
                id="bulk-limit"
                value={bulkLimit} 
                onChange={(e) => setBulkLimit(Number(e.target.value))}
                style={{
                  padding: '5px 10px',
                  borderRadius: '4px',
                  border: '1px solid #ddd',
                  marginRight: '10px'
                }}
              >
                <option value={20}>20 tags (quick)</option>
                <option value={50}>50 tags (moderate)</option>
                <option value={100}>100 tags (comprehensive)</option>
                <option value={150}>150 tags (extensive)</option>
                <option value={200}>200 tags (maximum)</option>
              </select>
                <span style={{ fontSize: '12px', color: '#666', marginLeft: '10px' }}>
                  Using Claude 4 Sonnet with {bulkLimit} tags
                </span>
              </div>
              <button
                onClick={() => setShowResetConfirm(true)}
                style={{
                  background: '#ff4444',
                  color: 'white',
                  border: 'none',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
                title="Reset the list of already processed tags"
              >
                🔄 Reset Processed Tags
              </button>
            </div>
            <button 
              onClick={generateBulkProposals}
              disabled={loading}
              className="generate-bulk-button"
            >
              {loading ? `Analyzing ${bulkLimit} tags...` : `Generate Bulk Suggestions (${bulkLimit} tags)`}
            </button>
            <p>AI will analyze uncategorized tags and suggest organization</p>
            <p style={{ fontSize: '11px', color: '#666', marginTop: '5px' }}>
              💡 Tip: The system tracks processed tags to show different batches each time. Use "Reset Processed Tags" to start over.
            </p>
          </div>

          {loading && (
            <div className="loading-container">
              <div className="spinner"></div>
              <div className="loading-text">Processing {bulkLimit} tags with Claude 4 Sonnet...</div>
              <div className="loading-subtext">
                Analyzing relationships, finding patterns, suggesting organization...
              </div>
            </div>
          )}

          {bulkSuggestions.length > 0 && !loading && (
            <div className="bulk-suggestions">
              <div className="bulk-suggestions-header" style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '20px',
                padding: '15px',
                background: '#f5f5f5',
                borderRadius: '8px'
              }}>
                <h4 style={{ margin: 0 }}>
                  Bulk Organization Suggestions ({selectedSuggestions.size}/{bulkSuggestions.length} selected)
                </h4>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button 
                    onClick={toggleSelectAll}
                    style={{
                      padding: '8px 16px',
                      background: '#fff',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    {selectedSuggestions.size === bulkSuggestions.length ? 'Deselect All' : 'Select All'}
                  </button>
                  <button 
                    onClick={applySelectedSuggestions}
                    disabled={selectedSuggestions.size === 0 || applyingBulk}
                    style={{
                      padding: '8px 20px',
                      background: selectedSuggestions.size > 0 ? '#28a745' : '#ccc',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: selectedSuggestions.size > 0 ? 'pointer' : 'not-allowed',
                      fontWeight: 'bold'
                    }}
                  >
                    {applyingBulk ? 
                      `Applying ${selectedSuggestions.size} suggestions...` : 
                      `Apply Selected (${selectedSuggestions.size})`
                    }
                  </button>
                </div>
              </div>
              
              <div className="suggestions-grid">
                {bulkSuggestions.map((suggestion, index) => (
                  <div 
                    key={index} 
                    className={`suggestion-card ${selectedSuggestions.has(index) ? 'selected' : ''}`}
                    style={{
                      border: selectedSuggestions.has(index) ? '2px solid #007bff' : '1px solid #ddd',
                      background: selectedSuggestions.has(index) ? '#f0f8ff' : '#fff'
                    }}
                  >
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'flex-start', 
                      gap: '10px',
                      marginBottom: '10px'
                    }}>
                      <input
                        type="checkbox"
                        checked={selectedSuggestions.has(index)}
                        onChange={() => toggleSuggestionSelection(index)}
                        style={{
                          width: '20px',
                          height: '20px',
                          cursor: 'pointer',
                          marginTop: '2px'
                        }}
                      />
                      <div style={{ flex: 1 }}>
                        <div className="suggestion-tag" style={{ fontWeight: 'bold', fontSize: '16px' }}>
                          {suggestion.tag}
                        </div>
                        <div className="suggestion-action" style={{ marginTop: '5px' }}>
                          <strong>Action:</strong> {suggestion.action}
                        </div>
                      </div>
                    </div>
                    
                    {suggestion.parent && (
                      <div className="suggestion-detail">
                        <strong>Parent:</strong> {suggestion.parent}
                      </div>
                    )}
                    {suggestion.merge_with && (
                      <div className="suggestion-detail">
                        <strong>Merge with:</strong> {suggestion.merge_with}
                      </div>
                    )}
                    {suggestion.create_synonym_for && (
                      <div className="suggestion-detail">
                        <strong>Synonym for:</strong> {suggestion.create_synonym_for}
                      </div>
                    )}
                    
                    {suggestion.reasoning && (
                      <div className="suggestion-reasoning" style={{ 
                        marginTop: '10px',
                        fontSize: '12px',
                        color: '#666',
                        fontStyle: 'italic'
                      }}>
                        {suggestion.reasoning}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="ai-info">
        <h4>How it works:</h4>
        <ul>
          <li><strong>Synonyms:</strong> AI identifies different expressions of the same concept</li>
          <li><strong>Hierarchy:</strong> AI suggests parent-child relationships based on specificity</li>
          <li><strong>Same-As:</strong> AI groups variations (abbreviations, alternate spellings)</li>
          <li><strong>Bulk Mode:</strong> AI organizes multiple uncategorized tags at once</li>
        </ul>
      </div>
    </div>
  )
}

export default OntologyAISuggestions