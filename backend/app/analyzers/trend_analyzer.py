"""
Trend Analyzer for identifying hot topics and emerging trends
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple
from collections import Counter
import re

class TrendAnalyzer:
    def __init__(self, db_session: Session = None):
        """Initialize the trend analyzer"""
        
    def analyze_trends(self, hours: int = 24) -> Dict:
        """
        Analyze trends over the specified time period
        Returns dictionary with trend analysis results
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get recent tweets
        recent_tweets = self.db.query(Tweet).filter(
            Tweet.created_at >= cutoff_time
        ).all()
        
        if not recent_tweets:
            return {"error": "No tweets found in the specified time period"}
        
        # Extract hashtags, mentions, and keywords
        hashtags = []
        mentions = []
        keywords = []
        
        for tweet in recent_tweets:
            # Extract hashtags
            hashtags.extend(self._extract_hashtags(tweet.text))
            
            # Extract mentions
            mentions.extend(self._extract_mentions(tweet.text))
            
            # Extract keywords (simple approach)
            keywords.extend(self._extract_keywords(tweet.text))
        
        # Count frequencies
        hashtag_counts = Counter(hashtags)
        mention_counts = Counter(mentions)
        keyword_counts = Counter(keywords)
        
        # Calculate velocity (compare with previous period)
        velocity_data = self._calculate_velocity(hours)
        
        return {
            "period_hours": hours,
            "total_tweets": len(recent_tweets),
            "top_hashtags": hashtag_counts.most_common(10),
            "top_mentions": mention_counts.most_common(10),
            "top_keywords": keyword_counts.most_common(20),
            "trending_up": velocity_data["trending_up"],
            "trending_down": velocity_data["trending_down"],
            "new_topics": velocity_data["new_topics"]
        }
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from tweet text"""
        return re.findall(r'#\w+', text.lower())
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from tweet text"""
        return re.findall(r'@\w+', text.lower())
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from tweet text"""
        # Remove URLs, mentions, hashtags
        clean_text = re.sub(r'http\S+|@\w+|#\w+', '', text.lower())
        
        # Split into words
        words = re.findall(r'\b[a-z]{4,}\b', clean_text)
        
        # Filter out common words (simple stopword list)
        stopwords = {
            'this', 'that', 'with', 'from', 'have', 'been', 
            'will', 'what', 'when', 'where', 'which', 'while',
            'about', 'after', 'before', 'during', 'through'
        }
        
        return [w for w in words if w not in stopwords]
    
    def _calculate_velocity(self, hours: int) -> Dict:
        """
        Calculate trend velocity by comparing current period with previous
        """
        now = datetime.now(timezone.utc)
        current_start = now - timedelta(hours=hours)
        previous_start = current_start - timedelta(hours=hours)
        
        # Get hashtag counts for current period
        current_tweets = self.db.query(Tweet).filter(
            Tweet.created_at >= current_start
        ).all()
        
        current_hashtags = Counter()
        for tweet in current_tweets:
            current_hashtags.update(self._extract_hashtags(tweet.text))
        
        # Get hashtag counts for previous period
        previous_tweets = self.db.query(Tweet).filter(
            Tweet.created_at >= previous_start,
            Tweet.created_at < current_start
        ).all()
        
        previous_hashtags = Counter()
        for tweet in previous_tweets:
            previous_hashtags.update(self._extract_hashtags(tweet.text))
        
        # Calculate trends
        trending_up = []
        trending_down = []
        new_topics = []
        
        for hashtag, current_count in current_hashtags.most_common(50):
            previous_count = previous_hashtags.get(hashtag, 0)
            
            if previous_count == 0:
                # New topic
                if current_count >= 3:  # Minimum threshold
                    new_topics.append((hashtag, current_count))
            else:
                # Calculate growth rate
                growth_rate = ((current_count - previous_count) / previous_count) * 100
                
                if growth_rate > 50:
                    trending_up.append((hashtag, current_count, f"+{growth_rate:.0f}%"))
                elif growth_rate < -30:
                    trending_down.append((hashtag, current_count, f"{growth_rate:.0f}%"))
        
        return {
            "trending_up": trending_up[:10],
            "trending_down": trending_down[:10],
            "new_topics": new_topics[:10]
        }
    
    def identify_topics(self) -> int:
        """
        Identify and store topics from tweets
        Returns number of new topics identified
        """
        # Get unprocessed tweets
        unprocessed = self.db.query(Tweet).filter(
            Tweet.processed == False
        ).limit(100).all()
        
        new_topics_count = 0
        
        for tweet in unprocessed:
            # Extract topics (hashtags and significant keywords)
            hashtags = self._extract_hashtags(tweet.text)
            keywords = self._extract_keywords(tweet.text)[:5]  # Top 5 keywords
            
            all_topics = hashtags + [f"keyword:{kw}" for kw in keywords]
            
            for topic_name in all_topics:
                # Get or create topic
                topic = self.db.query(Topic).filter(
                    Topic.name == topic_name
                ).first()
                
                if not topic:
                    topic = Topic(name=topic_name)
                    self.db.add(topic)
                    new_topics_count += 1
                else:
                    topic.mention_count += 1
                    topic.last_seen = datetime.now(timezone.utc)
                
                # Link tweet to topic
                tweet_topic = TweetTopic(
                    tweet_id=tweet.id,
                    topic_id=topic.id,
                    relevance_score=1.0
                )
                self.db.merge(tweet_topic)
            
            # Mark tweet as processed
            tweet.processed = True
        
        self.db.commit()
        return new_topics_count

def main():
    """Run trend analysis"""
    analyzer = TrendAnalyzer()
    
    print("Analyzing trends...")
    results = analyzer.analyze_trends(hours=24)
    
    print(f"\n=== TREND ANALYSIS (Last 24 Hours) ===")
    print(f"Total tweets analyzed: {results['total_tweets']}")
    
    print(f"\n📈 TRENDING UP:")
    for topic, count, growth in results['trending_up'][:5]:
        print(f"  {topic}: {count} mentions ({growth})")
    
    print(f"\n📉 TRENDING DOWN:")
    for topic, count, decline in results['trending_down'][:5]:
        print(f"  {topic}: {count} mentions ({decline})")
    
    print(f"\n🆕 NEW TOPICS:")
    for topic, count in results['new_topics'][:5]:
        print(f"  {topic}: {count} mentions")
    
    print(f"\n🏷️ TOP HASHTAGS:")
    for hashtag, count in results['top_hashtags'][:5]:
        print(f"  {hashtag}: {count}")

if __name__ == "__main__":
    main()