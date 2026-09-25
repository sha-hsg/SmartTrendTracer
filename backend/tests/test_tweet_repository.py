"""The shared tweet document builder must keep the established schema."""
from datetime import datetime, timezone

from app.repositories.tweets import build_tweet_document


def test_schema_and_id_rules():
    doc = build_tweet_document(
        tweet_id=2096000856487518466, text='hello', author_id='1605',
        author_username='sama', author_name='Sam', created_at='2026-09-12T18:01:37Z',
        public_metrics={'like_count': 5}, entities={'hashtags': [{'tag': 'ai'}]},
        urls=[], referenced_tweets=None, media=[{'media_key': 'm1'}],
        collected_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
    )
    assert doc['_id'] == '2096000856487518466'          # Twitter ID *string*
    assert 'tweet_id' not in doc                          # no separate id field
    assert doc['created_at'] == datetime(2026, 9, 12, 18, 1, 37, tzinfo=timezone.utc)
    assert doc['metrics'] == {'retweet_count': 0, 'like_count': 5, 'reply_count': 0, 'quote_count': 0}
    assert doc['media_count'] == 1 and doc['referenced_tweets'] == []
    assert set(doc) == {'_id', 'text', 'author_id', 'author_username', 'author_name', 'created_at',
                        'collected_at', 'processed', 'metrics', 'hashtags', 'mentions', 'urls',
                        'referenced_tweets', 'media', 'media_count', 'concept_ids'}
