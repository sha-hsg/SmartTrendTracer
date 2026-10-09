"""Aliases resolve when tagging (2026-10 fitness review: the lookup queried a
field `alias` that no alias document has, so every spelling variant became a
new concept)."""
from app.repositories.concepts.lookup import ConceptLookupMixin


class FakeCollection:
    def __init__(self, docs):
        self.docs = docs

    def find(self, *_a, **_k):
        return list(self.docs)

    def find_one(self, query, *_a, **_k):
        return next((d for d in self.docs if all(d.get(k) == v for k, v in query.items())), None)


class Svc(ConceptLookupMixin):
    def __init__(self, aliases, concepts=()):
        self.tag_aliases = FakeCollection(aliases)
        self.tag_concepts = FakeCollection(list(concepts))
        type(self)._alias_cache = None


def test_alias_text_matches_in_slug_form():
    svc = Svc([{'alias_text': 'AI-safety', 'concept_id': 'c1'}, {'alias_text': 'LLMs', 'concept_id': 'c2'}])
    assert svc._concept_id_for_alias(svc._normalize_to_slug('AI Safety')) == 'c1'
    assert svc._concept_id_for_alias(svc._normalize_to_slug('llms')) == 'c2'
    assert svc._concept_id_for_alias('unknown') is None


def test_find_or_create_uses_alias_instead_of_creating():
    svc = Svc([{'alias_text': 'HuggingFace', 'concept_id': 'hf'}])
    assert svc.find_or_create_concept('huggingface') == 'hf'
