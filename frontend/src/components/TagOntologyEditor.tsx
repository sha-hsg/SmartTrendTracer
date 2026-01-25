import { useState, useEffect } from 'react'
import axios from 'axios'
import OntologyAISuggestions from './OntologyAISuggestions'
import TagReorganizer from './TagReorganizer'
import './TagOntologyEditor.css'

interface TagConcept {
  id: number
  tag: string
  display_name: string
  description: string | null
  child_count: number
  descendant_count: number
  synonyms: string[]
  children?: TagConcept[]
}

interface ConceptDetails {
  id: number
  tag: string
  display_name: string
  description: string | null
  parent_id: number | null
  level: number
  child_count: number
  descendant_count: number
  synonyms: string[]
  path: string
}

function TagOntologyEditor() {
  const [tree, setTree] = useState<TagConcept[]>([])
  const [selectedConcept, setSelectedConcept] = useState<ConceptDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [editMode, setEditMode] = useState(false)
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set())
  const [showAI, setShowAI] = useState(false)
  const [showReorganizer, setShowReorganizer] = useState(false)
  
  // Form states
  const [newConceptForm, setNewConceptForm] = useState({
    tag: '',
    display_name: '',
    description: '',
    parent_id: null as number | null
  })
  
  const [newSynonym, setNewSynonym] = useState('')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchOntologyTree()
  }, [])

  const fetchOntologyTree = async () => {
    try {
      const response = await axios.get('/api/ontology/tree')
      setTree(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching ontology tree:', error)
      setLoading(false)
    }
  }

  const fetchConceptDetails = async (conceptId: number) => {
    try {
      const response = await axios.get(`/api/ontology/concept/${conceptId}`)
      setSelectedConcept(response.data)
    } catch (error) {
      console.error('Error fetching concept details:', error)
    }
  }

  const createConcept = async () => {
    try {
      await axios.post('/api/ontology/concept', newConceptForm)
      fetchOntologyTree()
      setNewConceptForm({
        tag: '',
        display_name: '',
        description: '',
        parent_id: null
      })
      alert('Concept created successfully!')
    } catch (error: any) {
      alert(`Error creating concept: ${error.response?.data?.detail || error.message}`)
    }
  }

  const updateConcept = async () => {
    if (!selectedConcept) return
    
    try {
      await axios.put(`/api/ontology/concept/${selectedConcept.id}`, {
        display_name: selectedConcept.display_name,
        description: selectedConcept.description
      })
      fetchOntologyTree()
      setEditMode(false)
      alert('Concept updated successfully!')
    } catch (error: any) {
      alert(`Error updating concept: ${error.response?.data?.detail || error.message}`)
    }
  }

  const deleteConcept = async (conceptId: number) => {
    if (!confirm('Are you sure you want to delete this concept?')) return
    
    try {
      await axios.delete(`/api/ontology/concept/${conceptId}`)
      fetchOntologyTree()
      setSelectedConcept(null)
      alert('Concept deleted successfully!')
    } catch (error: any) {
      alert(`Error deleting concept: ${error.response?.data?.detail || error.message}`)
    }
  }

  const addSynonym = async () => {
    if (!selectedConcept || !newSynonym) return
    
    try {
      await axios.post(`/api/ontology/concept/${selectedConcept.id}/synonym`, {
        synonym_tag: newSynonym
      })
      fetchConceptDetails(selectedConcept.id)
      setNewSynonym('')
      alert('Synonym added successfully!')
    } catch (error: any) {
      alert(`Error adding synonym: ${error.response?.data?.detail || error.message}`)
    }
  }

  const removeSynonym = async (_synonym: string) => {
    // This would need an endpoint to remove synonyms by name
    alert('Remove synonym functionality not yet implemented')
  }

  const toggleNode = (nodeId: number) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId)
    } else {
      newExpanded.add(nodeId)
    }
    setExpandedNodes(newExpanded)
  }

  const renderTreeNode = (node: TagConcept, level: number = 0) => {
    const isExpanded = expandedNodes.has(node.id)
    const hasChildren = node.children && node.children.length > 0
    const matchesSearch = !searchTerm || 
      node.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.tag.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.synonyms.some(s => s.toLowerCase().includes(searchTerm.toLowerCase()))

    if (!matchesSearch && !hasChildren) return null

    return (
      <div key={node.id} className="tree-node" style={{ marginLeft: `${level * 20}px` }}>
        <div className="node-content">
          {hasChildren && (
            <button 
              className="expand-button"
              onClick={() => toggleNode(node.id)}
            >
              {isExpanded ? '▼' : '▶'}
            </button>
          )}
          
          <div 
            className={`node-label ${selectedConcept?.id === node.id ? 'selected' : ''}`}
            onClick={() => fetchConceptDetails(node.id)}
          >
            <span className="node-name">{node.display_name}</span>
            <span className="node-tag">({node.tag})</span>
            {node.descendant_count > 0 && (
              <span className="node-count">[{node.descendant_count} descendants]</span>
            )}
            {node.synonyms.length > 0 && (
              <span className="node-synonyms">
                {node.synonyms.map(s => (
                  <span key={s} className="synonym-badge">{s}</span>
                ))}
              </span>
            )}
          </div>
        </div>
        
        {isExpanded && hasChildren && (
          <div className="node-children">
            {node.children!.map(child => renderTreeNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  const rebuildMappings = async () => {
    try {
      await axios.post('/api/ontology/rebuild-mappings')
      alert('Tag mappings rebuilt successfully!')
    } catch (error) {
      console.error('Error rebuilding mappings:', error)
      alert('Failed to rebuild mappings')
    }
  }

  const importExistingTags = async () => {
    try {
      const response = await axios.post('/api/ontology/import-existing-tags')
      alert(`Imported ${response.data.imported} tags, skipped ${response.data.skipped}`)
      fetchOntologyTree()
    } catch (error) {
      console.error('Error importing tags:', error)
      alert('Failed to import existing tags')
    }
  }

  if (loading) {
    return <div className="loading">Loading tag ontology...</div>
  }

  return (
    <div className="tag-ontology-editor">
      <div className="editor-header">
        <h2>Tag Ontology Manager</h2>
        <div className="header-actions">
          <button 
            onClick={() => setShowReorganizer(!showReorganizer)} 
            className={`reorganizer-button ${showReorganizer ? 'active' : ''}`}
          >
            ✨ GPT-5 Concept Reorganizer
          </button>
          <button 
            onClick={() => setShowAI(!showAI)} 
            className={`ai-button ${showAI ? 'active' : ''}`}
          >
            🤖 AI Assistant
          </button>
          <button onClick={rebuildMappings} className="rebuild-button">
            🔄 Rebuild Mappings
          </button>
          <button onClick={importExistingTags} className="import-button">
            📥 Import Existing Tags
          </button>
        </div>
      </div>

      <div className="editor-body">
        <div className="tree-panel">
          <div className="search-box">
            <input
              type="text"
              placeholder="Search concepts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div className="tree-view">
            {tree.map(node => renderTreeNode(node))}
          </div>
          
          <div className="add-concept-form">
            <h3>Add New Concept</h3>
            <input
              type="text"
              placeholder="Tag (lowercase, no spaces)"
              value={newConceptForm.tag}
              onChange={(e) => setNewConceptForm({
                ...newConceptForm,
                tag: e.target.value.toLowerCase().replace(/\s+/g, '-')
              })}
            />
            <input
              type="text"
              placeholder="Display Name"
              value={newConceptForm.display_name}
              onChange={(e) => setNewConceptForm({
                ...newConceptForm,
                display_name: e.target.value
              })}
            />
            <textarea
              placeholder="Description (optional)"
              value={newConceptForm.description}
              onChange={(e) => setNewConceptForm({
                ...newConceptForm,
                description: e.target.value
              })}
            />
            <select
              value={newConceptForm.parent_id || ''}
              onChange={(e) => setNewConceptForm({
                ...newConceptForm,
                parent_id: e.target.value ? parseInt(e.target.value) : null
              })}
            >
              <option value="">No Parent (Top Level)</option>
              {selectedConcept && (
                <option value={selectedConcept.id}>
                  Under: {selectedConcept.display_name}
                </option>
              )}
            </select>
            <button onClick={createConcept}>Create Concept</button>
          </div>
        </div>

        <div className="details-panel">
          {selectedConcept ? (
            <>
              <div className="concept-header">
                <h3>{selectedConcept.display_name}</h3>
                <div className="concept-actions">
                  <button onClick={() => setEditMode(!editMode)}>
                    {editMode ? 'Cancel' : 'Edit'}
                  </button>
                  {selectedConcept.child_count === 0 && (
                    <button 
                      onClick={() => deleteConcept(selectedConcept.id)}
                      className="delete-button"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>

              {editMode ? (
                <div className="edit-form">
                  <input
                    type="text"
                    value={selectedConcept.display_name}
                    onChange={(e) => setSelectedConcept({
                      ...selectedConcept,
                      display_name: e.target.value
                    })}
                  />
                  <textarea
                    value={selectedConcept.description || ''}
                    onChange={(e) => setSelectedConcept({
                      ...selectedConcept,
                      description: e.target.value
                    })}
                  />
                  <button onClick={updateConcept}>Save Changes</button>
                </div>
              ) : (
                <div className="concept-info">
                  <p><strong>Tag:</strong> {selectedConcept.tag}</p>
                  <p><strong>Description:</strong> {selectedConcept.description || 'No description'}</p>
                  <p><strong>Level:</strong> {selectedConcept.level}</p>
                  <p><strong>Path:</strong> {selectedConcept.path}</p>
                  <p><strong>Children:</strong> {selectedConcept.child_count}</p>
                  <p><strong>Total Descendants:</strong> {selectedConcept.descendant_count}</p>
                </div>
              )}

              <div className="synonyms-section">
                <h4>Synonyms (sameAs)</h4>
                <div className="synonyms-list">
                  {selectedConcept.synonyms.map(syn => (
                    <div key={syn} className="synonym-item">
                      <span>{syn}</span>
                      <button onClick={() => removeSynonym(syn)}>×</button>
                    </div>
                  ))}
                </div>
                <div className="add-synonym">
                  <input
                    type="text"
                    placeholder="Add synonym..."
                    value={newSynonym}
                    onChange={(e) => setNewSynonym(e.target.value.toLowerCase().replace(/\s+/g, '-'))}
                    onKeyPress={(e) => e.key === 'Enter' && addSynonym()}
                  />
                  <button onClick={addSynonym}>Add</button>
                </div>
              </div>

              <div className="hierarchy-info">
                <h4>Hierarchy</h4>
                <p>When filtering by "{selectedConcept.display_name}", the system will include:</p>
                <ul>
                  <li>Direct tags with "{selectedConcept.tag}"</li>
                  {selectedConcept.synonyms.length > 0 && (
                    <li>Tags with synonyms: {selectedConcept.synonyms.join(', ')}</li>
                  )}
                  {selectedConcept.descendant_count > 0 && (
                    <li>All {selectedConcept.descendant_count} descendant concepts and their synonyms</li>
                  )}
                </ul>
              </div>
            </>
          ) : (
            <div className="no-selection">
              <p>Select a concept from the tree to view details</p>
              <div className="help-text">
                <h4>How the Ontology Works:</h4>
                <ul>
                  <li><strong>Hierarchy:</strong> Tags can have parent-child relationships</li>
                  <li><strong>Synonyms:</strong> Multiple tags can refer to the same concept</li>
                  <li><strong>Filtering:</strong> Selecting a parent tag includes all descendants</li>
                  <li><strong>Performance:</strong> Uses materialized paths for fast queries</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>

      {showAI && (
        <div className="ai-panel">
          <OntologyAISuggestions onProposalApplied={fetchOntologyTree} />
        </div>
      )}
      
      {showReorganizer && (
        <div className="reorganizer-modal">
          <div className="modal-overlay" onClick={() => setShowReorganizer(false)} />
          <div className="modal-content">
            <button className="modal-close" onClick={() => setShowReorganizer(false)}>×</button>
            <TagReorganizer />
          </div>
        </div>
      )}
    </div>
  )
}

export default TagOntologyEditor