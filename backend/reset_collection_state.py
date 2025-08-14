#!/usr/bin/env python3
"""
Reset the collection state to force fresh collection
"""
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, CollectionState

def reset_state():
    db = next(get_db())
    
    print("🔄 Resetting Collection State")
    print("=" * 50)
    
    # Set last run to 2 hours ago to force collection
    two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
    
    state = db.query(CollectionState).filter(CollectionState.key == "main").first()
    
    if state:
        print(f"Current last run: {state.last_run}")
        state.last_run = two_hours_ago
        print(f"New last run: {two_hours_ago}")
    else:
        state = CollectionState(key="main", last_run=two_hours_ago)
        db.add(state)
        print(f"Created new state with last run: {two_hours_ago}")
    
    db.commit()
    db.close()
    
    print("\n✅ Collection state reset!")
    print("   Next server start will collect tweets from the last 2 hours")

if __name__ == "__main__":
    reset_state()