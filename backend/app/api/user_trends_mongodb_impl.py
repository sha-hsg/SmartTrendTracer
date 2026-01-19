"""
Full implementation for user trends endpoints
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.database.mongodb import get_database
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# MongoDB connection
db = get_database()

def compare_user_trends_impl(users: List[str], days: int) -> Dict[str, Any]:
    """
    Compare trends between multiple users with real data
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    user_data = {}
    all_concepts = set()
    
    # Gather data for each user
    for username in users:
        tweets = list(db.tweets.find({
            'author_username': username,
            'created_at': {'$gte': start_date, '$lte': end_date}
        }))
        
        # Get concepts for this user
        user_concepts = set()
        for tweet in tweets:
            instances = db.tag_instances.find({
                'content_type': 'tweet',
                'content_id': str(tweet['_id'])
            })
            for instance in instances:
                concept_id = instance.get('concept_id')
                if concept_id:
                    user_concepts.add(str(concept_id))
                    all_concepts.add(str(concept_id))
        
        user_data[username] = {
            'tweets': tweets,
            'concepts': user_concepts,
            'tweet_count': len(tweets),
            'concept_count': len(user_concepts)
        }
    
    # Find common concepts
    common_concepts = None
    for username, data in user_data.items():
        if common_concepts is None:
            common_concepts = data['concepts'].copy()
        else:
            common_concepts = common_concepts.intersection(data['concepts'])
    
    # Get concept names for common concepts
    common_concept_names = []
    for concept_id in common_concepts or []:
        concept = db.tag_concepts_v2.find_one({'_id': concept_id})
        if concept:
            common_concept_names.append(concept.get('display_name'))
    
    # Find unique concepts per user
    unique_concepts_by_user = {}
    for username, data in user_data.items():
        unique = data['concepts'].copy()
        for other_user, other_data in user_data.items():
            if other_user != username:
                unique = unique - other_data['concepts']
        
        # Get concept names
        unique_names = []
        for concept_id in list(unique)[:10]:
            concept = db.tag_concepts_v2.find_one({'_id': concept_id})
            if concept:
                unique_names.append(concept.get('display_name'))
        unique_concepts_by_user[username] = unique_names
    
    # Activity comparison
    activity_comparison = {}
    posting_frequency = {}
    concept_diversity = {}
    
    for username, data in user_data.items():
        activity_comparison[username] = {
            'total_tweets': data['tweet_count'],
            'avg_daily': round(data['tweet_count'] / days, 2),
            'total_likes': sum(t.get('metrics', {}).get('like_count', 0) for t in data['tweets']),
            'total_retweets': sum(t.get('metrics', {}).get('retweet_count', 0) for t in data['tweets'])
        }
        
        # Calculate posting frequency
        if data['tweets']:
            hours = [t['created_at'].hour for t in data['tweets']]
            posting_frequency[username] = {
                'most_active_hour': max(set(hours), key=hours.count) if hours else None,
                'tweets_per_day': round(data['tweet_count'] / days, 2)
            }
        
        concept_diversity[username] = {
            'unique_concepts': data['concept_count'],
            'concepts_per_tweet': round(data['concept_count'] / max(data['tweet_count'], 1), 2)
        }
    
    # Find most similar and different pairs
    similarity_scores = {}
    for i, user1 in enumerate(users):
        for user2 in users[i+1:]:
            shared = len(user_data[user1]['concepts'].intersection(user_data[user2]['concepts']))
            total = len(user_data[user1]['concepts'].union(user_data[user2]['concepts']))
            similarity = shared / total if total > 0 else 0
            similarity_scores[f"{user1}-{user2}"] = similarity
    
    most_similar_pair = max(similarity_scores.items(), key=lambda x: x[1]) if similarity_scores else None
    most_different_pair = min(similarity_scores.items(), key=lambda x: x[1]) if similarity_scores else None
    
    # Identify concept leaders (users who use concepts first)
    concept_leaders = []
    trend_followers = []
    
    # Sort users by average tweet time
    user_avg_times = {}
    for username, data in user_data.items():
        if data['tweets']:
            avg_timestamp = sum(t['created_at'].timestamp() for t in data['tweets']) / len(data['tweets'])
            user_avg_times[username] = avg_timestamp
    
    if user_avg_times:
        sorted_users = sorted(user_avg_times.items(), key=lambda x: x[1])
        if sorted_users:
            concept_leaders = [sorted_users[0][0]]  # Earliest poster
            trend_followers = [sorted_users[-1][0]] if len(sorted_users) > 1 else []
    
    return {
        "users": users,
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "comparison": {
            "common_concepts": common_concept_names[:10],
            "unique_concepts_by_user": unique_concepts_by_user,
            "activity_comparison": activity_comparison,
            "posting_frequency": posting_frequency,
            "concept_diversity": concept_diversity
        },
        "insights": {
            "most_similar_pair": {
                "users": most_similar_pair[0].split('-'),
                "similarity": round(most_similar_pair[1], 3)
            } if most_similar_pair else None,
            "most_different_pair": {
                "users": most_different_pair[0].split('-'),
                "similarity": round(most_different_pair[1], 3)
            } if most_different_pair else None,
            "concept_leaders": concept_leaders,
            "trend_followers": trend_followers
        }
    }

