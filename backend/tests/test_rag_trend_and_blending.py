"""Regression tests for RAG trend detection and result blending.

These cover the pure functions fixed in the 2026-08 functional kaizen pass:
- is_trend_query: substring false positives ('photo' -> 'hot'), curly
  apostrophes, German phrasings
- _blend_results: small-k starvation of the last content type
"""

from app.services.rag.trend_analysis import is_trend_query
from app.services.rag.search import _blend_results


class TestIsTrendQuery:
    def test_positive_english(self):
        assert is_trend_query("What are the current trends in AI?")
        assert is_trend_query("What's hot in machine learning?")
        assert is_trend_query("Show me the hot topics this week")
        assert is_trend_query("What are people talking about?")
        assert is_trend_query("most discussed papers")

    def test_positive_german(self):
        assert is_trend_query("Was sind die wichtigsten Themen?")
        assert is_trend_query("Welche Themen sind gerade angesagt?")
        assert is_trend_query("Was ist meistdiskutiert?")
        assert is_trend_query("Zeig mir aktuelle Themen")

    def test_curly_apostrophe(self):
        # U+2019 (macOS/iOS default) must match the ASCII-keyword phrases
        assert is_trend_query("What’s happening in AI?")

    def test_no_substring_false_positives(self):
        # 'hot' must not fire inside other words
        assert not is_trend_query("Which papers cover photogrammetry?")
        assert not is_trend_query("Agents for hotel booking")
        assert not is_trend_query("Explain one-shot learning")

    def test_factual_questions_stay_factual(self):
        assert not is_trend_query("How does attention work in transformers?")
        assert not is_trend_query("Summarize the Mamba paper")


def _mk(type_, i, score):
    return {'type': type_, 'id': f'{type_}-{i}', 'score': score}


def _results_by_type(n_tweets=10, n_articles=10, n_papers=10):
    return {
        'tweet': [_mk('tweet', i, 0.9 - i * 0.01) for i in range(n_tweets)],
        'article': [_mk('article', i, 0.8 - i * 0.01) for i in range(n_articles)],
        'paper': [_mk('paper', i, 0.7 - i * 0.01) for i in range(n_papers)],
        'snippet': [],
    }

TYPES = ['tweet', 'article', 'paper']


class TestBlendResults:
    def _counts(self, results):
        counts = {}
        for r in results:
            counts[r['type']] = counts.get(r['type'], 0) + 1
        return counts

    def test_small_k_no_starvation(self):
        # Old block-wise quota gave k=5 over 3 types as 3/2/0 (papers starved)
        results = _blend_results(_results_by_type(), TYPES, k=5)
        counts = self._counts(results)
        assert len(results) == 5
        assert counts['paper'] >= 1, f"papers starved: {counts}"

    def test_k3_one_each(self):
        results = _blend_results(_results_by_type(), TYPES, k=3)
        assert self._counts(results) == {'tweet': 1, 'article': 1, 'paper': 1}

    def test_k10_unchanged_from_old_behavior(self):
        # The frontend default: 3/3/3 quota + 1 pooled by score
        results = _blend_results(_results_by_type(), TYPES, k=10)
        counts = self._counts(results)
        assert len(results) == 10
        assert counts == {'tweet': 4, 'article': 3, 'paper': 3}

    def test_empty_type_slots_redistributed(self):
        results = _blend_results(_results_by_type(n_articles=0), TYPES, k=9)
        counts = self._counts(results)
        assert len(results) == 9
        assert counts.get('article', 0) == 0
        assert counts['tweet'] + counts['paper'] == 9

    def test_never_exceeds_k(self):
        for k in range(1, 15):
            assert len(_blend_results(_results_by_type(), TYPES, k=k)) == min(k, 30)

    def test_single_type_top_k(self):
        results = _blend_results(_results_by_type(), ['tweet'], k=5)
        assert len(results) == 5
        assert all(r['type'] == 'tweet' for r in results)

    def test_no_duplicates(self):
        results = _blend_results(_results_by_type(), TYPES, k=12)
        ids = [r['id'] for r in results]
        assert len(ids) == len(set(ids))
