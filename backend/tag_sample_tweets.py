#!/usr/bin/env python3
"""
Tag sample tweets with some initial tags for testing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Tweet, Tag
from sqlalchemy import func
import random

def tag_sample_tweets():
    """Add some sample tags to tweets"""
    db = next(get_db())
    
    # Get all tweets
    tweets = db.query(Tweet).all()
    print(f"Found {len(tweets)} tweets")
    
    if not tweets:
        print("No tweets found to tag")
        return
    
    # Sample tags related to AI/ML
    sample_tags = [
        "ai", "machine-learning", "deep-learning", "neural-networks",
        "llm", "gpt", "transformers", "nlp", "computer-vision",
        "research", "paper", "model", "training", "dataset",
        "benchmark", "evaluation", "optimization", "architecture",
        "open-source", "api", "deployment", "inference", "prompt-engineering"
    ]
    
    # Check existing tags
    existing_tags = db.query(Tag.tweet_id, Tag.tag).all()
    existing_set = {(t.tweet_id, t.tag) for t in existing_tags}
    print(f"Found {len(existing_set)} existing tags")
    
    # Tag each tweet with 2-5 random tags
    new_tags = []
    for tweet in tweets:
        # Determine number of tags based on tweet content
        num_tags = random.randint(2, 5)
        
        # Select tags based on content keywords
        selected_tags = []
        tweet_lower = tweet.text.lower() if tweet.text else ""
        
        # Smart tag selection based on content
        for tag in sample_tags:
            if tag.replace("-", " ") in tweet_lower or tag in tweet_lower:
                selected_tags.append(tag)
                if len(selected_tags) >= num_tags:
                    break
        
        # If not enough content-based tags, add random ones
        while len(selected_tags) < num_tags:
            tag = random.choice(sample_tags)
            if tag not in selected_tags:
                selected_tags.append(tag)
        
        # Create tag entries
        for tag in selected_tags:
            if (tweet.id, tag) not in existing_set:
                new_tag = Tag(
                    tweet_id=tweet.id,
                    tag=tag,
                    tag_type="auto"
                )
                new_tags.append(new_tag)
                existing_set.add((tweet.id, tag))
    
    # Add all new tags
    if new_tags:
        db.bulk_save_objects(new_tags)
        db.commit()
        print(f"✅ Added {len(new_tags)} tags to tweets")
    else:
        print("No new tags to add")
    
    # Show statistics
    tag_counts = db.query(Tag.tag, func.count(Tag.id)).group_by(Tag.tag).all()
    print("\nTag distribution:")
    for tag, count in sorted(tag_counts, key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {tag}: {count} tweets")

if __name__ == "__main__":
    tag_sample_tweets()