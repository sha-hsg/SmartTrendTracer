/**
 * React hook for working with the new tag concept system
 */
import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  TagConcept,
  TagWithConcept,
  TagHierarchy,
  TagStatistics,
  EntityType
} from '../types/tagConcept';

const API_BASE = 'http://localhost:8000/api/tags-concept';

/**
 * Hook for tag concept operations
 */
export function useTagConcepts() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Resolve a tag text to its concept
   */
  const resolveTag = useCallback(async (tagText: string): Promise<TagConcept | null> => {
    try {
      const response = await axios.get(`${API_BASE}/resolve/${encodeURIComponent(tagText)}`);
      return response.data;
    } catch (err) {
      console.error('Error resolving tag:', err);
      return null;
    }
  }, []);

  /**
   * Create a new tag concept
   */
  const createConcept = useCallback(async (
    tagText: string,
    entityType: EntityType = 'concept'
  ): Promise<TagConcept | null> => {
    try {
      const response = await axios.post(`${API_BASE}/create`, null, {
        params: { tag_text: tagText, entity_type: entityType }
      });
      return response.data;
    } catch (err) {
      console.error('Error creating concept:', err);
      setError('Failed to create concept');
      return null;
    }
  }, []);

  /**
   * Add tag to content
   */
  const addTag = useCallback(async (
    contentType: 'tweet' | 'paper' | 'article',
    contentId: string,
    tagText: string,
    tagType: string = 'manual'
  ): Promise<boolean> => {
    try {
      await axios.post(`${API_BASE}/${contentType}s/${contentId}/tags`, {
        tag_text: tagText,
        tag_type: tagType
      });
      return true;
    } catch (err) {
      console.error('Error adding tag:', err);
      return false;
    }
  }, []);

  /**
   * Add multiple tags to content
   */
  const addBulkTags = useCallback(async (
    contentType: 'tweet' | 'paper' | 'article',
    contentId: string,
    tags: string[],
    tagType: string = 'manual'
  ): Promise<{ added: number; failed: number }> => {
    try {
      const response = await axios.post(`${API_BASE}/${contentType}s/${contentId}/tags/bulk`, {
        tags,
        tag_type: tagType
      });
      return response.data;
    } catch (err) {
      console.error('Error adding bulk tags:', err);
      return { added: 0, failed: tags.length };
    }
  }, []);

  /**
   * Get tags for content
   */
  const getContentTags = useCallback(async (
    contentType: 'tweet' | 'paper' | 'article',
    contentId: string
  ): Promise<TagWithConcept[]> => {
    try {
      const response = await axios.get(`${API_BASE}/${contentType}s/${contentId}/tags`);
      return response.data;
    } catch (err) {
      console.error('Error getting tags:', err);
      return [];
    }
  }, []);

  /**
   * Filter content by tag
   */
  const filterByTag = useCallback(async (
    contentType: 'tweet' | 'paper' | 'article',
    tag: string,
    includeDescendants: boolean = true
  ): Promise<string[]> => {
    try {
      const response = await axios.get(`${API_BASE}/filter/${contentType}s`, {
        params: { tag, include_descendants: includeDescendants }
      });
      return response.data;
    } catch (err) {
      console.error('Error filtering by tag:', err);
      return [];
    }
  }, []);

  /**
   * Get tag hierarchy
   */
  const getHierarchy = useCallback(async (): Promise<TagHierarchy | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE}/hierarchy`);
      return response.data;
    } catch (err) {
      console.error('Error getting hierarchy:', err);
      setError('Failed to load hierarchy');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get all concepts
   */
  const getAllConcepts = useCallback(async (
    entityType?: EntityType,
    limit: number = 100
  ): Promise<TagConcept[]> => {
    try {
      const response = await axios.get(`${API_BASE}/concepts`, {
        params: { entity_type: entityType, limit }
      });
      return response.data;
    } catch (err) {
      console.error('Error getting concepts:', err);
      return [];
    }
  }, []);

  /**
   * Get concept details
   */
  const getConceptDetails = useCallback(async (conceptId: string): Promise<TagConcept | null> => {
    try {
      const response = await axios.get(`${API_BASE}/concepts/${conceptId}`);
      return response.data;
    } catch (err) {
      console.error('Error getting concept details:', err);
      return null;
    }
  }, []);

  /**
   * Search tags
   */
  const searchTags = useCallback(async (query: string, limit: number = 10): Promise<TagConcept[]> => {
    try {
      const response = await axios.get(`${API_BASE}/search`, {
        params: { q: query, limit }
      });
      return response.data;
    } catch (err) {
      console.error('Error searching tags:', err);
      return [];
    }
  }, []);

  /**
   * Get tag statistics
   */
  const getStatistics = useCallback(async (): Promise<TagStatistics | null> => {
    try {
      const response = await axios.get(`${API_BASE}/statistics`);
      return response.data;
    } catch (err) {
      console.error('Error getting statistics:', err);
      return null;
    }
  }, []);

  /**
   * Migrate legacy tags
   */
  const migrateTags = useCallback(async (): Promise<{ migrated: number; skipped: number; errors: number } | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE}/migrate`);
      return response.data;
    } catch (err) {
      console.error('Error migrating tags:', err);
      setError('Failed to migrate tags');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    resolveTag,
    createConcept,
    addTag,
    addBulkTags,
    getContentTags,
    filterByTag,
    getHierarchy,
    getAllConcepts,
    getConceptDetails,
    searchTags,
    getStatistics,
    migrateTags
  };
}

/**
 * Hook for managing tags on a specific content item
 */
export function useContentTags(
  contentType: 'tweet' | 'paper' | 'article',
  contentId: string
) {
  const [tags, setTags] = useState<TagWithConcept[]>([]);
  const [loading, setLoading] = useState(false);
  const { getContentTags, addTag, addBulkTags } = useTagConcepts();

  // Load tags on mount
  useEffect(() => {
    if (contentId) {
      loadTags();
    }
  }, [contentId]);

  const loadTags = async () => {
    setLoading(true);
    const fetchedTags = await getContentTags(contentType, contentId);
    setTags(fetchedTags);
    setLoading(false);
  };

  const addNewTag = async (tagText: string, tagType: string = 'manual') => {
    const success = await addTag(contentType, contentId, tagText, tagType);
    if (success) {
      await loadTags(); // Reload tags
    }
    return success;
  };

  const addNewTags = async (tagTexts: string[], tagType: string = 'manual') => {
    const result = await addBulkTags(contentType, contentId, tagTexts, tagType);
    await loadTags(); // Reload tags
    return result;
  };

  return {
    tags,
    loading,
    reload: loadTags,
    addTag: addNewTag,
    addTags: addNewTags
  };
}