def get_influencer_analysis_impl(days: int, min_tweets: int) -> Dict[str, Any]:
    """
    Identify influential users based on concept introduction and spread
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get all users with minimum tweet count
    pipeline = [
        {'$match': {'created_at': {'$gte': start_date, '$lte': end_date}}},
        {'$group': {
            '_id': '$author_username',
            'tweet_count': {'$sum': 1},
            'total_likes': {'$sum': '$metrics.like_count'},
            'total_retweets': {'$sum': '$metrics.retweet_count'},
            'first_tweet': {'$min': '$created_at'},
            'tweets': {'$push': {'id': '$_id', 'created_at': '$created_at'}}
        }},
        {'$match': {'tweet_count': {'$gte': min_tweets}}},
        {'$sort': {'total_likes': -1}}
    ]
    
    user_stats = list(db.tweets.aggregate(pipeline))
    
    influencers = []
    concept_introducers = {}
    
    # Track who introduced each concept first
    concept_first_use = {}
    
    for user_stat in user_stats[:20]:  # Top 20 users by engagement
        username = user_stat['_id']
        
        # Find concepts this user introduced
        introduced_concepts = []
        for tweet_data in user_stat['tweets']:
            instances = db.tag_instances.find({
                'content_type': 'tweet',
                'content_id': str(tweet_data['id'])
            })
            
            for instance in instances:
                concept_id = str(instance.get('concept_id'))
                if concept_id:
                    if concept_id not in concept_first_use:
                        concept_first_use[concept_id] = {
                            'user': username,
                            'date': tweet_data['created_at']
                        }
                        introduced_concepts.append(concept_id)
                    elif concept_first_use[concept_id]['date'] > tweet_data['created_at']:
                        # This user used it earlier
                        concept_first_use[concept_id] = {
                            'user': username,
                            'date': tweet_data['created_at']
                        }
                        introduced_concepts.append(concept_id)
        
        # Calculate influence score
        influence_score = (
            user_stat['total_likes'] * 0.3 +
            user_stat['total_retweets'] * 0.5 +
            len(introduced_concepts) * 10
        )
        
        influencers.append({
            'username': username,
            'influence_score': round(influence_score, 2),
            'tweet_count': user_stat['tweet_count'],
            'avg_likes': round(user_stat['total_likes'] / user_stat['tweet_count'], 2),
            'avg_retweets': round(user_stat['total_retweets'] / user_stat['tweet_count'], 2),
            'concepts_introduced': len(introduced_concepts)
        })
    
    # Sort by influence score
    influencers.sort(key=lambda x: x['influence_score'], reverse=True)
    
    # Get concept names for introducers
    for concept_id, intro_data in list(concept_first_use.items())[:10]:
        concept = db.tag_concepts_v2.find_one({'_id': concept_id})
        if concept:
            concept_name = concept.get('display_name')
            if concept_name not in concept_introducers:
                concept_introducers[concept_name] = {
                    'introduced_by': intro_data['user'],
                    'introduced_on': intro_data['date'].isoformat()
                }
    
    # Identify trend setters (users whose concepts spread)
    trend_setters = []
    for username in [i['username'] for i in influencers[:5]]:
        # Count how many other users adopted their concepts
        adopters = set()
        for concept_id, intro_data in concept_first_use.items():
            if intro_data['user'] == username:
                # Find who else used this concept
                instances = db.tag_instances.find({
                    'content_type': 'tweet',
                    'concept_id': concept_id
                }).limit(50)
                
                for instance in instances:
                    tweet = db.tweets.find_one({'_id': instance['content_id']})
                    if tweet and tweet['author_username'] != username:
                        adopters.add(tweet['author_username'])
        
        if len(adopters) > 0:
            trend_setters.append({
                'username': username,
                'concepts_spread_to': len(adopters),
                'influence_reach': len(adopters)
            })
    
    trend_setters.sort(key=lambda x: x['influence_reach'], reverse=True)
    
    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "min_tweets_threshold": min_tweets,
        "influencers": influencers[:10],
        "concept_introducers": concept_introducers,
        "trend_setters": trend_setters[:5],
        "network_analysis": {
            "total_active_users": len(user_stats),
            "avg_tweets_per_user": round(sum(u['tweet_count'] for u in user_stats) / len(user_stats), 2) if user_stats else 0,
            "most_engaged_user": influencers[0]['username'] if influencers else None
        }
    }

def get_user_activity_heatmap_impl(days: int) -> Dict[str, Any]:
    """
    Get a heatmap of user activity over time with real data
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get tweets in period
    tweets = list(db.tweets.find({
        'created_at': {'$gte': start_date, '$lte': end_date}
    }))
    
    # Build heatmap data: hour x day
    heatmap_data = {}
    for tweet in tweets:
        username = tweet.get('author_username')
        hour = tweet['created_at'].hour
        day = tweet['created_at'].strftime('%Y-%m-%d')
        
        if username not in heatmap_data:
            heatmap_data[username] = {}
        if day not in heatmap_data[username]:
            heatmap_data[username][day] = {}
        if hour not in heatmap_data[username][day]:
            heatmap_data[username][day][hour] = 0
        
        heatmap_data[username][day][hour] += 1
    
    # Convert to array format for visualization
    heatmap = []
    for username, days_data in list(heatmap_data.items())[:10]:  # Top 10 users
        for day, hours_data in days_data.items():
            for hour, count in hours_data.items():
                heatmap.append({
                    'user': username,
                    'day': day,
                    'hour': hour,
                    'value': count
                })
    
    # Find peak activity times
    hour_totals = Counter()
    day_totals = Counter()
    user_peaks = {}
    
    for tweet in tweets:
        hour = tweet['created_at'].hour
        day = tweet['created_at'].strftime('%A')
        username = tweet.get('author_username')
        
        hour_totals[hour] += 1
        day_totals[day] += 1
        
        if username not in user_peaks:
            user_peaks[username] = Counter()
        user_peaks[username][hour] += 1
    
    # Get global peak
    global_peak_hour = hour_totals.most_common(1)[0] if hour_totals else (None, 0)
    global_peak_day = day_totals.most_common(1)[0] if day_totals else (None, 0)
    
    # Get user peaks
    user_peak_times = {}
    for username, hours in list(user_peaks.items())[:10]:
        peak = hours.most_common(1)[0] if hours else (None, 0)
        if peak[0] is not None:
            user_peak_times[username] = f"{peak[0]:02d}:00 ({peak[1]} tweets)"
    
    # Activity patterns
    weekday_tweets = sum(1 for t in tweets if t['created_at'].weekday() < 5)
    weekend_tweets = len(tweets) - weekday_tweets
    
    business_hours_tweets = sum(1 for t in tweets if 9 <= t['created_at'].hour < 17)
    after_hours_tweets = len(tweets) - business_hours_tweets
    
    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "heatmap": heatmap[:500],  # Limit for performance
        "peak_activity": {
            "global_peak": {
                "hour": f"{global_peak_hour[0]:02d}:00" if global_peak_hour[0] is not None else None,
                "count": global_peak_hour[1],
                "day": global_peak_day[0],
                "day_count": global_peak_day[1]
            },
            "user_peaks": user_peak_times
        },
        "activity_patterns": {
            "weekday_vs_weekend": {
                "weekday": weekday_tweets,
                "weekend": weekend_tweets,
                "weekday_percentage": round(weekday_tweets / len(tweets) * 100, 1) if tweets else 0
            },
            "business_hours_vs_after": {
                "business_hours": business_hours_tweets,
                "after_hours": after_hours_tweets,
                "business_percentage": round(business_hours_tweets / len(tweets) * 100, 1) if tweets else 0
            },
            "total_tweets": len(tweets),
            "unique_users": len(set(t.get('author_username') for t in tweets))
        }
    }

