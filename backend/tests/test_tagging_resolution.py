"""Regression test: get_tags_for_content must resolve ObjectId-form concept_ids.

The old code did `len(cid) == 24` on raw concept_id values; `len(ObjectId())`
raises TypeError, which was swallowed — so ~98% of tagged content returned []
(dead skip-filter in batch annotation, concepts missing from the RAG index,
false _no_concepts sentinels).

Runs against the local MongoDB; skipped when unavailable.
"""

import pytest

try:
    from app.database.mongodb import get_database
    _db = get_database()
    _db.command('ping')
    _HAS_DB = True
except Exception:
    _HAS_DB = False

pytestmark = pytest.mark.skipif(not _HAS_DB, reason="local MongoDB not available")


def test_objectid_tagged_content_resolves():
    from app.services.concept_tag.service import ConceptOnlyTagService
    svc = ConceptOnlyTagService()
    inst = svc.tag_instances.find_one({
        'content_type': 'tweet',
        'concept_id': {'$type': 'objectId'},
    })
    assert inst is not None, "fixture: DB has no ObjectId-tagged tweet"
    tags = svc.get_tags_for_content('tweet', inst['content_id'])
    assert len(tags) >= 1, "ObjectId concept_ids must resolve to concepts"
    assert all(t['display_name'] for t in tags)


def test_slug_tagged_content_resolves():
    from app.services.concept_tag.service import ConceptOnlyTagService
    svc = ConceptOnlyTagService()
    inst = svc.tag_instances.find_one({
        'content_type': {'$in': ['tweet', 'article', 'paper']},
        'concept_id': {'$type': 'string'},
    })
    if inst is None:
        pytest.skip("no slug-form tag instances in DB")
    tags = svc.get_tags_for_content(inst['content_type'], inst['content_id'])
    assert len(tags) >= 1, "legacy slug concept_ids must resolve to concepts"
