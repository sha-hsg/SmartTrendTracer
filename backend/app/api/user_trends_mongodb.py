"""
MongoDB-based User Trends API
Provides per-user trend analysis for tweets
"""

from fastapi import APIRouter, Query
from app.database.mongodb import get_database
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()

@router.get("/per-user")
def get_per_user_trends(
    hours: int = Query(168, ge=1, le=720, description="Number of hours to analyze (default: 7 days)")
):
    """
    Get trend analysis broken down by user/author with real data
    Returns activity and concept usage per Twitter account
    """
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(hours=hours)
    
    # Get tweets in the time period
    tweets = list(db.tweets.find({'created_at': {'$gte': start_date, '$lte': end_date}}).limit(5000))

    # Batch-fetch all tag_instances for these tweets (fixes N+1)
    all_tweet_ids = [tweet['_id'] for tweet in tweets]
    all_tag_instances = list(db.tag_instances.find({
        'content_type': 'tweet',
        'content_id': {'$in': all_tweet_ids}
    }).limit(50000))

    # Group tag instances by content_id
    tag_instances_by_tweet = {}
    for ti in all_tag_instances:
        cid = ti['content_id']
        if cid not in tag_instances_by_tweet:
            tag_instances_by_tweet[cid] = []
        tag_instances_by_tweet[cid].append(ti)

    # Group by author
    user_data = {}
    for tweet in tweets:
        username = tweet.get('author_username')
        if not username:
            continue

        if username not in user_data:
            user_data[username] = {
                'tweets': [],
                'concepts': set(),
                'total_likes': 0,
                'total_retweets': 0,
                'timeline': {}
            }

        user_data[username]['tweets'].append(tweet)

        # Add engagement metrics
        metrics = tweet.get('metrics', {})
        user_data[username]['total_likes'] += metrics.get('like_count', 0)
        user_data[username]['total_retweets'] += metrics.get('retweet_count', 0)

        # Track timeline
        hour_key = tweet['created_at'].strftime('%Y-%m-%d %H:00')
        if hour_key not in user_data[username]['timeline']:
            user_data[username]['timeline'][hour_key] = 0
        user_data[username]['timeline'][hour_key] += 1

        # Get concepts for this tweet from pre-fetched data
        for instance in tag_instances_by_tweet.get(tweet['_id'], []):
            if instance.get('concept_id'):
                user_data[username]['concepts'].add(str(instance['concept_id']))

    # Build user list with statistics
    users = []
    top_concepts_by_user = {}
    activity_by_user = {}

    for username, data in user_data.items():
        # Get concept names and counts from pre-fetched data
        concept_counts = {}
        for tweet in data['tweets']:
            for instance in tag_instances_by_tweet.get(tweet['_id'], []):
                concept_id = instance.get('concept_id')
                if concept_id:
                    concept_id_str = str(concept_id)
                    if concept_id_str not in concept_counts:
                        concept_counts[concept_id_str] = 0
                    concept_counts[concept_id_str] += 1
        
        # Get top concepts for this user
        top_concepts = []
        for concept_id, count in sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            # Convert string ID back to ObjectId for query
            try:
                concept_obj_id = ObjectId(concept_id)
                concept = db.tag_concepts_v2.find_one({'_id': concept_obj_id})
                if concept:
                    top_concepts.append({
                        'name': concept.get('display_name', concept.get('name', '')),
                        'count': count
                    })
            except Exception:
                pass
        
        top_concepts_by_user[username] = top_concepts
        
        # Calculate activity pattern
        activity_by_user[username] = {
            'total_tweets': len(data['tweets']),
            'engagement_rate': round((data['total_likes'] + data['total_retweets']) / max(len(data['tweets']), 1), 1),
            'unique_concepts': len(data['concepts'])
        }
        
        users.append({
            'username': username,
            'tweet_count': len(data['tweets']),
            'unique_concepts': len(data['concepts']),
            'total_likes': data['total_likes'],
            'total_retweets': data['total_retweets'],
            'engagement_rate': activity_by_user[username]['engagement_rate'],
            'top_concepts': top_concepts[:3]
        })
    
    # Sort users by activity
    users.sort(key=lambda x: x['tweet_count'], reverse=True)
    
    # Find cross-user concepts (concepts used by multiple users)
    concept_user_map = {}
    for username, data in user_data.items():
        for concept_id in data['concepts']:
            if concept_id not in concept_user_map:
                concept_user_map[concept_id] = set()
            concept_user_map[concept_id].add(username)
    
    cross_user_concepts = []
    for concept_id, usernames in concept_user_map.items():
        if len(usernames) > 1:
            try:
                concept_obj_id = ObjectId(concept_id)
                concept = db.tag_concepts_v2.find_one({'_id': concept_obj_id})
                if concept:
                    cross_user_concepts.append({
                        'concept': concept.get('display_name', concept.get('name', '')),
                        'user_count': len(usernames),
                        'users': list(usernames)[:5]
                    })
            except Exception:
                pass
    
    cross_user_concepts.sort(key=lambda x: x['user_count'], reverse=True)
    
    # Determine statistics
    most_active = users[0] if users else None
    most_diverse = max(users, key=lambda x: x['unique_concepts']) if users else None
    highest_engagement = max(users, key=lambda x: x['engagement_rate']) if users else None
    
    # Build timeline
    timeline = []
    all_hours = set()
    for data in user_data.values():
        all_hours.update(data['timeline'].keys())
    
    for hour in sorted(all_hours):
        hour_data = {
            'time': hour,
            'users': {}
        }
        for username, data in user_data.items():
            if hour in data['timeline']:
                hour_data['users'][username] = data['timeline'][hour]
        timeline.append(hour_data)
    
    return {
        "period_hours": hours,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "users": users[:20],  # Top 20 users
        "top_concepts_by_user": dict(list(top_concepts_by_user.items())[:10]),
        "activity_by_user": dict(list(activity_by_user.items())[:10]),
        "cross_user_concepts": cross_user_concepts[:10],
        "user_statistics": {
            "most_active": {
                "username": most_active['username'],
                "tweet_count": most_active['tweet_count']
            } if most_active else None,
            "most_diverse_concepts": {
                "username": most_diverse['username'],
                "unique_concepts": most_diverse['unique_concepts']
            } if most_diverse else None,
            "highest_engagement": {
                "username": highest_engagement['username'],
                "engagement_rate": highest_engagement['engagement_rate']
            } if highest_engagement else None
        },
        "timeline": timeline[:100]  # Limit timeline data
    }

