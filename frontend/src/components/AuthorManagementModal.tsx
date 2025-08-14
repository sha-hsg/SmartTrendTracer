import React, { useState } from 'react';
import axios from 'axios';
import './AuthorManagementModal.css';

interface Author {
  id: number;
  name: string;
  count: number;
  subdomain?: string;
}

interface AuthorManagementModalProps {
  authors: Author[];
  onClose: () => void;
}

function AuthorManagementModal({ authors, onClose }: AuthorManagementModalProps) {
  const [selectedAuthors, setSelectedAuthors] = useState<number[]>([]);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const toggleAuthor = (authorId: number) => {
    setSelectedAuthors(prev => 
      prev.includes(authorId) 
        ? prev.filter(id => id !== authorId)
        : [...prev, authorId]
    );
  };

  const selectAll = () => {
    setSelectedAuthors(authors.map(a => a.id));
  };

  const deselectAll = () => {
    setSelectedAuthors([]);
  };

  const handleDeleteSelected = async () => {
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }

    setDeleting(true);
    try {
      for (const authorId of selectedAuthors) {
        await axios.delete(`http://localhost:8000/api/substack/authors/${authorId}`);
      }
      
      alert(`Successfully deleted ${selectedAuthors.length} author(s) and all their articles`);
      onClose();
    } catch (error: any) {
      console.error('Error deleting authors:', error);
      alert(`Failed to delete authors: ${error.response?.data?.detail || error.message}`);
    } finally {
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

  const handleDeleteSingle = async (authorId: number) => {
    const author = authors.find(a => a.id === authorId);
    if (!confirm(`Delete author "${author?.name}" and ALL their articles (${author?.count} articles)?\n\nThis action cannot be undone.`)) {
      return;
    }

    setDeleting(true);
    try {
      await axios.delete(`http://localhost:8000/api/substack/authors/${authorId}`);
      alert(`Successfully deleted author "${author?.name}" and all their articles`);
      onClose();
    } catch (error: any) {
      console.error('Error deleting author:', error);
      alert(`Failed to delete author: ${error.response?.data?.detail || error.message}`);
    } finally {
      setDeleting(false);
    }
  };

  const selectedAuthorNames = authors
    .filter(a => selectedAuthors.includes(a.id))
    .map(a => a.name);

  const totalArticles = authors
    .filter(a => selectedAuthors.includes(a.id))
    .reduce((sum, a) => sum + a.count, 0);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="author-management-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Author Management</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <div className="bulk-actions">
            <button onClick={selectAll} className="select-all-btn">
              Select All
            </button>
            <button onClick={deselectAll} className="deselect-all-btn">
              Deselect All
            </button>
            {selectedAuthors.length > 0 && (
              <>
                {confirmDelete ? (
                  <div className="confirm-delete-section">
                    <span className="confirm-text">
                      Delete {selectedAuthors.length} author(s) and {totalArticles} article(s)?
                    </span>
                    <button 
                      onClick={handleDeleteSelected} 
                      className="confirm-delete-btn"
                      disabled={deleting}
                    >
                      {deleting ? 'Deleting...' : 'Yes, Delete'}
                    </button>
                    <button 
                      onClick={() => setConfirmDelete(false)} 
                      className="cancel-btn"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button 
                    onClick={handleDeleteSelected} 
                    className="delete-selected-btn"
                    disabled={deleting}
                  >
                    Delete Selected ({selectedAuthors.length})
                  </button>
                )}
              </>
            )}
          </div>

          {selectedAuthors.length > 0 && (
            <div className="selected-summary">
              <strong>Selected:</strong> {selectedAuthorNames.join(', ')}
              <br />
              <strong>Total articles to delete:</strong> {totalArticles}
            </div>
          )}

          <div className="authors-list">
            {authors.map(author => (
              <div key={author.id} className="author-item">
                <input
                  type="checkbox"
                  checked={selectedAuthors.includes(author.id)}
                  onChange={() => toggleAuthor(author.id)}
                  className="author-checkbox"
                />
                <div className="author-info">
                  <span className="author-name">{author.name}</span>
                  <span className="author-stats">
                    {author.count} article{author.count !== 1 ? 's' : ''}
                    {author.subdomain && ` • ${author.subdomain}.substack.com`}
                  </span>
                </div>
                <button
                  onClick={() => handleDeleteSingle(author.id)}
                  className="delete-single-btn"
                  title={`Delete ${author.name} and all articles`}
                  disabled={deleting}
                >
                  🗑️
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="modal-footer">
          <button onClick={onClose} className="close-btn">Close</button>
        </div>
      </div>
    </div>
  );
}

export default AuthorManagementModal;