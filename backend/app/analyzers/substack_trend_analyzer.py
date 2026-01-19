"""
Substack Trend Analyzer
Analyzes trends, topics, and themes from Substack articles
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

class SubstackTrendAnalyzer:
    """Analyzes trends and topics from Substack articles"""
    
    def __init__(self, db: Session):
        self.db = db
        self.time_windows = {
            'hot': timedelta(hours=24),      # Last 24 hours
            'recent': timedelta(days=3),     # Last 3 days
            'week': timedelta(days=7),       # Last week
            'month': timedelta(days=30)      # Last month
        }
    
    def analyze_trends(self, days: int = 7) -> Dict[str, Any]:
        """Main trend analysis function"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get articles in timeframe
        articles = self.db.query(SubstackArticle).filter(
            SubstackArticle.published_at >= start_date,
            SubstackArticle.deleted == False
        ).all()
        
        if not articles:
            return {
                "status": "No articles found",
                "period": f"{days} days",
                "trends": []
            }
        
        # Perform various analyses
        topic_trends = self._analyze_topic_trends(articles)
        author_trends = self._analyze_author_trends(articles, days)
        tag_trends = self._analyze_tag_trends(articles)
        snippet_insights = self._analyze_snippet_insights(articles)
        velocity_trends = self._calculate_topic_velocity(articles, days)
        content_clusters = self._cluster_content(articles)
        
        return {
            "period": f"{days} days",
            "total_articles": len(articles),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "topic_trends": topic_trends,
            "author_trends": author_trends,
            "tag_trends": tag_trends,
            "snippet_insights": snippet_insights,
            "velocity_trends": velocity_trends,
            "content_clusters": content_clusters,
            "emerging_themes": self._identify_emerging_themes(articles),
            "summary": self._generate_trend_summary(
                topic_trends, author_trends, velocity_trends
            )
        }
    
    def _analyze_topic_trends(self, articles: List[SubstackArticle]) -> Dict:
        """Analyze topic frequency and trends"""
        # Extract topics from titles and content
        all_text = []
        for article in articles:
            text = f"{article.title} {article.subtitle or ''}"
            if article.content_markdown:
                # Get first 1000 chars for topic extraction
                text += f" {article.content_markdown[:1000]}"
            all_text.append(text.lower())
        
        # Use TF-IDF to extract important terms
        if all_text:
            try:
                vectorizer = TfidfVectorizer(
                    max_features=50,
                    stop_words='english',
                    ngram_range=(1, 3),
                    min_df=2
                )
                tfidf_matrix = vectorizer.fit_transform(all_text)
                feature_names = vectorizer.get_feature_names_out()
                
                # Get top topics
                scores = tfidf_matrix.sum(axis=0).A1
                top_indices = scores.argsort()[-20:][::-1]
                
                topics = []
                for idx in top_indices:
                    topics.append({
                        "term": feature_names[idx],
                        "score": float(scores[idx]),
                        "articles": self._count_articles_with_term(articles, feature_names[idx])
                    })
                
                return {
                    "top_topics": topics[:10],
                    "trending_up": self._identify_trending_topics(articles, topics[:20])
                }
            except Exception as e:
                print(f"Error in TF-IDF analysis: {e}")
                return {"error": str(e)}
        
        return {"top_topics": [], "trending_up": []}
    
    def _analyze_author_trends(self, articles: List[SubstackArticle], days: int) -> Dict:
        """Analyze author activity and engagement"""
        author_stats = defaultdict(lambda: {
            'articles': 0,
            'total_words': 0,
            'snippets': 0,
            'avg_reading_time': 0,
            'topics': set()
        })
        
        for article in articles:
            author = article.author.name
            author_stats[author]['articles'] += 1
            author_stats[author]['total_words'] += article.word_count or 0
            author_stats[author]['snippets'] += len(article.snippets)
            author_stats[author]['avg_reading_time'] += article.reading_time_minutes or 0
            
            # Add topics from tags
            for tag in article.tags:
                author_stats[author]['topics'].add(tag.tag)
        
        # Calculate averages and format
        author_list = []
        for author, stats in author_stats.items():
            article_count = stats['articles']
            author_list.append({
                'author': author,
                'articles': article_count,
                'avg_words': stats['total_words'] // article_count if article_count > 0 else 0,
                'avg_reading_time': stats['avg_reading_time'] / article_count if article_count > 0 else 0,
                'total_snippets': stats['snippets'],
                'topics': list(stats['topics'])[:5],  # Top 5 topics
                'productivity': self._calculate_author_productivity(stats, days)
            })
        
        # Sort by article count
        author_list.sort(key=lambda x: x['articles'], reverse=True)
        
        return {
            'most_active': author_list[:5],
            'total_authors': len(author_list),
            'avg_articles_per_author': sum(a['articles'] for a in author_list) / len(author_list) if author_list else 0
        }
    
    def _analyze_tag_trends(self, articles: List[SubstackArticle]) -> Dict:
        """Analyze tag usage and co-occurrence"""
        tag_counts = Counter()
        tag_cooccurrence = defaultdict(Counter)
        
        for article in articles:
            article_tags = [tag.tag for tag in article.tags]
            tag_counts.update(article_tags)
            
            # Track co-occurrence
            for i, tag1 in enumerate(article_tags):
                for tag2 in article_tags[i+1:]:
                    tag_cooccurrence[tag1][tag2] += 1
                    tag_cooccurrence[tag2][tag1] += 1
        
        # Get top tags
        top_tags = [
            {'tag': tag, 'count': count}
            for tag, count in tag_counts.most_common(15)
        ]
        
        # Find related tags
        tag_relationships = []
        for tag in tag_counts.most_common(10):
            tag_name = tag[0]
            if tag_name in tag_cooccurrence:
                related = tag_cooccurrence[tag_name].most_common(3)
                tag_relationships.append({
                    'tag': tag_name,
                    'related': [{'tag': t, 'strength': c} for t, c in related]
                })
        
        return {
            'top_tags': top_tags,
            'tag_relationships': tag_relationships,
            'unique_tags': len(tag_counts)
        }
    
    def _analyze_snippet_insights(self, articles: List[SubstackArticle]) -> Dict:
        """Analyze highlighted snippets for insights"""
        snippet_categories = Counter()
        important_snippets = []
        snippet_themes = []
        
        for article in articles:
            for snippet in article.snippets:
                # Count categories
                if snippet.category:
                    snippet_categories[snippet.category] += 1
                
                # Collect important snippets
                if snippet.importance and snippet.importance >= 4:
                    important_snippets.append({
                        'text': snippet.text[:200],
                        'category': snippet.category,
                        'article': article.title[:50],
                        'annotation': snippet.annotation
                    })
        
        # Sort important snippets by recency
        important_snippets = important_snippets[:10]
        
        return {
            'categories': dict(snippet_categories.most_common()),
            'important_highlights': important_snippets,
            'total_snippets': sum(snippet_categories.values())
        }
    
    def _calculate_topic_velocity(self, articles: List[SubstackArticle], days: int) -> List[Dict]:
        """Calculate which topics are gaining or losing momentum"""
        if days < 2:
            return []
        
        mid_point = datetime.utcnow() - timedelta(days=days//2)
        
        # Split articles into two periods
        first_half = [a for a in articles if a.published_at < mid_point]
        second_half = [a for a in articles if a.published_at >= mid_point]
        
        # Count topics in each half
        first_topics = self._extract_topic_counts(first_half)
        second_topics = self._extract_topic_counts(second_half)
        
        # Calculate velocity
        velocities = []
        all_topics = set(first_topics.keys()) | set(second_topics.keys())
        
        for topic in all_topics:
            first_count = first_topics.get(topic, 0)
            second_count = second_topics.get(topic, 0)
            
            if first_count > 0:
                velocity = (second_count - first_count) / first_count
            elif second_count > 0:
                velocity = 1.0  # New topic
            else:
                continue
            
            velocities.append({
                'topic': topic,
                'velocity': velocity,
                'first_period': first_count,
                'second_period': second_count,
                'trend': 'rising' if velocity > 0.2 else 'falling' if velocity < -0.2 else 'stable'
            })
        
        # Sort by absolute velocity
        velocities.sort(key=lambda x: abs(x['velocity']), reverse=True)
        
        return velocities[:15]
    
    def _cluster_content(self, articles: List[SubstackArticle]) -> List[Dict]:
        """Cluster articles by content similarity"""
        if len(articles) < 5:
            return []
        
        # Prepare text for clustering
        texts = []
        for article in articles:
            text = f"{article.title} {article.subtitle or ''}"
            if article.preview:
                text += f" {article.preview}"
            texts.append(text)
        
        try:
            # Use TF-IDF for feature extraction
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                max_df=0.8,
                min_df=2
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Determine optimal number of clusters (3-8)
            n_clusters = min(8, max(3, len(articles) // 5))
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(tfidf_matrix)
            
            # Get cluster themes
            feature_names = vectorizer.get_feature_names_out()
            cluster_info = []
            
            for i in range(n_clusters):
                cluster_articles = [articles[j] for j in range(len(articles)) if clusters[j] == i]
                if not cluster_articles:
                    continue
                
                # Get top terms for this cluster
                cluster_center = kmeans.cluster_centers_[i]
                top_indices = cluster_center.argsort()[-5:][::-1]
                top_terms = [feature_names[idx] for idx in top_indices]
                
                cluster_info.append({
                    'cluster_id': i,
                    'size': len(cluster_articles),
                    'theme': ' + '.join(top_terms[:3]),
                    'keywords': top_terms,
                    'articles': [
                        {
                            'title': a.title[:60],
                            'author': a.author.name
                        }
                        for a in cluster_articles[:3]
                    ]
                })
            
            # Sort by cluster size
            cluster_info.sort(key=lambda x: x['size'], reverse=True)
            
            return cluster_info
            
        except Exception as e:
            print(f"Error in clustering: {e}")
            return []
    
    def _identify_emerging_themes(self, articles: List[SubstackArticle]) -> List[Dict]:
        """Identify new or emerging themes"""
        if len(articles) < 10:
            return []
        
        # Sort articles by date
        sorted_articles = sorted(articles, key=lambda a: a.published_at)
        
        # Split into old and new
        split_point = len(sorted_articles) * 3 // 4
        old_articles = sorted_articles[:split_point]
        new_articles = sorted_articles[split_point:]
        
        # Extract topics from each group
        old_topics = self._extract_topic_counts(old_articles)
        new_topics = self._extract_topic_counts(new_articles)
        
        # Find emerging topics (appear in new but not old, or significantly increased)
        emerging = []
        for topic, new_count in new_topics.items():
            old_count = old_topics.get(topic, 0)
            
            if old_count == 0 and new_count >= 2:
                # Brand new topic
                emerging.append({
                    'theme': topic,
                    'type': 'new',
                    'occurrences': new_count,
                    'growth': 'infinite'
                })
            elif old_count > 0 and new_count / old_count > 2:
                # Rapidly growing topic
                emerging.append({
                    'theme': topic,
                    'type': 'growing',
                    'occurrences': new_count,
                    'growth': f"{int((new_count / old_count - 1) * 100)}%"
                })
        
        # Sort by occurrences
        emerging.sort(key=lambda x: x['occurrences'], reverse=True)
        
        return emerging[:10]
    
    def _extract_topic_counts(self, articles: List[SubstackArticle]) -> Counter:
        """Extract and count topics from articles"""
        topics = Counter()
        
        for article in articles:
            # Extract from tags
            for tag in article.tags:
                topics[tag.tag.lower()] += 1
            
            # Extract key terms from title (simple approach)
            title_words = re.findall(r'\b[a-z]{4,}\b', article.title.lower())
            # Filter out common words
            stop_words = {'this', 'that', 'with', 'from', 'have', 'will', 'your', 'about', 'what', 'when', 'where'}
            for word in title_words:
                if word not in stop_words:
                    topics[word] += 0.5  # Lower weight for title words
        
        return topics
    
    def _count_articles_with_term(self, articles: List[SubstackArticle], term: str) -> int:
        """Count how many articles contain a specific term"""
        count = 0
        term_lower = term.lower()
        for article in articles:
            text = f"{article.title} {article.subtitle or ''} {article.preview or ''}".lower()
            if term_lower in text:
                count += 1
        return count
    
    def _identify_trending_topics(self, articles: List[SubstackArticle], topics: List[Dict]) -> List[Dict]:
        """Identify which topics are trending upward"""
        if len(articles) < 5:
            return []
        
        # Sort articles by date
        sorted_articles = sorted(articles, key=lambda a: a.published_at)
        mid_point = len(sorted_articles) // 2
        
        first_half = sorted_articles[:mid_point]
        second_half = sorted_articles[mid_point:]
        
        trending = []
        for topic in topics[:10]:  # Check top 10 topics
            term = topic['term']
            first_count = self._count_articles_with_term(first_half, term)
            second_count = self._count_articles_with_term(second_half, term)
            
            if second_count > first_count and second_count >= 2:
                trending.append({
                    'term': term,
                    'growth': second_count - first_count,
                    'current_count': second_count
                })
        
        trending.sort(key=lambda x: x['growth'], reverse=True)
        return trending[:5]
    
    def _calculate_author_productivity(self, stats: Dict, days: int) -> str:
        """Calculate author productivity level"""
        articles_per_week = (stats['articles'] / days) * 7
        
        if articles_per_week >= 3:
            return 'very_high'
        elif articles_per_week >= 2:
            return 'high'
        elif articles_per_week >= 1:
            return 'moderate'
        elif articles_per_week >= 0.5:
            return 'low'
        else:
            return 'occasional'
    
    def _generate_trend_summary(self, topics: Dict, authors: Dict, velocity: List[Dict]) -> Dict:
        """Generate a summary of the trends"""
        summary = {
            'key_insights': [],
            'recommendations': []
        }
        
        # Top topics insight
        if topics.get('top_topics'):
            top_topic = topics['top_topics'][0]['term'] if topics['top_topics'] else 'unknown'
            summary['key_insights'].append(
                f"Most discussed topic: {top_topic}"
            )
        
        # Rising topics
        rising = [t for t in velocity if t.get('trend') == 'rising']
        if rising:
            summary['key_insights'].append(
                f"{len(rising)} topics showing upward momentum"
            )
            summary['recommendations'].append(
                f"Focus on emerging topics: {', '.join([t['topic'] for t in rising[:3]])}"
            )
        
        # Author insights
        if authors.get('most_active'):
            top_author = authors['most_active'][0] if authors['most_active'] else None
            if top_author:
                summary['key_insights'].append(
                    f"Most active author: {top_author['author']} with {top_author['articles']} articles"
                )
        
        # Falling topics
        falling = [t for t in velocity if t.get('trend') == 'falling']
        if falling:
            summary['key_insights'].append(
                f"{len(falling)} topics showing declining interest"
            )
        
        return summary

def analyze_substack_trends(days: int = 7) -> Dict[str, Any]:
    """Main entry point for Substack trend analysis"""
    try:
        analyzer = SubstackTrendAnalyzer(db)
        return analyzer.analyze_trends(days)
    finally:
        db.close()