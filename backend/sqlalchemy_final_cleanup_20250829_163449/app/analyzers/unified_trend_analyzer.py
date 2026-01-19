"""
Unified Trend and Clustering Analyzer
Provides tag-based trends and clustering for both tweets and articles
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import re

from app.models import Tweet, Tag, get_db
from app.models.substack import SubstackArticle, ArticleTag, SubstackAuthor


class UnifiedTrendAnalyzer:
    """Unified analyzer for tweets and articles with clustering capabilities"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def analyze_tweet_tag_trends(self, days: int = 7, limit: int = 20) -> Dict[str, Any]:
        """
        Analyze tag trends for tweets similar to article analysis
        Returns tag frequencies, velocity, and co-occurrence patterns
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get tag counts over time
        daily_tag_counts = self.db.query(
            func.date(Tweet.created_at).label('date'),
            Tag.tag,
            func.count(Tag.id).label('count')
        ).join(Tweet).filter(
            Tweet.created_at >= start_date
        ).group_by(
            func.date(Tweet.created_at),
            Tag.tag
        ).all()
        
        # Organize by tag
        tag_timeline = defaultdict(list)
        tag_totals = Counter()
        
        for date, tag, count in daily_tag_counts:
            tag_timeline[tag].append({
                'date': str(date),
                'count': count
            })
            tag_totals[tag] += count
        
        # Calculate velocity (compare first half vs second half)
        mid_point = start_date + timedelta(days=days/2)
        
        first_half_tags = self.db.query(
            Tag.tag,
            func.count(Tag.id).label('count')
        ).join(Tweet).filter(
            and_(
                Tweet.created_at >= start_date,
                Tweet.created_at < mid_point
            )
        ).group_by(Tag.tag).all()
        
        second_half_tags = self.db.query(
            Tag.tag,
            func.count(Tag.id).label('count')
        ).join(Tweet).filter(
            Tweet.created_at >= mid_point
        ).group_by(Tag.tag).all()
        
        first_half_dict = {tag: count for tag, count in first_half_tags}
        second_half_dict = {tag: count for tag, count in second_half_tags}
        
        # Calculate velocity for each tag
        tag_velocities = []
        for tag in tag_totals.keys():
            first_count = first_half_dict.get(tag, 0)
            second_count = second_half_dict.get(tag, 0)
            
            if first_count > 0:
                velocity = ((second_count - first_count) / first_count) * 100
            elif second_count > 0:
                velocity = 100  # New tag
            else:
                velocity = 0
            
            trend = 'rising' if velocity > 20 else 'falling' if velocity < -20 else 'stable'
            
            tag_velocities.append({
                'tag': tag,
                'total_count': tag_totals[tag],
                'velocity': velocity,
                'trend': trend,
                'first_half': first_count,
                'second_half': second_count
            })
        
        # Sort by velocity
        tag_velocities.sort(key=lambda x: abs(x['velocity']), reverse=True)
        
        # Get tag co-occurrence
        tag_pairs = self._get_tag_cooccurrence_tweets(start_date)
        
        return {
            'period_days': days,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'top_tags': [
                {'tag': tag, 'count': count}
                for tag, count in tag_totals.most_common(limit)
            ],
            'tag_timeline': dict(tag_timeline),
            'tag_velocities': tag_velocities[:15],
            'rising_tags': [t for t in tag_velocities if t['trend'] == 'rising'][:10],
            'falling_tags': [t for t in tag_velocities if t['trend'] == 'falling'][:10],
            'tag_relationships': tag_pairs[:10]
        }
    
    def analyze_article_tag_trends(self, days: int = 7, limit: int = 20) -> Dict[str, Any]:
        """
        Analyze tag trends for articles
        Returns tag frequencies, velocity, and co-occurrence patterns
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get articles with tags
        articles = self.db.query(SubstackArticle).filter(
            SubstackArticle.published_at >= start_date,
            SubstackArticle.deleted == False
        ).all()
        
        # Count tags over time
        daily_tag_counts = defaultdict(lambda: defaultdict(int))
        tag_totals = Counter()
        
        for article in articles:
            date = article.published_at.date()
            for tag in article.tags:
                daily_tag_counts[tag.tag][str(date)] += 1
                tag_totals[tag.tag] += 1
        
        # Format timeline
        tag_timeline = {}
        for tag, dates in daily_tag_counts.items():
            tag_timeline[tag] = [
                {'date': date, 'count': count}
                for date, count in sorted(dates.items())
            ]
        
        # Calculate velocity
        mid_point = start_date + timedelta(days=days/2)
        tag_velocities = []
        
        for tag, total in tag_totals.items():
            # Count in each half
            first_half = sum(
                1 for article in articles
                if (article.published_at.replace(tzinfo=timezone.utc) if article.published_at.tzinfo is None else article.published_at) < mid_point
                for t in article.tags if t.tag == tag
            )
            second_half = total - first_half
            
            if first_half > 0:
                velocity = ((second_half - first_half) / first_half) * 100
            elif second_half > 0:
                velocity = 100
            else:
                velocity = 0
            
            trend = 'rising' if velocity > 20 else 'falling' if velocity < -20 else 'stable'
            
            tag_velocities.append({
                'tag': tag,
                'total_count': total,
                'velocity': velocity,
                'trend': trend,
                'first_half': first_half,
                'second_half': second_half
            })
        
        tag_velocities.sort(key=lambda x: abs(x['velocity']), reverse=True)
        
        # Get tag co-occurrence
        tag_pairs = self._get_tag_cooccurrence_articles(articles)
        
        return {
            'period_days': days,
            'total_articles': len(articles),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'top_tags': [
                {'tag': tag, 'count': count}
                for tag, count in tag_totals.most_common(limit)
            ],
            'tag_timeline': tag_timeline,
            'tag_velocities': tag_velocities[:15],
            'rising_tags': [t for t in tag_velocities if t['trend'] == 'rising'][:10],
            'falling_tags': [t for t in tag_velocities if t['trend'] == 'falling'][:10],
            'tag_relationships': tag_pairs[:10]
        }
    
    def cluster_tweets(self, days: int = 7, n_clusters: Optional[int] = None) -> Dict[str, Any]:
        """
        Cluster tweets based on content similarity
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get tweets
        tweets = self.db.query(Tweet).filter(
            Tweet.created_at >= start_date
        ).all()
        
        if len(tweets) < 10:
            return {
                'error': 'Not enough tweets for clustering',
                'tweet_count': len(tweets)
            }
        
        # Prepare text for clustering
        texts = []
        tweet_data = []
        for tweet in tweets:
            texts.append(tweet.text)
            tweet_data.append({
                'id': tweet.id,
                'author': tweet.author_username,
                'text': tweet.text[:100],
                'created_at': tweet.created_at.isoformat()
            })
        
        # Vectorize text
        try:
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                max_df=0.8,
                min_df=2
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Determine optimal clusters if not specified
            if n_clusters is None:
                n_clusters = self._find_optimal_clusters(tfidf_matrix, max_k=min(10, len(tweets)//3))
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(tfidf_matrix)
            
            # Calculate silhouette score
            if n_clusters > 1:
                score = silhouette_score(tfidf_matrix, clusters)
            else:
                score = 0
            
            # Get cluster information
            feature_names = vectorizer.get_feature_names_out()
            cluster_info = []
            
            for i in range(n_clusters):
                cluster_indices = [j for j in range(len(tweets)) if clusters[j] == i]
                if not cluster_indices:
                    continue
                
                # Get top terms for this cluster
                cluster_center = kmeans.cluster_centers_[i]
                top_indices = cluster_center.argsort()[-10:][::-1]
                top_terms = [feature_names[idx] for idx in top_indices]
                
                # Get sample tweets
                sample_tweets = [tweet_data[idx] for idx in cluster_indices[:5]]
                
                # Get most common tags in cluster
                cluster_tags = Counter()
                for idx in cluster_indices:
                    for tag in tweets[idx].tags:
                        cluster_tags[tag.tag] += 1
                
                cluster_info.append({
                    'cluster_id': i,
                    'size': len(cluster_indices),
                    'theme': ' + '.join(top_terms[:3]),
                    'keywords': top_terms[:5],
                    'top_tags': [
                        {'tag': tag, 'count': count}
                        for tag, count in cluster_tags.most_common(5)
                    ],
                    'sample_tweets': sample_tweets,
                    'authors': Counter(
                        tweets[idx].author_username for idx in cluster_indices
                    ).most_common(3)
                })
            
            # Sort by cluster size
            cluster_info.sort(key=lambda x: x['size'], reverse=True)
            
            return {
                'period_days': days,
                'total_tweets': len(tweets),
                'n_clusters': n_clusters,
                'silhouette_score': float(score),
                'clusters': cluster_info,
                'quality_rating': self._rate_clustering_quality(score)
            }
            
        except Exception as e:
            return {
                'error': f'Clustering failed: {str(e)}',
                'tweet_count': len(tweets)
            }
    
    def cluster_articles(self, days: int = 30, n_clusters: Optional[int] = None) -> Dict[str, Any]:
        """
        Enhanced clustering for articles with better feature extraction
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get articles
        articles = self.db.query(SubstackArticle).filter(
            SubstackArticle.published_at >= start_date,
            SubstackArticle.deleted == False
        ).all()
        
        if len(articles) < 5:
            return {
                'error': 'Not enough articles for clustering',
                'article_count': len(articles)
            }
        
        # Prepare text - use title, subtitle, and preview
        texts = []
        article_data = []
        for article in articles:
            text = f"{article.title} {article.subtitle or ''}"
            if article.preview:
                text += f" {article.preview[:500]}"
            texts.append(text)
            
            article_data.append({
                'id': article.id,
                'title': article.title,
                'author': article.author.name,
                'published_at': article.published_at.isoformat()
            })
        
        try:
            # Use better TF-IDF parameters for articles
            vectorizer = TfidfVectorizer(
                max_features=150,
                stop_words='english',
                ngram_range=(1, 2),  # Include bigrams
                max_df=0.9,
                min_df=1 if len(articles) < 20 else 2
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Determine optimal clusters
            if n_clusters is None:
                n_clusters = self._find_optimal_clusters(
                    tfidf_matrix, 
                    max_k=min(8, max(3, len(articles)//4))
                )
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(tfidf_matrix)
            
            # Calculate silhouette score
            if n_clusters > 1:
                score = silhouette_score(tfidf_matrix, clusters)
            else:
                score = 0
            
            # Get cluster information
            feature_names = vectorizer.get_feature_names_out()
            cluster_info = []
            
            for i in range(n_clusters):
                cluster_indices = [j for j in range(len(articles)) if clusters[j] == i]
                if not cluster_indices:
                    continue
                
                # Get top terms
                cluster_center = kmeans.cluster_centers_[i]
                top_indices = cluster_center.argsort()[-15:][::-1]
                top_terms = [feature_names[idx] for idx in top_indices]
                
                # Get articles in cluster
                cluster_articles = [articles[idx] for idx in cluster_indices]
                
                # Get tags and authors
                cluster_tags = Counter()
                cluster_authors = Counter()
                total_words = 0
                
                for article in cluster_articles:
                    for tag in article.tags:
                        cluster_tags[tag.tag] += 1
                    cluster_authors[article.author.name] += 1
                    total_words += article.word_count or 0
                
                cluster_info.append({
                    'cluster_id': i,
                    'size': len(cluster_indices),
                    'theme': ' + '.join(top_terms[:3]),
                    'keywords': top_terms[:7],
                    'top_tags': [
                        {'tag': tag, 'count': count}
                        for tag, count in cluster_tags.most_common(5)
                    ],
                    'articles': [
                        {
                            'id': a.id,
                            'title': a.title,
                            'author': a.author.name,
                            'published_at': a.published_at.isoformat()
                        }
                        for a in cluster_articles[:3]
                    ],
                    'authors': [
                        {'name': author, 'count': count}
                        for author, count in cluster_authors.most_common(3)
                    ],
                    'avg_word_count': total_words // len(cluster_articles) if cluster_articles else 0
                })
            
            cluster_info.sort(key=lambda x: x['size'], reverse=True)
            
            return {
                'period_days': days,
                'total_articles': len(articles),
                'n_clusters': n_clusters,
                'silhouette_score': float(score),
                'clusters': cluster_info,
                'quality_rating': self._rate_clustering_quality(score)
            }
            
        except Exception as e:
            return {
                'error': f'Clustering failed: {str(e)}',
                'article_count': len(articles)
            }
    
    def _find_optimal_clusters(self, matrix, max_k: int = 10) -> int:
        """Find optimal number of clusters using silhouette score"""
        if matrix.shape[0] < 3:
            return 2
        
        scores = []
        k_range = range(2, min(max_k + 1, matrix.shape[0]))
        
        for k in k_range:
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=5)
                clusters = kmeans.fit_predict(matrix)
                score = silhouette_score(matrix, clusters)
                scores.append((k, score))
            except:
                continue
        
        if not scores:
            return 3
        
        # Return k with highest silhouette score
        return max(scores, key=lambda x: x[1])[0]
    
    def _rate_clustering_quality(self, score: float) -> str:
        """Rate clustering quality based on silhouette score"""
        if score > 0.7:
            return 'excellent'
        elif score > 0.5:
            return 'good'
        elif score > 0.3:
            return 'fair'
        else:
            return 'poor'
    
    def _get_tag_cooccurrence_tweets(self, start_date: datetime) -> List[Dict]:
        """Get tag co-occurrence patterns for tweets"""
        tweets = self.db.query(Tweet).filter(
            Tweet.created_at >= start_date
        ).all()
        
        cooccurrence = defaultdict(Counter)
        
        for tweet in tweets:
            tags = [tag.tag for tag in tweet.tags]
            for i, tag1 in enumerate(tags):
                for tag2 in tags[i+1:]:
                    cooccurrence[tag1][tag2] += 1
                    cooccurrence[tag2][tag1] += 1
        
        # Format results
        pairs = []
        seen = set()
        
        for tag1, related in cooccurrence.items():
            for tag2, count in related.most_common(3):
                pair = tuple(sorted([tag1, tag2]))
                if pair not in seen and count > 1:
                    seen.add(pair)
                    pairs.append({
                        'tags': list(pair),
                        'count': count
                    })
        
        pairs.sort(key=lambda x: x['count'], reverse=True)
        return pairs
    
    def _get_tag_cooccurrence_articles(self, articles: List[SubstackArticle]) -> List[Dict]:
        """Get tag co-occurrence patterns for articles"""
        cooccurrence = defaultdict(Counter)
        
        for article in articles:
            tags = [tag.tag for tag in article.tags]
            for i, tag1 in enumerate(tags):
                for tag2 in tags[i+1:]:
                    cooccurrence[tag1][tag2] += 1
                    cooccurrence[tag2][tag1] += 1
        
        # Format results
        pairs = []
        seen = set()
        
        for tag1, related in cooccurrence.items():
            for tag2, count in related.most_common(3):
                pair = tuple(sorted([tag1, tag2]))
                if pair not in seen and count > 1:
                    seen.add(pair)
                    pairs.append({
                        'tags': list(pair),
                        'count': count
                    })
        
        pairs.sort(key=lambda x: x['count'], reverse=True)
        return pairs