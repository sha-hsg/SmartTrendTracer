import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './TagTaxonomyEditor.css';

interface TagNode {
  name: string;
  display_name: string;
  description?: string;
  level: number;
  parent?: string;
  children: string[];
  synonyms: string[];
  usage_count: number;
  color?: string;
  icon?: string;
}

interface ReorganizationProposal {
  proposal_id: string;
  version: string;
  created_at: string;
  model_used: string;
  total_tags: number;
  confidence_score: number;
  reasoning: string;
  statistics: any;
  root_categories: string[];
  hierarchy: { [key: string]: TagNode };
  merge_proposals: any[];
  deprecated_tags: any[];
  new_tags_suggested: any[];
}

interface CurrentStructure {
  tags: { [key: string]: any };
  statistics: any;
}

const TagTaxonomyEditor: React.FC = () => {
  const [currentStructure, setCurrentStructure] = useState<CurrentStructure | null>(null);
  const [proposal, setProposal] = useState<ReorganizationProposal | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [editingNode, setEditingNode] = useState<TagNode | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [approvalSettings, setApprovalSettings] = useState({
    merges: true,
    deprecations: true,
    new_categories: true,
    synonyms: true
  });
  const [viewMode, setViewMode] = useState<'current' | 'proposed' | 'compare'>('current');

  useEffect(() => {
    loadCurrentStructure();
  }, []);

  const loadCurrentStructure = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/tags/reorganize/current-structure');
      setCurrentStructure(response.data);
    } catch (error) {
      console.error('Error loading current structure:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateProposal = async () => {
    setGenerating(true);
    try {
      const response = await axios.post('http://localhost:8000/api/tags/reorganize/generate-proposal', {
        include_context: true,
        max_samples_per_tag: 3,
        confidence_threshold: 0.7
      });
      setProposal(response.data);
      setViewMode('proposed');
      
      // Auto-expand root categories
      const roots = new Set<string>(response.data.root_categories);
      setExpandedNodes(roots);
    } catch (error) {
      console.error('Error generating proposal:', error);
      alert('Failed to generate proposal. Please check your Gemini API key.');
    } finally {
      setGenerating(false);
    }
  };

  const applyProposal = async () => {
    if (!proposal) return;
    
    const confirmed = window.confirm(
      `This will apply the following changes:\n` +
      `- ${proposal.merge_proposals.length} tag merges\n` +
      `- ${proposal.deprecated_tags.length} tag deprecations\n` +
      `- ${Object.keys(proposal.hierarchy).length} reorganized tags\n\n` +
      `Are you sure you want to proceed?`
    );
    
    if (!confirmed) return;
    
    try {
      const response = await axios.post(
        `http://localhost:8000/api/tags/reorganize/proposal/${proposal.proposal_id}/apply`,
        {
          proposal_id: proposal.proposal_id,
          approved_changes: approvalSettings
        }
      );
      
      alert(`Changes applied successfully!\n${JSON.stringify(response.data.results, null, 2)}`);
      
      // Reload current structure
      await loadCurrentStructure();
      setProposal(null);
      setViewMode('current');
    } catch (error) {
      console.error('Error applying proposal:', error);
      alert('Failed to apply changes');
    }
  };

  const updateNode = async (nodeName: string, updates: Partial<TagNode>) => {
    if (!proposal) return;
    
    try {
      await axios.put(
        `http://localhost:8000/api/tags/reorganize/proposal/${proposal.proposal_id}/node/${nodeName}`,
        updates
      );
      
      // Update local state
      const updatedProposal = { ...proposal };
      updatedProposal.hierarchy[nodeName] = {
        ...updatedProposal.hierarchy[nodeName],
        ...updates
      };
      setProposal(updatedProposal);
      setEditingNode(null);
    } catch (error) {
      console.error('Error updating node:', error);
    }
  };

  const exportProposal = async (format: 'json' | 'markdown' | 'csv') => {
    if (!proposal) return;
    
    try {
      const response = await axios.get(
        `http://localhost:8000/api/tags/reorganize/proposal/${proposal.proposal_id}/export?format=${format}`
      );
      
      // Create download
      const blob = new Blob(
        [format === 'json' ? JSON.stringify(response.data, null, 2) : response.data.content],
        { type: format === 'json' ? 'application/json' : 'text/plain' }
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `taxonomy_${proposal.proposal_id}.${format === 'markdown' ? 'md' : format}`;
      a.click();
    } catch (error) {
      console.error('Error exporting proposal:', error);
    }
  };

  const toggleNode = (nodeName: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeName)) {
      newExpanded.delete(nodeName);
    } else {
      newExpanded.add(nodeName);
    }
    setExpandedNodes(newExpanded);
  };

  const renderTagNode = (node: TagNode, hierarchy: { [key: string]: TagNode }) => {
    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = expandedNodes.has(node.name);
    const isSelected = selectedNode === node.name;
    
    return (
      <div key={node.name} className={`tag-node level-${node.level}`}>
        <div 
          className={`node-content ${isSelected ? 'selected' : ''}`}
          onClick={() => setSelectedNode(node.name)}
          style={{ 
            paddingLeft: `${node.level * 20}px`,
            borderLeftColor: node.color || '#ccc'
          }}
        >
          {hasChildren && (
            <button 
              className="expand-toggle"
              onClick={(e) => {
                e.stopPropagation();
                toggleNode(node.name);
              }}
            >
              {isExpanded ? '▼' : '▶'}
            </button>
          )}
          
          <span className="node-icon">{node.icon || '🏷️'}</span>
          
          <span className="node-name">
            {node.display_name}
            {node.usage_count > 0 && (
              <span className="usage-count">({node.usage_count})</span>
            )}
          </span>
          
          {node.synonyms && node.synonyms.length > 0 && (
            <span className="synonym-badge" title={node.synonyms.join(', ')}>
              +{node.synonyms.length} syn
            </span>
          )}
          
          {viewMode === 'proposed' && (
            <button 
              className="edit-btn"
              onClick={(e) => {
                e.stopPropagation();
                setEditingNode(node);
              }}
            >
              ✏️
            </button>
          )}
        </div>
        
        {node.description && isSelected && (
          <div className="node-description" style={{ paddingLeft: `${(node.level + 1) * 20}px` }}>
            {node.description}
          </div>
        )}
        
        {hasChildren && isExpanded && (
          <div className="node-children">
            {node.children.map(childName => 
              hierarchy[childName] && renderTagNode(hierarchy[childName], hierarchy)
            )}
          </div>
        )}
      </div>
    );
  };

  const renderHierarchy = (hierarchy: { [key: string]: TagNode }, roots: string[]) => {
    return (
      <div className="hierarchy-tree">
        {roots.map(rootName => 
          hierarchy[rootName] && renderTagNode(hierarchy[rootName], hierarchy)
        )}
      </div>
    );
  };

  const renderCurrentTags = () => {
    if (!currentStructure) return null;
    
    const tagsByUsage = Object.entries(currentStructure.tags)
      .sort((a, b) => b[1].usage_count - a[1].usage_count);
    
    return (
      <div className="current-tags-grid">
        {tagsByUsage.map(([tagName, tagData]) => (
          <div key={tagName} className="current-tag-card">
            <div className="tag-header">
              <span className="tag-name">{tagName}</span>
              <span className="tag-usage">{tagData.usage_count} uses</span>
            </div>
            {tagData.existing_synonyms && tagData.existing_synonyms.length > 0 && (
              <div className="tag-synonyms">
                Synonyms: {tagData.existing_synonyms.join(', ')}
              </div>
            )}
            {tagData.co_occurring_tags && tagData.co_occurring_tags.length > 0 && (
              <div className="co-occurring">
                Often with: {tagData.co_occurring_tags.slice(0, 3).map((t: { tag: string }) => t.tag).join(', ')}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="taxonomy-editor">
      <div className="editor-header">
        <h1>🌳 Concept Taxonomy Reorganization</h1>
        <p className="subtitle">
          Powered by GPT-5 - Comprehensively reorganize all {currentStructure?.statistics.total_tags || 0} concepts with full backwards compatibility
        </p>
      </div>

      <div className="controls-bar">
        <div className="view-mode-selector">
          <button 
            className={viewMode === 'current' ? 'active' : ''}
            onClick={() => setViewMode('current')}
            disabled={loading}
          >
            📊 Current Structure
          </button>
          <button 
            className={viewMode === 'proposed' ? 'active' : ''}
            onClick={() => setViewMode('proposed')}
            disabled={!proposal}
          >
            🎯 Proposed Taxonomy
          </button>
          <button 
            className={viewMode === 'compare' ? 'active' : ''}
            onClick={() => setViewMode('compare')}
            disabled={!proposal}
          >
            🔄 Compare
          </button>
        </div>

        <div className="action-buttons">
          {!proposal && (
            <button 
              className="generate-btn"
              onClick={generateProposal}
              disabled={generating || !currentStructure}
            >
              {generating ? '🤖 Analyzing with GPT-5...' : '✨ Generate Reorganization'}
            </button>
          )}
          
          {proposal && (
            <>
              <button className="apply-btn" onClick={applyProposal}>
                ✅ Apply Changes
              </button>
              <button onClick={() => exportProposal('json')}>📥 Export JSON</button>
              <button onClick={() => exportProposal('markdown')}>📝 Export Markdown</button>
              <button onClick={() => exportProposal('csv')}>📊 Export CSV</button>
            </>
          )}
        </div>
      </div>

      {currentStructure && (
        <div className="statistics-bar">
          <div className="stat">
            <span className="stat-label">Total Tags:</span>
            <span className="stat-value">{currentStructure.statistics.total_tags}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Total Taggings:</span>
            <span className="stat-value">{currentStructure.statistics.total_taggings}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Avg Usage:</span>
            <span className="stat-value">{currentStructure.statistics.average_usage.toFixed(1)}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Low Usage Tags:</span>
            <span className="stat-value">{currentStructure.statistics.low_usage_tags.length}</span>
          </div>
        </div>
      )}

      {proposal && (
        <div className="proposal-info">
          <div className="confidence-score">
            <span>Confidence Score:</span>
            <div className="confidence-bar">
              <div 
                className="confidence-fill"
                style={{ width: `${proposal.confidence_score * 100}%` }}
              />
            </div>
            <span>{(proposal.confidence_score * 100).toFixed(0)}%</span>
          </div>
          
          <div className="proposal-stats">
            <span className="stat-chip">📁 {proposal.root_categories.length} root categories</span>
            <span className="stat-chip">🔀 {proposal.merge_proposals.length} merges</span>
            <span className="stat-chip">🗑️ {proposal.deprecated_tags.length} deprecations</span>
            <span className="stat-chip">✨ {proposal.new_tags_suggested.length} new categories</span>
          </div>
          
          {proposal.reasoning && (
            <details className="reasoning-section">
              <summary>🧠 AI Reasoning</summary>
              <p>{proposal.reasoning}</p>
            </details>
          )}
        </div>
      )}

      <div className="content-area">
        {loading && <div className="loading">Loading current structure...</div>}
        
        {viewMode === 'current' && currentStructure && renderCurrentTags()}
        
        {viewMode === 'proposed' && proposal && (
          <div className="proposed-taxonomy">
            {renderHierarchy(proposal.hierarchy, proposal.root_categories)}
          </div>
        )}
        
        {viewMode === 'compare' && proposal && (
          <div className="compare-view">
            <div className="compare-panel">
              <h3>Current Structure</h3>
              {renderCurrentTags()}
            </div>
            <div className="compare-panel">
              <h3>Proposed Taxonomy</h3>
              {renderHierarchy(proposal.hierarchy, proposal.root_categories)}
            </div>
          </div>
        )}
      </div>

      {proposal && (
        <div className="approval-settings">
          <h3>Apply Settings</h3>
          <label>
            <input 
              type="checkbox"
              checked={approvalSettings.merges}
              onChange={(e) => setApprovalSettings({...approvalSettings, merges: e.target.checked})}
            />
            Apply tag merges ({proposal.merge_proposals.length})
          </label>
          <label>
            <input 
              type="checkbox"
              checked={approvalSettings.deprecations}
              onChange={(e) => setApprovalSettings({...approvalSettings, deprecations: e.target.checked})}
            />
            Apply deprecations ({proposal.deprecated_tags.length})
          </label>
          <label>
            <input 
              type="checkbox"
              checked={approvalSettings.synonyms}
              onChange={(e) => setApprovalSettings({...approvalSettings, synonyms: e.target.checked})}
            />
            Create synonyms
          </label>
          <label>
            <input 
              type="checkbox"
              checked={approvalSettings.new_categories}
              onChange={(e) => setApprovalSettings({...approvalSettings, new_categories: e.target.checked})}
            />
            Add new categories
          </label>
        </div>
      )}

      {editingNode && (
        <div className="edit-modal">
          <div className="modal-content">
            <h3>Edit Tag Node: {editingNode.name}</h3>
            <label>
              Display Name:
              <input 
                value={editingNode.display_name}
                onChange={(e) => setEditingNode({...editingNode, display_name: e.target.value})}
              />
            </label>
            <label>
              Description:
              <textarea 
                value={editingNode.description || ''}
                onChange={(e) => setEditingNode({...editingNode, description: e.target.value})}
              />
            </label>
            <label>
              Icon:
              <input 
                value={editingNode.icon || ''}
                onChange={(e) => setEditingNode({...editingNode, icon: e.target.value})}
              />
            </label>
            <label>
              Color:
              <input 
                type="color"
                value={editingNode.color || '#000000'}
                onChange={(e) => setEditingNode({...editingNode, color: e.target.value})}
              />
            </label>
            <label>
              Synonyms (comma-separated):
              <input 
                value={editingNode.synonyms.join(', ')}
                onChange={(e) => setEditingNode({
                  ...editingNode, 
                  synonyms: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                })}
              />
            </label>
            <div className="modal-actions">
              <button onClick={() => updateNode(editingNode.name, editingNode)}>
                Save
              </button>
              <button onClick={() => setEditingNode(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TagTaxonomyEditor;