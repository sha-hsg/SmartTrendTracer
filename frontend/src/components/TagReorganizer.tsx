import { useState, useEffect } from 'react'
import axios from 'axios'
import './TagReorganizer.css'

interface TagNode {
  name: string
  display_name: string
  description: string | null
  level: number
  parent: string | null
  children: string[]
  synonyms: string[]
  usage_count: number
  color?: string
  icon?: string
}

interface Proposal {
  proposal_id: string
  version: string
  created_at: string
  model_used: string
  total_tags: number
  confidence_score: number
  reasoning: string
  statistics: any
  root_categories: string[]
  hierarchy: { [key: string]: TagNode }
  merge_proposals: any[]
  deprecated_tags: string[]
  new_tags_suggested: any[]
}

function TagReorganizer() {
  const [currentStructure, setCurrentStructure] = useState<any>(null)
  const [proposal, setProposal] = useState<Proposal | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [approvedChanges, setApprovedChanges] = useState<{ [key: string]: boolean }>({})
  const [viewMode, setViewMode] = useState<'current' | 'proposed'>('current')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadCurrentStructure()
  }, [])

  const loadCurrentStructure = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/tags/reorganize/current-structure')
      setCurrentStructure(response.data)
    } catch (error) {
      console.error('Failed to load current structure:', error)
      setError('Failed to load current tag structure')
    }
  }

  const generateProposal = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await axios.post('http://localhost:8000/api/tags/reorganize/generate-proposal', {
        include_context: true,
        max_samples_per_tag: 3,
        confidence_threshold: 0.7
      })
      
      setProposal(response.data)
      setViewMode('proposed')
      
      // Initialize all changes as approved by default
      const initialApproval: { [key: string]: boolean } = {}
      Object.keys(response.data.hierarchy).forEach(tag => {
        initialApproval[tag] = true
      })
      setApprovedChanges(initialApproval)
      
    } catch (error: any) {
      console.error('Failed to generate proposal:', error)
      setError(error.response?.data?.detail || 'Failed to generate reorganization proposal')
    } finally {
      setLoading(false)
    }
  }

  const toggleNode = (nodeName: string) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(nodeName)) {
      newExpanded.delete(nodeName)
    } else {
      newExpanded.add(nodeName)
    }
    setExpandedNodes(newExpanded)
  }

  const toggleApproval = (tagName: string) => {
    setApprovedChanges(prev => ({
      ...prev,
      [tagName]: !prev[tagName]
    }))
  }

  const applyProposal = async () => {
    if (!proposal) return
    
    setLoading(true)
    setError(null)
    
    try {
      const response = await axios.post(
        `http://localhost:8000/api/tags/reorganize/proposal/${proposal.proposal_id}/apply`,
        {
          proposal_id: proposal.proposal_id,
          approved_changes: approvedChanges
        }
      )
      
      if (response.data.status === 'applied') {
        alert('Reorganization applied successfully!')
        setProposal(null)
        setViewMode('current')
        await loadCurrentStructure()
      } else {
        alert('Some changes could not be applied. Check the console for details.')
        console.error('Application errors:', response.data.results.errors)
      }
    } catch (error: any) {
      console.error('Failed to apply proposal:', error)
      setError(error.response?.data?.detail || 'Failed to apply reorganization')
    } finally {
      setLoading(false)
    }
  }

  const exportProposal = async (format: 'json' | 'markdown' | 'csv') => {
    if (!proposal) return
    
    try {
      const response = await axios.get(
        `http://localhost:8000/api/tags/reorganize/proposal/${proposal.proposal_id}/export?format=${format}`
      )
      
      // Create download link
      const content = format === 'json' 
        ? JSON.stringify(response.data, null, 2)
        : response.data.content
      
      const blob = new Blob([content], { 
        type: format === 'json' ? 'application/json' : 'text/plain' 
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tag-reorganization.${format}`
      a.click()
      URL.revokeObjectURL(url)
      
    } catch (error) {
      console.error('Failed to export proposal:', error)
      setError('Failed to export proposal')
    }
  }

  const renderNode = (nodeName: string, hierarchy: { [key: string]: TagNode }, level: number = 0) => {
    const node = hierarchy[nodeName]
    if (!node) return null
    
    const isExpanded = expandedNodes.has(nodeName)
    const hasChildren = node.children && node.children.length > 0
    const isSelected = selectedNode === nodeName
    const isApproved = approvedChanges[nodeName]
    
    return (
      <div key={nodeName} className={`tree-node ${!isApproved ? 'rejected' : ''}`}>
        <div 
          className={`node-content ${isSelected ? 'selected' : ''}`}
          style={{ paddingLeft: `${level * 20}px` }}
        >
          {viewMode === 'proposed' && (
            <input
              type="checkbox"
              checked={isApproved}
              onChange={() => toggleApproval(nodeName)}
              className="approval-checkbox"
            />
          )}
          
          {hasChildren && (
            <button 
              className="expand-btn"
              onClick={() => toggleNode(nodeName)}
            >
              {isExpanded ? '▼' : '▶'}
            </button>
          )}
          
          <div 
            className="node-label"
            onClick={() => setSelectedNode(nodeName)}
          >
            {node.icon && <span className="node-icon">{node.icon}</span>}
            <span className="node-display-name">{node.display_name}</span>
            <span className="node-tag">({node.name})</span>
            <span className="node-usage">[{node.usage_count} uses]</span>
            
            {node.synonyms.length > 0 && (
              <span className="node-synonyms">
                {node.synonyms.map(syn => (
                  <span key={syn} className="synonym-badge">{syn}</span>
                ))}
              </span>
            )}
          </div>
        </div>
        
        {isExpanded && hasChildren && (
          <div className="node-children">
            {node.children.map(childName => renderNode(childName, hierarchy, level + 1))}
          </div>
        )}
      </div>
    )
  }

  const renderTree = () => {
    if (viewMode === 'current' && currentStructure) {
      // For current structure, render flat list
      return (
        <div className="flat-tags">
          <h3>Current Tags ({currentStructure.total_tags} total)</h3>
          <div className="tag-list">
            {Object.entries(currentStructure.tags).map(([tag, data]: [string, any]) => (
              <div key={tag} className="tag-item">
                <span className="tag-name">{tag}</span>
                <span className="tag-count">({data.usage_count} uses)</span>
              </div>
            ))}
          </div>
        </div>
      )
    }
    
    if (viewMode === 'proposed' && proposal) {
      return (
        <div className="proposed-tree">
          <h3>Proposed Hierarchy</h3>
          <div className="tree-view">
            {proposal.root_categories.map(rootName => 
              renderNode(rootName, proposal.hierarchy)
            )}
          </div>
        </div>
      )
    }
    
    return null
  }

  return (
    <div className="tag-reorganizer">
      <div className="reorganizer-header">
        <h2>🤖 GPT-5 Enhanced Concept Reorganizer</h2>
        <p>Use GPT-5 to comprehensively reorganize your concepts with full backwards compatibility</p>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      <div className="controls">
        <div className="view-toggle">
          <button 
            className={viewMode === 'current' ? 'active' : ''}
            onClick={() => setViewMode('current')}
          >
            Current Structure
          </button>
          <button 
            className={viewMode === 'proposed' ? 'active' : ''}
            onClick={() => setViewMode('proposed')}
            disabled={!proposal}
          >
            Proposed Structure
          </button>
        </div>

        <div className="action-buttons">
          {!proposal && (
            <button 
              className="generate-btn"
              onClick={generateProposal}
              disabled={loading}
            >
              {loading ? '⏳ Generating...' : '✨ Generate Reorganization Proposal'}
            </button>
          )}
          
          {proposal && (
            <>
              <button 
                className="apply-btn"
                onClick={applyProposal}
                disabled={loading}
              >
                {loading ? '⏳ Applying...' : '✅ Apply Selected Changes'}
              </button>
              
              <div className="export-buttons">
                <button onClick={() => exportProposal('json')}>📥 Export JSON</button>
                <button onClick={() => exportProposal('markdown')}>📥 Export Markdown</button>
                <button onClick={() => exportProposal('csv')}>📥 Export CSV</button>
              </div>
            </>
          )}
        </div>
      </div>

      {proposal && (
        <div className="proposal-info">
          <div className="info-card">
            <h4>Proposal Details</h4>
            <p><strong>Model:</strong> {proposal.model_used}</p>
            <p><strong>Confidence:</strong> {(proposal.confidence_score * 100).toFixed(1)}%</p>
            <p><strong>Total Tags:</strong> {proposal.total_tags}</p>
            <p><strong>Root Categories:</strong> {proposal.root_categories.length}</p>
            <p><strong>Deprecated Tags:</strong> {proposal.deprecated_tags.length}</p>
            <p><strong>New Suggestions:</strong> {proposal.new_tags_suggested.length}</p>
          </div>
          
          {proposal.reasoning && (
            <div className="reasoning-card">
              <h4>AI Reasoning</h4>
              <p>{proposal.reasoning}</p>
            </div>
          )}
        </div>
      )}

      <div className="tree-container">
        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Analyzing all tags with Gemini 2.5 Pro...</p>
          </div>
        ) : (
          renderTree()
        )}
      </div>

      {selectedNode && proposal && viewMode === 'proposed' && (
        <div className="node-details">
          <h3>Selected Node: {proposal.hierarchy[selectedNode]?.display_name}</h3>
          <p><strong>Tag:</strong> {selectedNode}</p>
          <p><strong>Description:</strong> {proposal.hierarchy[selectedNode]?.description || 'No description'}</p>
          <p><strong>Level:</strong> {proposal.hierarchy[selectedNode]?.level}</p>
          <p><strong>Parent:</strong> {proposal.hierarchy[selectedNode]?.parent || 'Root'}</p>
          <p><strong>Children:</strong> {proposal.hierarchy[selectedNode]?.children.length || 0}</p>
          <p><strong>Synonyms:</strong> {proposal.hierarchy[selectedNode]?.synonyms.join(', ') || 'None'}</p>
        </div>
      )}
    </div>
  )
}

export default TagReorganizer