#!/usr/bin/env python3
"""
Fix HTML entities in existing tweets in the database
Converts &amp; to &, &gt; to >, &lt; to <, etc.
"""

import html
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Tweet

# Create database connection
engine = create_engine('sqlite:///data/tweets.db')
Session = sessionmaker(bind=engine)
session = Session()

def fix_html_entities():
    """Fix HTML entities in all tweet texts"""
    
    # Get all tweets
    tweets = session.query(Tweet).all()
    
    fixed_count = 0
    total_count = len(tweets)
    
    print(f"Checking {total_count} tweets for HTML entities...")
    
    for tweet in tweets:
        original_text = tweet.text
        
        # Unescape HTML entities
        unescaped_text = html.unescape(original_text)
        
        # Check if anything changed
        if original_text != unescaped_text:
            # Count what entities were found
            entities_found = []
            if '&amp;' in original_text:
                entities_found.append('&amp;')
            if '&gt;' in original_text:
                entities_found.append('&gt;')
            if '&lt;' in original_text:
                entities_found.append('&lt;')
            if '&quot;' in original_text:
                entities_found.append('&quot;')
            if '&#39;' in original_text or '&apos;' in original_text:
                entities_found.append('quotes')
            
            # Update the tweet text
            tweet.text = unescaped_text
            fixed_count += 1
            
            # Show progress every 100 tweets
            if fixed_count % 100 == 0:
                print(f"  Fixed {fixed_count} tweets so far...")
            
            # Show sample of what was fixed (first 10)
            if fixed_count <= 10:
                print(f"\n  Tweet ID: {tweet.id}")
                print(f"  Author: @{tweet.author_username}")
                print(f"  Entities found: {', '.join(entities_found)}")
                print(f"  Original: {original_text[:100]}...")
                print(f"  Fixed:    {unescaped_text[:100]}...")
    
    # Commit changes
    if fixed_count > 0:
        session.commit()
        print(f"\n✅ Fixed HTML entities in {fixed_count} tweets out of {total_count}")
        
        # Show statistics
        print("\nSummary:")
        print(f"  Total tweets: {total_count}")
        print(f"  Fixed tweets: {fixed_count}")
        print(f"  Clean tweets: {total_count - fixed_count}")
        print(f"  Percentage fixed: {(fixed_count / total_count * 100):.1f}%")
    else:
        print(f"\n✅ All {total_count} tweets are already clean (no HTML entities found)")
    
    session.close()

if __name__ == "__main__":
    fix_html_entities()