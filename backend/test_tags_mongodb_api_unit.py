"""Unit tests for MongoDB-backed tag API helpers."""

import io
import types

import pytest

from app.api import tags_mongodb


class _DummyTweetsCollection:
    """Simple stand-in for the tweets collection used in tests."""

    def __init__(self, documents=None):
        self._documents = documents or {}

    def find_one(self, query):
        return self._documents.get(query.get("id"))


class _VectorStoreStub:
    def __init__(self):
        self.updates = []

    def update_tag_incrementally(self, tag, source, context):
        self.updates.append((tag, source, context))


def test_add_tag_uses_concept_service(monkeypatch):
    """Ensure add_tag cooperates with ConceptOnlyTagService and returns concept data."""

    fake_tweets = _DummyTweetsCollection({"tweet123": {"id": "tweet123", "text": "Some tweet"}})
    monkeypatch.setattr(tags_mongodb, "db", types.SimpleNamespace(tweets=fake_tweets))

    class ConceptServiceStub:
        def __init__(self):
            self.calls = []

        def add_concept_to_content(self, **kwargs):
            self.calls.append(kwargs)
            return True, "507f191e810c19729de860ea"

        def get_concept_by_id(self, concept_id):
            return {"display_name": "AI", "slug": "ai"}

    concept_stub = ConceptServiceStub()
    monkeypatch.setattr(tags_mongodb, "concept_service", concept_stub)

    vector_store_stub = _VectorStoreStub()
    monkeypatch.setattr(tags_mongodb, "get_vector_store", lambda: vector_store_stub)

    payload = tags_mongodb.TagCreate(tag="AI", tag_type="manual", confidence=0.9)
    response = tags_mongodb.add_tag("tweet123", payload)

    assert response["concept_id"] == "507f191e810c19729de860ea"
    assert response["concept"]["display_name"] == "AI"
    assert concept_stub.calls == [
        {
            "content_type": "tweet",
            "content_id": "tweet123",
            "concept_name": "AI",
            "preserve_display_name": True,
        }
    ]
    assert vector_store_stub.updates[0][0] == "ai"


def test_remove_tag_delegates_to_concept_service(monkeypatch):
    """Deleting a tag should resolve through the concept service by name."""

    class ConceptServiceStub:
        def __init__(self):
            self.removals = []

        def remove_concept_from_content(self, **kwargs):
            self.removals.append(kwargs)
            return True

    concept_stub = ConceptServiceStub()
    monkeypatch.setattr(tags_mongodb, "concept_service", concept_stub)

    response = tags_mongodb.remove_tag("tweet123", "AI")

    assert response == {"message": "Tag removed successfully"}
    assert concept_stub.removals == [
        {
            "content_type": "tweet",
            "content_id": "tweet123",
            "concept_name": "AI",
        }
    ]


def test_suggest_tags_handles_display_only_concepts(monkeypatch):
    """Existing concepts lacking legacy keys should not crash suggestions."""

    fake_tweets = _DummyTweetsCollection({"tweet42": {"id": "tweet42", "text": "Testing tweet"}})
    monkeypatch.setattr(tags_mongodb, "db", types.SimpleNamespace(tweets=fake_tweets))

    class ConceptServiceStub:
        def get_tags_for_content(self, content_type, content_id):  # noqa: D401 - interface stub
            return [{"display_name": "AI", "concept_id": "507f191e810c19729de860ea"}]

    monkeypatch.setattr(tags_mongodb, "concept_service", ConceptServiceStub())

    class VectorStoreStub:
        def search_similar_tags(self, **_):
            return []

        def update_tag_incrementally(self, *_args, **_kwargs):  # pragma: no cover - not used here
            pass

    vector_store_stub_factory = lambda: VectorStoreStub()
    monkeypatch.setattr(tags_mongodb, "get_vector_store", vector_store_stub_factory)

    from app.services import vector_store_mongodb as vector_store_module

    monkeypatch.setattr(vector_store_module, "get_vector_store", vector_store_stub_factory)

    class LLMStub:
        def suggest_tags(self, **_):
            return []

    monkeypatch.setattr(tags_mongodb, "get_llm_service", lambda: LLMStub())

    # Provide deterministic llm.json content without touching disk
    monkeypatch.setattr(
        tags_mongodb,
        "open",
        lambda *_, **__: io.StringIO('{"models": {"tag_suggestion": {"model": "stub-model"}}}'),
        raising=False,
    )

    result = tags_mongodb.suggest_tags_for_tweet("tweet42")

    assert result["already_tagged"] == ["AI"]
    assert result["total_suggestions"] == 0