def get_engagement_metrics_impl(days: int) -> Dict[str, Any]:
    """
    Get engagement metrics across all users with real data
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get all tweets in period
    tweets = list(db.tweets.find({
        'created_at': {'$gte': start_date, '$lte': end_date}
    }))
    
    # Calculate overall metrics
    total_tweets = len(tweets)
    total_likes = sum(t.get('metrics', {}).get('like_count', 0) for t in tweets)
    total_retweets = sum(t.get('metrics', {}).get('retweet_count', 0) for t in tweets)
    avg_engagement_rate = (total_likes + total_retweets) / total_tweets if total_tweets > 0 else 0
    
    # Get metrics by user
    by_user = {}
    for tweet in tweets:
        username = tweet.get('author_username')
        if username not in by_user:
            by_user[username] = {
                'tweets': 0,
                'likes': 0,
                'retweets': 0
            }
        by_user[username]['tweets'] += 1
        by_user[username]['likes'] += tweet.get('metrics', {}).get('like_count', 0)
        by_user[username]['retweets'] += tweet.get('metrics', {}).get('retweet_count', 0)
    
    # Calculate engagement rates per user
    user_engagement = {}
    for username, stats in by_user.items():
        engagement_rate = (stats['likes'] + stats['retweets']) / stats['tweets'] if stats['tweets'] > 0 else 0
        user_engagement[username] = {
            'tweet_count': stats['tweets'],
            'total_likes': stats['likes'],
            'total_retweets': stats['retweets'],
            'engagement_rate': round(engagement_rate, 2),
            'avg_likes': round(stats['likes'] / stats['tweets'], 2) if stats['tweets'] > 0 else 0,
            'avg_retweets': round(stats['retweets'] / stats['tweets'], 2) if stats['tweets'] > 0 else 0
        }
    
    # Get top performing tweets
    top_tweets = sorted(tweets, key=lambda t: t.get('metrics', {}).get('like_count', 0) + 
                                              t.get('metrics', {}).get('retweet_count', 0), reverse=True)[:10]
    
    top_performing_tweets = []
    for tweet in top_tweets:
        top_performing_tweets.append({
            'id': str(tweet['_id']),
            'author': tweet.get('author_username'),
            'text': tweet.get('text', '')[:100] + '...' if len(tweet.get('text', '')) > 100 else tweet.get('text', ''),
            'likes': tweet.get('metrics', {}).get('like_count', 0),
            'retweets': tweet.get('metrics', {}).get('retweet_count', 0),
            'total_engagement': tweet.get('metrics', {}).get('like_count', 0) + tweet.get('metrics', {}).get('retweet_count', 0),
            'created_at': tweet['created_at'].isoformat()
        })
    
    # Engagement trends over time
    engagement_trends = []
    tweets_by_day = {}
    for tweet in tweets:
        day = tweet['created_at'].strftime('%Y-%m-%d')
        if day not in tweets_by_day:
            tweets_by_day[day] = {
                'count': 0,
                'likes': 0,
                'retweets': 0
            }
        tweets_by_day[day]['count'] += 1
        tweets_by_day[day]['likes'] += tweet.get('metrics', {}).get('like_count', 0)
        tweets_by_day[day]['retweets'] += tweet.get('metrics', {}).get('retweet_count', 0)
    
    for day in sorted(tweets_by_day.keys()):
        stats = tweets_by_day[day]
        engagement_trends.append({
            'date': day,
            'tweets': stats['count'],
            'likes': stats['likes'],
            'retweets': stats['retweets'],
            'engagement_rate': round((stats['likes'] + stats['retweets']) / stats['count'], 2) if stats['count'] > 0 else 0
        })
    
    # Correlation analysis
    # Analyze engagement by concept
    concept_engagement = {}
    for tweet in tweets:
        engagement = tweet.get('metrics', {}).get('like_count', 0) + tweet.get('metrics', {}).get('retweet_count', 0)
        
        instances = db.tag_instances.find({
            'content_type': 'tweet',
            'content_id': str(tweet['_id'])
        })
        
        for instance in instances:
            concept_id = instance.get('concept_id')
            if concept_id:
                concept = db.tag_concepts_v2.find_one({'_id': concept_id})
                if concept:
                    concept_name = concept.get('display_name')
                    if concept_name not in concept_engagement:
                        concept_engagement[concept_name] = {
                            'total_engagement': 0,
                            'tweet_count': 0
                        }
                    concept_engagement[concept_name]['total_engagement'] += engagement
                    concept_engagement[concept_name]['tweet_count'] += 1
    
    # Calculate average engagement per concept
    for concept_name, stats in concept_engagement.items():
        stats['avg_engagement'] = round(stats['total_engagement'] / stats['tweet_count'], 2) if stats['tweet_count'] > 0 else 0
    
    # Sort by average engagement
    top_concepts_by_engagement = sorted(concept_engagement.items(), 
                                       key=lambda x: x[1]['avg_engagement'], 
                                       reverse=True)[:10]
    
    # Time-based engagement analysis
    time_engagement = {}
    for tweet in tweets:
        hour = tweet['created_at'].hour
        engagement = tweet.get('metrics', {}).get('like_count', 0) + tweet.get('metrics', {}).get('retweet_count', 0)
        
        if hour not in time_engagement:
            time_engagement[hour] = {
                'total_engagement': 0,
                'tweet_count': 0
            }
        time_engagement[hour]['total_engagement'] += engagement
        time_engagement[hour]['tweet_count'] += 1
    
    # Calculate average engagement per hour
    for hour, stats in time_engagement.items():
        stats['avg_engagement'] = round(stats['total_engagement'] / stats['tweet_count'], 2) if stats['tweet_count'] > 0 else 0
    
    # Length-based engagement (simplified - just check if long or short)
    length_engagement = {'short': {'total': 0, 'count': 0}, 'long': {'total': 0, 'count': 0}}
    for tweet in tweets:
        engagement = tweet.get('metrics', {}).get('like_count', 0) + tweet.get('metrics', {}).get('retweet_count', 0)
        text_length = len(tweet.get('text', ''))
        
        if text_length < 140:
            length_engagement['short']['total'] += engagement
            length_engagement['short']['count'] += 1
        else:
            length_engagement['long']['total'] += engagement
            length_engagement['long']['count'] += 1
    
    for category in length_engagement.values():
        category['avg_engagement'] = round(category['total'] / category['count'], 2) if category['count'] > 0 else 0
    
    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "overall_metrics": {
            "total_tweets": total_tweets,
            "total_retweets": total_retweets,
            "total_likes": total_likes,
            "avg_engagement_rate": round(avg_engagement_rate, 2)
        },
        "by_user": dict(sorted(user_engagement.items(), 
                              key=lambda x: x[1]['engagement_rate'], 
                              reverse=True)[:20]),  # Top 20 users by engagement
        "top_performing_tweets": top_performing_tweets,
        "engagement_trends": engagement_trends,
        "correlation_analysis": {
            "concept_engagement": dict(top_concepts_by_engagement),
            "time_engagement": {f"{h:02d}:00": stats for h, stats in sorted(time_engagement.items())},
            "length_engagement": length_engagement
        }
    }
