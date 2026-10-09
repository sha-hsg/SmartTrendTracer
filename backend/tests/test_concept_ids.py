"""Concepts are identified by _id only (2026-10 fitness review: the custom
"id" field was generated per process and shared by up to 91 concepts)."""
from app.repositories.concepts.lookup import ConceptLookupMixin


class FakeConcepts:
    def __init__(self):
        self.docs = []

    def find_one(self, query, *_a, **_k):
        return next((d for d in self.docs if all(d.get(k) == v for k, v in query.items())), None)

    def insert_one(self, doc):
        doc.setdefault('_id', f'oid{len(self.docs)}')
        self.docs.append(doc)

        class R:
            inserted_id = doc['_id']
        return R()

    def find(self, *_a, **_k):
        return []


class Svc(ConceptLookupMixin):
    def __init__(self):
        self.tag_concepts = FakeConcepts()
        self.tag_aliases = FakeConcepts()
        type(self)._alias_cache = None


def test_new_concepts_get_no_custom_id():
    svc = Svc()
    cid = svc.find_or_create_concept('Kimi K3')
    doc = svc.tag_concepts.docs[0]
    assert cid == 'oid0' and 'id' not in doc and doc['slug'] == 'kimi_k3'


def test_one_slug_rule_folds_accents_and_punctuation():
    from app.repositories.concepts import concept_slug
    assert concept_slug('Clément Delangue') == concept_slug('Clement Delangue') == 'clement_delangue'
    assert concept_slug('GPT-5.1') == 'gpt_5_1'
    assert concept_slug('Apple-π') == 'apple_π'          # non-accent letters are kept
    assert concept_slug('  AI   Safety!! ') == 'ai_safety'
