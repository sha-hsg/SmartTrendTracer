"""API document serializers."""


def serialize_account(account: dict) -> dict:
    """Serialize MongoDB account document to response format."""
    return {
        'id': str(account['_id']),
        'twitter_id': account.get('twitter_id', ''),
        'username': account.get('username', ''),
        'display_name': account.get('display_name', account.get('username', '')),
        'category': account.get('category', 'Other'),
        'description': account.get('description'),
        'tier': account.get('tier', 2),
        'enabled': account.get('enabled', True),
        'created_at': account.get('created_at'),
        'updated_at': account.get('updated_at'),
        'profile_image_url': account.get('profile_image_url'),
        'followers_count': account.get('followers_count'),
        'verified': account.get('verified'),
        'last_collected_at': account.get('last_collected_at'),
        'tweets_collected': account.get('tweets_collected', 0)
    }
