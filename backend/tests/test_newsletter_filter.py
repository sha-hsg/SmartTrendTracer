"""Gmail newsletter allow-list and duplicate check (2026-10)."""
from datetime import datetime, timezone

from app.collectors import gmail_substack_collector as g


def test_allow_list_maps_publication_to_person_and_longest_key_wins(monkeypatch):
    monkeypatch.setattr(g, '_newsletter_sources', lambda: {
        'LLM Watch': {'author': 'Pascal Biese', 'include': True},
        'Substack': {'include': False},
        'The Substack Post': {'include': False},
        'Import AI': {'author': 'Jack Clark', 'include': True},
    })
    assert g.match_newsletter_source('LLM Watch <llmwatch@substack.com>')['author'] == 'Pascal Biese'
    assert g.match_newsletter_source('Jack Clark from Import AI <x@substack.com>')['author'] == 'Jack Clark'
    assert g.match_newsletter_source('The Substack Post <post@substack.com>')['include'] is False
    assert g.match_newsletter_source('Silver Bulletin <x@substack.com>') is None   # unknown: skipped


class FakeArticles:
    def __init__(self, docs):
        self.docs = docs

    def find(self, query, *_a):
        lo, hi = query['published_at']['$gte'], query['published_at']['$lte']
        return [d for d in self.docs if lo <= d['published_at'] <= hi]


class FakeDB:
    def __init__(self, docs):
        self.articles = FakeArticles(docs)


def test_duplicate_needs_same_title_within_three_days():
    d = datetime(2026, 10, 8, tzinfo=timezone.utc)
    db = FakeDB([{'title': 'Papers You Should Know About', 'published_at': datetime(2026, 9, 20, tzinfo=timezone.utc)},
                 {'title': 'Notes on NVIDIA Nemotron', 'published_at': datetime(2026, 10, 7, tzinfo=timezone.utc)}])
    assert g.is_duplicate_article(db, 'Notes on NVIDIA Nemotron!', d)
    assert not g.is_duplicate_article(db, 'Papers You Should Know About', d)    # recurring title, other week
