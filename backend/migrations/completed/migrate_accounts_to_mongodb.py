#!/usr/bin/env python3
"""
Migration script to move Twitter accounts from accounts.json to MongoDB.
This creates the twitter_accounts collection with proper schema and indexes.
"""
import json
import os
from datetime import datetime
from pymongo import MongoClient, ASCENDING

# Tier definitions from tweet_collector_service.py
TIER_1_ACCOUNTS = ["OpenAI", "AnthropicAI", "sama", "emollick"]
TIER_2_ACCOUNTS = ["huggingface", "GoogleDeepMind", "stanfordnlp", "hwchase17", "kaggle"]
TIER_3_ACCOUNTS = ["rasbt", "JayAlammar", "Yoavgo", "Shayneredford", "Sebastienbubeck",
                   "Langchainai", "Colm_Conf", "GH_Wiegand", "ABosselut"]


def determine_tier(username: str) -> int:
    """Determine the collection tier for an account based on username."""
    if username in TIER_1_ACCOUNTS:
        return 1
    elif username in TIER_2_ACCOUNTS:
        return 2
    else:
        return 3  # Default tier


def migrate_accounts():
    """Migrate accounts.json to MongoDB twitter_accounts collection."""
    # Get the path to accounts.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    accounts_file = os.path.join(script_dir, 'accounts.json')

    # Load accounts from JSON
    print(f"Loading accounts from {accounts_file}...")
    with open(accounts_file, 'r') as f:
        data = json.load(f)

    accounts = data.get('accounts', [])
    print(f"Found {len(accounts)} accounts in JSON file")

    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer

    # Check if collection already has data
    existing_count = db.twitter_accounts.count_documents({})
    if existing_count > 0:
        print(f"Warning: twitter_accounts collection already has {existing_count} documents")
        response = input("Do you want to drop existing data and re-migrate? (y/n): ")
        if response.lower() != 'y':
            print("Migration cancelled")
            return
        db.twitter_accounts.drop()
        print("Dropped existing collection")

    # Prepare documents for insertion
    documents = []
    now = datetime.utcnow()

    for account in accounts:
        username = account.get('username', '')
        tier = determine_tier(username)

        doc = {
            'twitter_id': account.get('id', ''),
            'username': username,
            'display_name': account.get('displayName', username),
            'category': account.get('category', 'Other'),
            'description': account.get('description', ''),
            'tier': tier,
            'enabled': True,
            'created_at': now,
            'updated_at': now,
            # Optional fields for future use
            'profile_image_url': None,
            'followers_count': None,
            'verified': None,
            'last_collected_at': None,
            'tweets_collected': 0
        }
        documents.append(doc)
        print(f"  - {username} (Tier {tier}, Category: {doc['category']})")

    # Insert all documents
    if documents:
        result = db.twitter_accounts.insert_many(documents)
        print(f"\nInserted {len(result.inserted_ids)} accounts into MongoDB")

    # Create indexes
    print("\nCreating indexes...")
    db.twitter_accounts.create_index('username', unique=True)
    db.twitter_accounts.create_index('twitter_id', unique=True)
    db.twitter_accounts.create_index('tier')
    db.twitter_accounts.create_index('enabled')
    db.twitter_accounts.create_index('category')
    db.twitter_accounts.create_index([('enabled', ASCENDING), ('tier', ASCENDING)])
    print("Indexes created successfully")

    # Verify migration
    final_count = db.twitter_accounts.count_documents({})
    print(f"\nMigration complete! {final_count} accounts now in MongoDB")

    # Show summary by tier
    print("\nAccounts by tier:")
    for tier in [1, 2, 3]:
        count = db.twitter_accounts.count_documents({'tier': tier})
        print(f"  Tier {tier}: {count} accounts")

    # Show summary by category
    print("\nAccounts by category:")
    pipeline = [
        {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    for doc in db.twitter_accounts.aggregate(pipeline):
        print(f"  {doc['_id']}: {doc['count']} accounts")


if __name__ == '__main__':
    migrate_accounts()
