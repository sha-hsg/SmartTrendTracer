"""
Article Clustering Service based on Tags
Clusters articles using tag co-occurrence and similarity
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

class ArticleClusteringService:
    """Service for clustering articles based on their tags"""
    
    def __init__(self):
        self.articles = []
        self.tag_vectors = None
        self.similarity_matrix = None
        self.clusters = None
        
    def prepare_articles_data(self, articles: List[Dict[str, Any]]) -> None:
        """
        Prepare articles data for clustering
        
        Args:
            articles: List of article dictionaries with 'id', 'title', 'tags' fields
        """
        self.articles = articles
        self._create_tag_vectors()
        
    def _create_tag_vectors(self) -> np.ndarray:
        """
        Create binary vectors for articles based on their tags
        Each article is represented as a vector where 1 indicates tag presence
        """
        # Collect all unique tags
        all_tags = set()
        for article in self.articles:
            tags = article.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
            all_tags.update(tags)
        
        # Create tag to index mapping
        self.tag_to_idx = {tag: idx for idx, tag in enumerate(sorted(all_tags))}
        self.idx_to_tag = {idx: tag for tag, idx in self.tag_to_idx.items()}
        
        # Create binary vectors
        n_articles = len(self.articles)
        n_tags = len(all_tags)
        self.tag_vectors = np.zeros((n_articles, n_tags))
        
        for i, article in enumerate(self.articles):
            tags = article.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
            for tag in tags:
                if tag in self.tag_to_idx:
                    self.tag_vectors[i, self.tag_to_idx[tag]] = 1
                    
        return self.tag_vectors
    
    def calculate_similarity_matrix(self) -> np.ndarray:
        """
        Calculate cosine similarity matrix between all articles
        """
        if self.tag_vectors is None:
            raise ValueError("Tag vectors not initialized. Call prepare_articles_data first.")
            
        self.similarity_matrix = cosine_similarity(self.tag_vectors)
        return self.similarity_matrix
    
    def cluster_kmeans(self, n_clusters: int = 5) -> Dict[str, Any]:
        """
        Perform K-means clustering on articles
        
        Args:
            n_clusters: Number of clusters to create
            
        Returns:
            Clustering results with cluster assignments and centers
        """
        if self.tag_vectors is None:
            raise ValueError("Tag vectors not initialized. Call prepare_articles_data first.")
            
        # Apply K-means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(self.tag_vectors)
        
        # Get cluster centers and find most representative tags
        cluster_centers = kmeans.cluster_centers_
        clusters = defaultdict(list)
        
        for i, label in enumerate(cluster_labels):
            article = self.articles[i].copy()
            article['cluster'] = int(label)
            clusters[int(label)].append(article)
        
        # Find representative tags for each cluster
        cluster_info = {}
        for cluster_id in range(n_clusters):
            center = cluster_centers[cluster_id]
            top_tag_indices = np.argsort(center)[-5:][::-1]  # Top 5 tags
            top_tags = [self.idx_to_tag[idx] for idx in top_tag_indices if center[idx] > 0]
            
            cluster_info[cluster_id] = {
                'articles': clusters[cluster_id],
                'size': len(clusters[cluster_id]),
                'representative_tags': top_tags,
                'center': center.tolist()
            }
            
        return {
            'method': 'kmeans',
            'n_clusters': n_clusters,
            'clusters': cluster_info,
            'silhouette_score': self._calculate_silhouette_score(cluster_labels)
        }
    
    def cluster_hierarchical(self, n_clusters: Optional[int] = None, 
                            distance_threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Perform hierarchical clustering on articles
        
        Args:
            n_clusters: Number of clusters (if None, use distance_threshold)
            distance_threshold: Distance threshold for clustering
            
        Returns:
            Clustering results
        """
        if self.tag_vectors is None:
            raise ValueError("Tag vectors not initialized. Call prepare_articles_data first.")
            
        # Apply hierarchical clustering
        if n_clusters is not None:
            clustering = AgglomerativeClustering(n_clusters=n_clusters)
        else:
            clustering = AgglomerativeClustering(
                n_clusters=None, 
                distance_threshold=distance_threshold or 0.5,
                compute_full_tree=True
            )
            
        cluster_labels = clustering.fit_predict(self.tag_vectors)
        
        # Organize results
        clusters = defaultdict(list)
        for i, label in enumerate(cluster_labels):
            article = self.articles[i].copy()
            article['cluster'] = int(label)
            clusters[int(label)].append(article)
        
        # Get cluster characteristics
        cluster_info = {}
        unique_labels = np.unique(cluster_labels)
        
        for cluster_id in unique_labels:
            cluster_articles = clusters[cluster_id]
            
            # Collect all tags in cluster
            cluster_tags = []
            for article in cluster_articles:
                tags = article.get('tags', [])
                if isinstance(tags, str):
                    tags = [tags]
                cluster_tags.extend(tags)
            
            # Find most common tags
            tag_counts = Counter(cluster_tags)
            top_tags = [tag for tag, _ in tag_counts.most_common(5)]
            
            cluster_info[int(cluster_id)] = {
                'articles': cluster_articles,
                'size': len(cluster_articles),
                'representative_tags': top_tags,
                'tag_distribution': dict(tag_counts)
            }
            
        return {
            'method': 'hierarchical',
            'n_clusters': len(unique_labels),
            'clusters': cluster_info,
            'silhouette_score': self._calculate_silhouette_score(cluster_labels)
        }
    
    def cluster_dbscan(self, eps: float = 0.3, min_samples: int = 2) -> Dict[str, Any]:
        """
        Perform DBSCAN clustering (density-based)
        
        Args:
            eps: Maximum distance between samples in same cluster
            min_samples: Minimum samples in a neighborhood
            
        Returns:
            Clustering results
        """
        if self.similarity_matrix is None:
            self.calculate_similarity_matrix()
            
        # Convert similarity to distance and ensure non-negative values
        distance_matrix = 1 - self.similarity_matrix
        # Clip to ensure no negative values due to floating point errors
        distance_matrix = np.clip(distance_matrix, 0, None)
        
        # Apply DBSCAN
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
        cluster_labels = dbscan.fit_predict(distance_matrix)
        
        # Organize results
        clusters = defaultdict(list)
        noise_articles = []
        
        for i, label in enumerate(cluster_labels):
            article = self.articles[i].copy()
            article['cluster'] = int(label)
            
            if label == -1:  # Noise point
                noise_articles.append(article)
            else:
                clusters[int(label)].append(article)
        
        # Get cluster characteristics
        cluster_info = {}
        unique_labels = set(cluster_labels)
        unique_labels.discard(-1)  # Remove noise label
        
        for cluster_id in unique_labels:
            cluster_articles = clusters[cluster_id]
            
            # Collect all tags in cluster
            cluster_tags = []
            for article in cluster_articles:
                tags = article.get('tags', [])
                if isinstance(tags, str):
                    tags = [tags]
                cluster_tags.extend(tags)
            
            # Find most common tags
            tag_counts = Counter(cluster_tags)
            top_tags = [tag for tag, _ in tag_counts.most_common(5)]
            
            cluster_info[int(cluster_id)] = {
                'articles': cluster_articles,
                'size': len(cluster_articles),
                'representative_tags': top_tags,
                'tag_distribution': dict(tag_counts)
            }
            
        return {
            'method': 'dbscan',
            'n_clusters': len(unique_labels),
            'clusters': cluster_info,
            'noise_articles': noise_articles,
            'eps': eps,
            'min_samples': min_samples
        }
    
    def find_similar_articles(self, article_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find most similar articles to a given article based on tags
        
        Args:
            article_id: ID of the reference article
            top_k: Number of similar articles to return
            
        Returns:
            List of similar articles with similarity scores
        """
        if self.similarity_matrix is None:
            self.calculate_similarity_matrix()
            
        # Find article index
        article_idx = None
        for i, article in enumerate(self.articles):
            if article.get('id') == article_id:
                article_idx = i
                break
                
        if article_idx is None:
            raise ValueError(f"Article with ID {article_id} not found")
            
        # Get similarity scores
        similarities = self.similarity_matrix[article_idx]
        
        # Get top K similar articles (excluding self)
        similar_indices = np.argsort(similarities)[::-1][1:top_k+1]
        
        similar_articles = []
        for idx in similar_indices:
            article = self.articles[idx].copy()
            article['similarity_score'] = float(similarities[idx])
            similar_articles.append(article)
            
        return similar_articles
    
    def get_tag_co_occurrence_matrix(self) -> Dict[str, Any]:
        """
        Calculate tag co-occurrence matrix
        
        Returns:
            Co-occurrence matrix and tag relationships
        """
        tag_pairs = defaultdict(int)
        tag_counts = defaultdict(int)
        
        for article in self.articles:
            tags = article.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
                
            # Count individual tags
            for tag in tags:
                tag_counts[tag] += 1
                
            # Count tag pairs
            for i, tag1 in enumerate(tags):
                for tag2 in tags[i+1:]:
                    pair = tuple(sorted([tag1, tag2]))
                    tag_pairs[pair] += 1
                    
        # Find strongest associations
        strong_associations = []
        for (tag1, tag2), count in tag_pairs.items():
            # Calculate association strength (Jaccard similarity)
            union = tag_counts[tag1] + tag_counts[tag2] - count
            jaccard = count / union if union > 0 else 0
            
            strong_associations.append({
                'tag1': tag1,
                'tag2': tag2,
                'co_occurrence_count': count,
                'jaccard_similarity': jaccard
            })
            
        # Sort by co-occurrence count
        strong_associations.sort(key=lambda x: x['co_occurrence_count'], reverse=True)
        
        return {
            'tag_counts': dict(tag_counts),
            'tag_pairs': {f"{k[0]}-{k[1]}": v for k, v in tag_pairs.items()},
            'strong_associations': strong_associations[:20],  # Top 20 associations
            'total_tags': len(tag_counts),
            'total_pairs': len(tag_pairs)
        }
    
    def get_cluster_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all clustering methods
        
        Returns:
            Summary of clustering results
        """
        summary = {
            'total_articles': len(self.articles),
            'total_unique_tags': len(self.tag_to_idx) if hasattr(self, 'tag_to_idx') else 0,
            'articles_with_tags': sum(1 for a in self.articles if a.get('tags')),
            'average_tags_per_article': np.mean([len(a.get('tags', [])) for a in self.articles])
        }
        
        # Tag frequency distribution
        all_tags = []
        for article in self.articles:
            tags = article.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
            all_tags.extend(tags)
            
        tag_freq = Counter(all_tags)
        summary['most_common_tags'] = tag_freq.most_common(10)
        summary['tag_frequency_stats'] = {
            'min': min(tag_freq.values()) if tag_freq else 0,
            'max': max(tag_freq.values()) if tag_freq else 0,
            'mean': np.mean(list(tag_freq.values())) if tag_freq else 0,
            'median': np.median(list(tag_freq.values())) if tag_freq else 0
        }
        
        return summary
    
    def _calculate_silhouette_score(self, labels: np.ndarray) -> Optional[float]:
        """Calculate silhouette score for clustering quality"""
        try:
            from sklearn.metrics import silhouette_score
            if len(np.unique(labels)) > 1:
                return float(silhouette_score(self.tag_vectors, labels))
        except Exception:
            pass
        return None
    
    def export_for_visualization(self, method: str = 'pca', n_components: int = 2) -> Dict[str, Any]:
        """
        Export data for 2D/3D visualization
        
        Args:
            method: Dimensionality reduction method ('pca', 'tsne')
            n_components: Number of dimensions (2 or 3)
            
        Returns:
            Coordinates and metadata for visualization
        """
        if self.tag_vectors is None:
            raise ValueError("Tag vectors not initialized. Call prepare_articles_data first.")
            
        # Dimensionality reduction
        if method == 'pca':
            reducer = PCA(n_components=n_components, random_state=42)
            coordinates = reducer.fit_transform(self.tag_vectors)
            explained_variance = reducer.explained_variance_ratio_.tolist()
        else:
            from sklearn.manifold import TSNE
            reducer = TSNE(n_components=n_components, random_state=42)
            coordinates = reducer.fit_transform(self.tag_vectors)
            explained_variance = None
            
        # Prepare visualization data
        viz_data = []
        for i, article in enumerate(self.articles):
            point = {
                'id': article.get('id'),
                'title': article.get('title', ''),
                'tags': article.get('tags', []),
                'x': float(coordinates[i, 0]),
                'y': float(coordinates[i, 1])
            }
            if n_components == 3:
                point['z'] = float(coordinates[i, 2])
            viz_data.append(point)
            
        return {
            'method': method,
            'n_components': n_components,
            'points': viz_data,
            'explained_variance': explained_variance
        }