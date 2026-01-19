"""Tests for tag instance backfill helpers."""

from types import SimpleNamespace

from bson import ObjectId

from backfill_tag_instances_concepts import ensure_concept, update_tag_instance


class DummyCollection:
    def __init__(self):
        self.docs = {}

    def find_one(self, query):
        if "_id" in query:
            return self.docs.get(query["_id"])
        if "slug" in query:
            slug = query["slug"]
            for doc in self.docs.values():
                if doc.get("slug") == slug:
                    return doc
        return None

    def insert_one(self, doc):
        stored = dict(doc)
        stored.setdefault("_id", ObjectId())
        self.docs[stored["_id"]] = stored
        return SimpleNamespace(inserted_id=stored["_id"])

    def update_one(self, filt, update):
        doc = self.docs.get(filt.get("_id"))
        if not doc:
            return SimpleNamespace(modified_count=0)
        if "$set" in update:
            for key, value in update["$set"].items():
                doc[key] = value
        if "$unset" in update:
            for key in update["$unset"].keys():
                doc.pop(key, None)
        return SimpleNamespace(modified_count=1)


class DummyInstanceCollection(DummyCollection):
    def add(self, doc):
        self.docs[doc["_id"]] = doc


class DummyConceptService:
    def __init__(self):
        self.tag_concepts = DummyCollection()
        self.tag_instances = DummyInstanceCollection()
        self._counter = 1000

    def _normalize_to_slug(self, text):
        return text.lower().strip().replace(" ", "_")

    def _generate_display_name(self, slug):
        return slug.replace("_", " ").title()

    def _generate_concept_id(self):
        self._counter += 1
        return f"c_{self._counter}"


def test_update_tag_instance_creates_concept_when_missing():
    service = DummyConceptService()
    instance_id = ObjectId()
    instance = {"_id": instance_id, "original_text": "Edge AI"}
    service.tag_instances.add(instance)

    changed, concept_created = update_tag_instance(service, instance)

    assert changed is True
    assert concept_created is True
    assert "concept_id" in instance
    concept = service.tag_concepts.docs[instance["concept_id"]]
    assert concept["slug"] == "edge_ai"
    assert instance["tag_text"] == "edge ai"
    assert instance["source"] == "backfill_migration"


def test_update_tag_instance_reuses_existing_concept():
    service = DummyConceptService()
    existing = service.tag_concepts.insert_one({"slug": "edge_ai", "display_name": "Edge AI"}).inserted_id

    instance_id = ObjectId()
    instance = {"_id": instance_id, "tag": "Edge AI"}
    service.tag_instances.add(instance)

    changed, concept_created = update_tag_instance(service, instance)

    assert changed is True
    assert concept_created is False
    assert instance["concept_id"] == existing
    assert "tag" not in instance  # legacy field removed


def test_ensure_concept_returns_existing(monkeypatch):
    service = DummyConceptService()
    inserted = service.tag_concepts.insert_one({
        "slug": "language_models",
        "display_name": "Language Models"
    }).inserted_id

    concept_id, created = ensure_concept(service, "Language Models")

    assert concept_id == inserted
    assert created is False