@router.get("/user/{username}")
def get_user_trends(
    username: str,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze")
):
    """
    Get detailed trend analysis for a specific user
    """
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Get user's tweets in the period
    tweets = list(db.tweets.find({
        'author_username': username,
        'created_at': {'$gte': start_date, '$lte': end_date}
    }).sort('created_at', -1).limit(5000))

    # Batch-fetch all tag_instances for these tweets (fixes N+1)
    user_tweet_ids = [tweet['_id'] for tweet in tweets]
    user_tag_instances = list(db.tag_instances.find({
        'content_type': 'tweet',
        'content_id': {'$in': user_tweet_ids}
    }).limit(50000))

    # Group tag instances by content_id
    user_ti_by_tweet = {}
    for ti in user_tag_instances:
        cid = ti['content_id']
        if cid not in user_ti_by_tweet:
            user_ti_by_tweet[cid] = []
        user_ti_by_tweet[cid].append(ti)

    # Get concepts used
    concept_counts = {}
    concepts_used = []
    for tweet in tweets:
        for instance in user_ti_by_tweet.get(tweet['_id'], []):
            concept_id = instance.get('concept_id')
            if concept_id:
                concept_id_str = str(concept_id)
                if concept_id_str not in concept_counts:
                    concept_counts[concept_id_str] = 0
                concept_counts[concept_id_str] += 1
                if concept_id_str not in concepts_used:
                    concepts_used.append(concept_id_str)
    
    # Get top concepts with names
    top_concepts = []
    for concept_id, count in sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        try:
            concept_obj_id = ObjectId(concept_id)
            concept = db.tag_concepts_v2.find_one({'_id': concept_obj_id})
            if concept:
                top_concepts.append({
                    'concept': concept.get('display_name', concept.get('name', '')),
                    'count': count
                })
        except Exception:
            pass
    
    # Calculate posting patterns
    by_hour = {}
    by_day = {}
    for tweet in tweets:
        hour = tweet['created_at'].hour
        day = tweet['created_at'].strftime('%A')
        
        if hour not in by_hour:
            by_hour[hour] = 0
        by_hour[hour] += 1
        
        if day not in by_day:
            by_day[day] = 0
        by_day[day] += 1
    
    # Find peak times
    peak_times = []
    if by_hour:
        sorted_hours = sorted(by_hour.items(), key=lambda x: x[1], reverse=True)[:3]
        for hour, count in sorted_hours:
            peak_times.append(f"{hour:02d}:00 ({count} tweets)")
    
    # Calculate engagement metrics
    total_likes = sum(tweet.get('metrics', {}).get('like_count', 0) for tweet in tweets)
    total_retweets = sum(tweet.get('metrics', {}).get('retweet_count', 0) for tweet in tweets)
    
    avg_likes = total_likes / len(tweets) if tweets else 0
    avg_retweets = total_retweets / len(tweets) if tweets else 0
    total_reach = total_likes + total_retweets
    
    # Track concept evolution over time
    concept_evolution = []
    if tweets:
        # Group tweets by week
        weeks = {}
        for tweet in tweets:
            week = tweet['created_at'].strftime('%Y-W%U')
            if week not in weeks:
                weeks[week] = []
            weeks[week].append(tweet)
        
        # Get top concepts per week
        # First pass: collect all concept IDs from all weeks
        all_week_concept_ids = set()
        weeks_data = {}
        for week in sorted(weeks.keys())[-4:]:  # Last 4 weeks
            week_concepts = {}
            for tweet in weeks[week]:
                for instance in user_ti_by_tweet.get(tweet['_id'], []):
                    concept_id = instance.get('concept_id')
                    if concept_id:
                        concept_id_str = str(concept_id)
                        if concept_id_str not in week_concepts:
                            week_concepts[concept_id_str] = 0
                        week_concepts[concept_id_str] += 1
                        all_week_concept_ids.add(concept_id_str)
            weeks_data[week] = week_concepts

        # Batch-fetch all concept names (fixes ObjectId mismatch + N+1)
        week_concept_obj_ids = []
        for cid in all_week_concept_ids:
            try:
                week_concept_obj_ids.append(ObjectId(cid))
            except Exception:
                pass
        week_concept_map = {str(c['_id']): c for c in db.tag_concepts_v2.find({'_id': {'$in': week_concept_obj_ids}})}

        for week in sorted(weeks_data.keys()):
            week_concepts = weeks_data[week]
            top_week_concepts = []
            for cid, count in sorted(week_concepts.items(), key=lambda x: x[1], reverse=True)[:3]:
                concept = week_concept_map.get(cid)
                if concept:
                    top_week_concepts.append(concept.get('display_name'))

            if top_week_concepts:
                concept_evolution.append({
                    'week': week,
                    'concepts': top_week_concepts
                })
    
    # Find similar users (users who use similar concepts)
    similar_users = []
    if concepts_used:
        # Batch-fetch tag_instances for top 10 concepts (fixes N+1)
        top_concept_ids_for_sim = concepts_used[:10]
        # Convert to ObjectId for query since concept_id is stored as ObjectId
        sim_concept_obj_ids = []
        for cid in top_concept_ids_for_sim:
            try:
                sim_concept_obj_ids.append(ObjectId(cid))
            except Exception:
                pass

        sim_instances = list(db.tag_instances.find({
            'content_type': 'tweet',
            'concept_id': {'$in': sim_concept_obj_ids}
        }).limit(1000))

        # Batch-fetch all referenced tweets
        sim_content_ids = list(set(inst['content_id'] for inst in sim_instances))
        sim_tweets_map = {}
        if sim_content_ids:
            # Try both ObjectId and string content_ids
            oid_ids = []
            for cid in sim_content_ids:
                if isinstance(cid, ObjectId):
                    oid_ids.append(cid)
                elif isinstance(cid, str):
                    try:
                        oid_ids.append(ObjectId(cid))
                    except Exception:
                        pass

            for tweet in db.tweets.find({'_id': {'$in': oid_ids}}).limit(1000):
                sim_tweets_map[tweet['_id']] = tweet
                sim_tweets_map[str(tweet['_id'])] = tweet

        user_similarity = {}
        for instance in sim_instances:
            tweet = sim_tweets_map.get(instance['content_id']) or sim_tweets_map.get(str(instance['content_id']))
            if tweet and tweet.get('author_username') != username:
                other_user = tweet['author_username']
                if other_user not in user_similarity:
                    user_similarity[other_user] = 0
                user_similarity[other_user] += 1

        # Get top 5 similar users
        for user, score in sorted(user_similarity.items(), key=lambda x: x[1], reverse=True)[:5]:
            similar_users.append({
                'username': user,
                'similarity_score': score
            })
    
    return {
        "username": username,
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "tweet_count": len(tweets),
        "concepts_used": concepts_used[:20],  # Top 20 concept IDs
        "top_concepts": top_concepts,
        "posting_patterns": {
            "by_hour": [{'hour': h, 'count': c} for h, c in sorted(by_hour.items())],
            "by_day": [{'day': d, 'count': c} for d, c in by_day.items()],
            "peak_times": peak_times
        },
        "engagement_metrics": {
            "avg_retweets": round(avg_retweets, 2),
            "avg_likes": round(avg_likes, 2),
            "total_reach": total_reach
        },
        "concept_evolution": concept_evolution,
        "similar_users": similar_users
    }
