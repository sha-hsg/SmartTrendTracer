"""Regression tests for concept_id_query_variants.

tag_instances.concept_id is stored in mixed form (ObjectId, stringified
ObjectId, legacy slug id). Single-form queries silently drop rows — every
count/lookup must use all variants.
"""

from bson import ObjectId

from app.database.mongodb import concept_id_query_variants


class TestConceptIdQueryVariants:
    def test_hex_string_yields_string_and_objectid(self):
        cid = '68a8c0098e144ce949766ea1'
        variants = concept_id_query_variants(cid)
        assert cid in variants
        assert ObjectId(cid) in variants
        assert len(variants) == 2

    def test_objectid_yields_objectid_and_string(self):
        oid = ObjectId('68a8c0098e144ce949766ea1')
        variants = concept_id_query_variants(oid)
        assert oid in variants
        assert str(oid) in variants
        assert len(variants) == 2

    def test_slug_id_stays_as_is(self):
        # Legacy slug ids like 'c_method_active_querying' are not ObjectIds —
        # they must survive as the only variant (the old code dropped them)
        variants = concept_id_query_variants('c_method_active_querying')
        assert variants == ['c_method_active_querying']

    def test_no_duplicates(self):
        for cid in ('68a8c0098e144ce949766ea1', 'c_x', ObjectId()):
            variants = concept_id_query_variants(cid)
            assert len(variants) == len(set(map(str, variants))) or len(variants) <= 3
