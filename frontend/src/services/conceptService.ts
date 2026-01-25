/**
 * Service for managing concepts (tags) in the frontend
 * Handles fetching, caching, and concept operations
 */

import axios from 'axios';
import { Concept, ConceptWithCount } from '@/types/concept';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ConceptService {
  private conceptCache: Map<string, Concept> = new Map();
  private conceptsBySlug: Map<string, Concept> = new Map();

  /**
   * Get a concept by ID, with caching
   */
  async getConcept(conceptId: string): Promise<Concept | null> {
    // Check cache first
    if (this.conceptCache.has(conceptId)) {
      return this.conceptCache.get(conceptId)!;
    }

    try {
      const response = await axios.get(`${API_BASE_URL}/api/concepts/${conceptId}`);
      const concept = response.data;
      this.cacheContent(concept);
      return concept;
    } catch (error) {
      console.error(`Failed to fetch concept ${conceptId}:`, error);
      return null;
    }
  }

  /**
   * Get multiple concepts by IDs
   */
  async getConcepts(conceptIds: string[]): Promise<Map<string, Concept>> {
    const results = new Map<string, Concept>();
    const missingIds: string[] = [];

    // Check cache for each ID
    for (const id of conceptIds) {
      if (this.conceptCache.has(id)) {
        results.set(id, this.conceptCache.get(id)!);
      } else {
        missingIds.push(id);
      }
    }

    // Fetch missing concepts
    if (missingIds.length > 0) {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/concepts/batch`, {
          concept_ids: missingIds
        });
        
        for (const concept of response.data.concepts) {
          this.cacheContent(concept);
          results.set(concept.concept_id, concept);
        }
      } catch (error) {
        console.error('Failed to fetch concepts:', error);
      }
    }

    return results;
  }

  /**
   * Search for concepts by text
   */
  async searchConcepts(query: string, limit: number = 10): Promise<Concept[]> {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/concepts/search`, {
        params: { q: query, limit }
      });
      
      const concepts = response.data.concepts || [];
      concepts.forEach((c: Concept) => this.cacheContent(c));
      return concepts;
    } catch (error) {
      console.error('Failed to search concepts:', error);
      return [];
    }
  }

  /**
   * Get all concepts with usage counts
   */
  async getConceptStats(contentType?: 'tweet' | 'paper' | 'article'): Promise<ConceptWithCount[]> {
    try {
      const params = contentType ? { content_type: contentType } : {};
      const response = await axios.get(`${API_BASE_URL}/api/concepts/stats`, { params });
      
      const concepts = response.data.top_concepts || [];
      concepts.forEach((c: ConceptWithCount) => this.cacheContent(c));
      return concepts;
    } catch (error) {
      console.error('Failed to fetch concept stats:', error);
      return [];
    }
  }

  /**
   * Create or find a concept from text
   */
  async createConceptFromText(text: string): Promise<Concept | null> {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/concepts`, {
        text: text
      });
      
      const concept = response.data.concept;
      if (concept) {
        this.cacheContent(concept);
      }
      return concept;
    } catch (error) {
      console.error('Failed to create concept:', error);
      return null;
    }
  }

  /**
   * Add a concept to content (tweet, paper, article)
   */
  async addConceptToContent(
    contentType: 'tweet' | 'paper' | 'article',
    contentId: string,
    text: string
  ): Promise<Concept | null> {
    try {
      const endpoint = `${API_BASE_URL}/api/${contentType}s/${contentId}/concepts`;
      const response = await axios.post(endpoint, null, {
        params: { text }
      });
      
      const concept = response.data.concept;
      if (concept) {
        this.cacheContent(concept);
      }
      return concept;
    } catch (error) {
      console.error('Failed to add concept:', error);
      return null;
    }
  }

  /**
   * Remove a concept from content
   */
  async removeConceptFromContent(
    contentType: 'tweet' | 'paper' | 'article',
    contentId: string,
    conceptId: string
  ): Promise<boolean> {
    try {
      const endpoint = `${API_BASE_URL}/api/${contentType}s/${contentId}/concepts/${conceptId}`;
      await axios.delete(endpoint);
      return true;
    } catch (error) {
      console.error('Failed to remove concept:', error);
      return false;
    }
  }

  /**
   * Get concept by slug
   */
  getConceptBySlug(slug: string): Concept | null {
    return this.conceptsBySlug.get(slug) || null;
  }

  /**
   * Cache a concept
   */
  private cacheContent(concept: Concept) {
    this.conceptCache.set(concept.concept_id, concept);
    this.conceptsBySlug.set(concept.slug, concept);
  }

  /**
   * Clear the cache
   */
  clearCache() {
    this.conceptCache.clear();
    this.conceptsBySlug.clear();
  }

  /**
   * Convert legacy tag to concept search
   */
  async findConceptForLegacyTag(tagText: string): Promise<Concept | null> {
    // First check cache by slug
    const slug = tagText.toLowerCase().replace(/[\s-]+/g, '_');
    const cached = this.getConceptBySlug(slug);
    if (cached) return cached;

    // Search for the concept
    const results = await this.searchConcepts(tagText, 1);
    return results.length > 0 ? results[0] : null;
  }

  /**
   * Format concept for display
   */
  formatConcept(concept: Concept): string {
    return concept.display_name || concept.slug.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  /**
   * Get concept color based on entity type
   */
  getConceptColor(concept: Concept): string {
    if (concept.color) return concept.color;
    
    switch (concept.entity_type) {
      case 'person': return '#3B82F6'; // blue
      case 'organisation': return '#10B981'; // green
      case 'location': return '#F59E0B'; // amber
      case 'event': return '#8B5CF6'; // purple
      case 'product': return '#EF4444'; // red
      case 'topic':
      default: return '#6B7280'; // gray
    }
  }

  /**
   * Get concept icon based on entity type
   */
  getConceptIcon(concept: Concept): string {
    if (concept.icon) return concept.icon;
    
    switch (concept.entity_type) {
      case 'person': return '👤';
      case 'organisation': return '🏢';
      case 'location': return '📍';
      case 'event': return '📅';
      case 'product': return '📦';
      case 'topic':
      default: return '🏷️';
    }
  }
}

// Export singleton instance
export const conceptService = new ConceptService();
export default conceptService;