"""Regression tests for the concept search text scoring.

Covers the 2026-08 fixes: alias matching, and the usage boost no longer
rescuing concepts with zero textual relevance (previously any concept with
>=110 usages appeared for every query).
"""

from app.api.concepts_suggestions_mongodb import _score_concept_text


def score(query, name, slug='', description='', aliases=None):
    q = query.lower()
    return _score_concept_text(q, q.split(), name, slug or name.lower().replace(' ', '_'),
                               description, aliases or [])


class TestScoring:
    def test_exact_match_is_max(self):
        assert score('transformers', 'Transformers') == 100

    def test_alias_exact_match(self):
        # "LLM" must find "Large Language Model" via its alias
        s = score('llm', 'Large Language Model', aliases=['LLM'])
        assert s == 95

    def test_alias_beats_plain_word_match(self):
        alias_hit = score('llm', 'Large Language Model', aliases=['LLM'])
        word_hit = score('language', 'Large Language Model')
        assert alias_hit > word_hit

    def test_substring_match(self):
        assert score('transform', 'Transformers') == 80

    def test_no_match_is_zero(self):
        # Regression: with the old code a popular concept (usage >= 110)
        # scored 0 + boost 20 > threshold 10 and leaked into every result
        assert score('quantum chemistry', 'Transformers') == 0

    def test_word_match_fraction(self):
        # one of two query words matches -> 30
        assert score('attention pancakes', 'Attention Mechanisms') == 30

    def test_exact_beats_alias_beats_substring(self):
        exact = score('rag', 'RAG')
        alias = score('rag', 'Retrieval Augmented Generation', aliases=['RAG'])
        substr = score('rag', 'RAG Pipelines')
        assert exact > alias > substr

    def test_description_only_word_match(self):
        s = score('retrieval', 'RAG', description='Retrieval augmented generation')
        assert s == 60

    def test_empty_query_words(self):
        assert _score_concept_text('', [], 'X', 'x', '', []) == 0
