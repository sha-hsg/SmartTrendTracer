import React, { useState, useEffect } from 'react';
import axios from 'axios';
interface Author {
  id: string;
  name: string;
  email?: string;
  subdomain?: string;
  article_count: number;
}

interface Article {
  id: string;
  title: string;
  published?: string;
}

interface AuthorManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthorsUpdated?: () => void;
}

const AuthorManagementModal: React.FC<AuthorManagementModalProps> = ({ 
  isOpen, 
  onClose,
  onAuthorsUpdated 
}) => {
  const [activeTab, setActiveTab] = useState<'view' | 'edit' | 'create' | 'assign'>('view');
  const [authors, setAuthors] = useState<Author[]>([]);
  const [selectedAuthor, setSelectedAuthor] = useState<Author | null>(null);
  const [editingAuthor, setEditingAuthor] = useState<Author | null>(null);
  const [articlesWithoutAuthor, setArticlesWithoutAuthor] = useState<Article[]>([]);
  const [selectedArticles, setSelectedArticles] = useState<string[]>([]);
  const [newAuthor, setNewAuthor] = useState({ name: '', email: '', subdomain: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{ authorId: string; deleteArticles: boolean } | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchAuthors();
      if (activeTab === 'assign') {
        fetchArticlesWithoutAuthor();
      }
    }
  }, [isOpen, activeTab]);

  const fetchAuthors = async () => {
    try {
      const response = await axios.get(`/api/articles/authors/all`);
      setAuthors(response.data);
    } catch (err) {
      console.error('Error fetching authors:', err);
      setError('Failed to fetch authors');
    }
  };

  const fetchArticlesWithoutAuthor = async () => {
    try {
      const response = await axios.get(`/api/articles/without-author`);
      setArticlesWithoutAuthor(response.data.articles || response.data);
    } catch (err) {
      console.error('Error fetching articles:', err);
    }
  };

  const handleUpdateAuthor = async () => {
    if (!editingAuthor) return;
    
    setLoading(true);
    setError(null);
    
    try {
      await axios.put(
        `/api/articles/authors/${editingAuthor.id}`,
        {
          name: editingAuthor.name,
          email: editingAuthor.email,
          subdomain: editingAuthor.subdomain
        }
      );
      
      await fetchAuthors();
      setEditingAuthor(null);
      setSelectedAuthor(null);
      
      if (onAuthorsUpdated) {
        onAuthorsUpdated();
      }
    } catch (err: any) {
      console.error('Error updating author:', err);
      setError(err.response?.data?.detail || 'Failed to update author');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAuthor = async (authorId: string, deleteArticles: boolean) => {
    setLoading(true);
    setError(null);
    
    try {
      await axios.delete(
        `/api/articles/authors/${authorId}?delete_articles=${deleteArticles}`
      );
      
      await fetchAuthors();
      setSelectedAuthor(null);
      setDeleteConfirm(null);
      
      if (onAuthorsUpdated) {
        onAuthorsUpdated();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete author');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAuthor = async () => {
    if (!newAuthor.name) {
      setError('Author name is required');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      await axios.post(`/api/articles/authors`, newAuthor);
      
      await fetchAuthors();
      setNewAuthor({ name: '', email: '', subdomain: '' });
      setActiveTab('view');
      
      if (onAuthorsUpdated) {
        onAuthorsUpdated();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create author');
    } finally {
      setLoading(false);
    }
  };

  const handleAssignArticles = async () => {
    if (!selectedAuthor || selectedArticles.length === 0) return;
    
    setLoading(true);
    setError(null);
    
    try {
      await axios.post(
        `/api/articles/authors/${selectedAuthor.id}/assign-articles`,
        selectedArticles
      );
      
      await fetchArticlesWithoutAuthor();
      setSelectedArticles([]);
      
      if (onAuthorsUpdated) {
        onAuthorsUpdated();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to assign articles');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-[800px] max-h-[80vh] flex flex-col">
        <div className="flex justify-between items-center p-4 border-b">
          <h2 className="text-xl font-semibold">Author Management</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>

        <div className="flex border-b">
          <button
            className={`px-4 py-2 ${activeTab === 'view' ? 'bg-blue-50 border-b-2 border-blue-500' : ''}`}
            onClick={() => setActiveTab('view')}
          >
            View Authors
          </button>
          <button
            className={`px-4 py-2 ${activeTab === 'edit' ? 'bg-blue-50 border-b-2 border-blue-500' : ''}`}
            onClick={() => setActiveTab('edit')}
          >
            Edit Author
          </button>
          <button
            className={`px-4 py-2 ${activeTab === 'create' ? 'bg-blue-50 border-b-2 border-blue-500' : ''}`}
            onClick={() => setActiveTab('create')}
          >
            Create Author
          </button>
          <button
            className={`px-4 py-2 ${activeTab === 'assign' ? 'bg-blue-50 border-b-2 border-blue-500' : ''}`}
            onClick={() => setActiveTab('assign')}
          >
            Assign Articles
          </button>
        </div>

        <div className="flex-1 overflow-auto p-4">
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded mb-4">
              {error}
            </div>
          )}

          {activeTab === 'view' && (
            <div className="space-y-2">
              {authors.map(author => (
                <div key={author.id} className="flex justify-between items-center p-3 border rounded hover:bg-gray-50">
                  <div>
                    <div className="font-medium">{author.name}</div>
                    {author.email && <div className="text-sm text-gray-500">{author.email}</div>}
                    {author.subdomain && <div className="text-sm text-gray-500">{author.subdomain}.substack.com</div>}
                    <div className="text-sm text-gray-500">{author.article_count} articles</div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setSelectedAuthor(author);
                        setEditingAuthor(author);
                        setActiveTab('edit');
                      }}
                      className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setDeleteConfirm({ authorId: author.id, deleteArticles: false })}
                      className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'edit' && (
            <div className="space-y-4">
              <select
                className="w-full p-2 border rounded"
                value={editingAuthor?.id || ''}
                onChange={(e) => {
                  const author = authors.find(a => a.id === e.target.value);
                  setEditingAuthor(author || null);
                }}
              >
                <option value="">Select an author to edit</option>
                {authors.map(author => (
                  <option key={author.id} value={author.id}>
                    {author.name} ({author.article_count} articles)
                  </option>
                ))}
              </select>

              {editingAuthor && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Name</label>
                    <input
                      type="text"
                      value={editingAuthor.name}
                      onChange={(e) => setEditingAuthor({ ...editingAuthor, name: e.target.value })}
                      className="w-full p-2 border rounded"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Email</label>
                    <input
                      type="email"
                      value={editingAuthor.email || ''}
                      onChange={(e) => setEditingAuthor({ ...editingAuthor, email: e.target.value })}
                      className="w-full p-2 border rounded"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Subdomain</label>
                    <div className="flex items-center">
                      <input
                        type="text"
                        value={editingAuthor.subdomain || ''}
                        onChange={(e) => setEditingAuthor({ ...editingAuthor, subdomain: e.target.value })}
                        className="flex-1 p-2 border rounded-l"
                      />
                      <span className="px-3 py-2 bg-gray-100 border border-l-0 rounded-r">.substack.com</span>
                    </div>
                  </div>
                  <button
                    onClick={handleUpdateAuthor}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
                  >
                    {loading ? 'Updating...' : 'Update Author'}
                  </button>
                </>
              )}
            </div>
          )}

          {activeTab === 'create' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name *</label>
                <input
                  type="text"
                  value={newAuthor.name}
                  onChange={(e) => setNewAuthor({ ...newAuthor, name: e.target.value })}
                  className="w-full p-2 border rounded"
                  placeholder="Author name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  value={newAuthor.email}
                  onChange={(e) => setNewAuthor({ ...newAuthor, email: e.target.value })}
                  className="w-full p-2 border rounded"
                  placeholder="author@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Subdomain</label>
                <div className="flex items-center">
                  <input
                    type="text"
                    value={newAuthor.subdomain}
                    onChange={(e) => setNewAuthor({ ...newAuthor, subdomain: e.target.value })}
                    className="flex-1 p-2 border rounded-l"
                    placeholder="authorname"
                  />
                  <span className="px-3 py-2 bg-gray-100 border border-l-0 rounded-r">.substack.com</span>
                </div>
              </div>
              <button
                onClick={handleCreateAuthor}
                disabled={loading || !newAuthor.name}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-400"
              >
                {loading ? 'Creating...' : 'Create Author'}
              </button>
            </div>
          )}

          {activeTab === 'assign' && (
            <div className="space-y-4">
              <select
                className="w-full p-2 border rounded"
                value={selectedAuthor?.id || ''}
                onChange={(e) => {
                  const author = authors.find(a => a.id === e.target.value);
                  setSelectedAuthor(author || null);
                }}
              >
                <option value="">Select an author</option>
                {authors.map(author => (
                  <option key={author.id} value={author.id}>
                    {author.name}
                  </option>
                ))}
              </select>

              {selectedAuthor && (
                <>
                  <div className="font-medium">
                    Select articles to assign to {selectedAuthor.name}:
                  </div>
                  <div className="max-h-64 overflow-auto border rounded p-2 space-y-1">
                    {articlesWithoutAuthor.map(article => (
                      <label key={article.id} className="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded">
                        <input
                          type="checkbox"
                          checked={selectedArticles.includes(article.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedArticles([...selectedArticles, article.id]);
                            } else {
                              setSelectedArticles(selectedArticles.filter(id => id !== article.id));
                            }
                          }}
                        />
                        <div className="flex-1">
                          <div className="text-sm">{article.title}</div>
                          {article.published && (
                            <div className="text-xs text-gray-500">
                              {new Date(article.published).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                  <button
                    onClick={handleAssignArticles}
                    disabled={loading || selectedArticles.length === 0}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
                  >
                    {loading ? 'Assigning...' : `Assign ${selectedArticles.length} Articles`}
                  </button>
                </>
              )}
            </div>
          )}
        </div>

        {deleteConfirm && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <div className="bg-white p-6 rounded-lg shadow-xl">
              <h3 className="text-lg font-semibold mb-4">Confirm Delete</h3>
              <p className="mb-4">
                Delete author "{authors.find(a => a.id === deleteConfirm.authorId)?.name}"?
              </p>
              <div className="space-y-2 mb-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    checked={!deleteConfirm.deleteArticles}
                    onChange={() => setDeleteConfirm({ ...deleteConfirm, deleteArticles: false })}
                  />
                  <span>Keep articles (reassign to no author)</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    checked={deleteConfirm.deleteArticles}
                    onChange={() => setDeleteConfirm({ ...deleteConfirm, deleteArticles: true })}
                  />
                  <span className="text-red-600">Delete author and all their articles</span>
                </label>
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setDeleteConfirm(null)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDeleteAuthor(deleteConfirm.authorId, deleteConfirm.deleteArticles)}
                  className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                >
                  {deleteConfirm.deleteArticles ? 'Delete Author & Articles' : 'Delete Author Only'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthorManagementModal;