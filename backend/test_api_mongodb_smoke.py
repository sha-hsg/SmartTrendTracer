"""Smoke tests for Mongo-backed FastAPI routers using dependency overrides."""

import json
from typing import Any, Dict
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from fastapi import FastAPI
from bson import ObjectId

from types import SimpleNamespace

from app.api import tweets_mongodb, papers_mongodb, books_mongodb
from app.database import mongodb


class DummyCollection:
    def __init__(self, documents):
        self._documents = list(documents)

    def _matches(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        if not query:
            return True
        for key, value in query.items():
            if key == 'content_type':
                if doc.get('content_type') != value:
                    return False
            elif key == 'content_id':
                if isinstance(value, dict) and '$in' in value:
                    if doc.get('content_id') not in value['$in']:
                        return False
                elif doc.get('content_id') != value:
                    return False
            elif key == '_id':
                if isinstance(value, dict) and '$in' in value:
                    if doc.get('_id') not in value['$in']:
                        return False
                elif doc.get('_id') != value:
                    return False
            elif key == 'id':
                if isinstance(value, dict) and '$in' in value:
                    if doc.get('id') not in value['$in']:
                        return False
                elif doc.get('id') != value:
                    return False
            elif key == '$or':
                if not any(self._matches(doc, sub) for sub in value):
                    return False
            else:
                continue
        return True

    def find(self, query=None, *_args, **_kwargs):
        query = query or {}
        docs = [doc for doc in self._documents if self._matches(doc, query)]
        return DummyCursor(docs)

    def find_one(self, query=None, *_args, **_kwargs):
        matches = list(self.find(query))
        return matches[0] if matches else None

    def count_documents(self, query=None, *_args, **_kwargs):
        query = query or {}
        return len([doc for doc in self._documents if self._matches(doc, query)])

    def aggregate(self, *_args, **_kwargs):
        return []

    def distinct(self, field, *_args, **_kwargs):  # pragma: no cover
        values = set()
        for doc in self._documents:
            if field in doc:
                val = doc[field]
                if isinstance(val, list):
                    values.update(val)
                else:
                    values.add(val)
        return list(values)


class DummyCursor:
    def __init__(self, documents):
        self._docs = list(documents)

    def sort(self, *_, **__):
        return self

    def skip(self, *_):
        return self

    def limit(self, *_):
        return self

    def __iter__(self):
        return iter(self._docs)


class DummyDB(dict):
    def __getattr__(self, item):
        return self[item]


@pytest.fixture(autouse=True)
def override_database(monkeypatch):
    paper_id = ObjectId()
    book_id = ObjectId()
    concept_id = ObjectId()

    dummy_db = DummyDB(
        tweets=DummyCollection([
            {
                "_id": "t1",
                "id": "t1",
                "text": "Test tweet",
                "author_username": "tester",
                "created_at": datetime(2025, 9, 20, tzinfo=timezone.utc),
                "tags": [],
                "referenced_tweets": [],
            }
        ]),
        papers=DummyCollection([
            {
                "_id": paper_id,
                "title": "Test paper",
                "authors": ["Author"],
                "created_at": None,
                "processed": False,
            }
        ]),
        books=DummyCollection([
            {
                "_id": book_id,
                "title": "Test book",
                "uploaded_at": datetime(2025, 9, 19, tzinfo=timezone.utc),
            }
        ]),
        tag_instances=DummyCollection([
            {
                "content_type": 'book',
                "content_id": str(book_id),
                "concept_id": concept_id,
            }
        ]),
        tag_concepts_v2=DummyCollection([
            {
                "_id": concept_id,
                "display_name": "Knowledge Graphs",
                "slug": "knowledge_graphs",
                "id": "c_1001",
            }
        ]),
    )

    if hasattr(mongodb.get_database, "cache_clear"):
        mongodb.get_database.cache_clear()
    if hasattr(mongodb.get_client, "cache_clear"):
        mongodb.get_client.cache_clear()

    monkeypatch.setattr(mongodb, "get_database", lambda: dummy_db)
    monkeypatch.setattr(mongodb, "get_client", lambda: None)

    # Patch modules that captured db at import time
    monkeypatch.setattr(tweets_mongodb, "db", dummy_db)
    monkeypatch.setattr(papers_mongodb, "db", dummy_db)
    monkeypatch.setattr(books_mongodb, "db", dummy_db)

    dummy_concept_service = SimpleNamespace(
        get_concept_by_id=lambda _cid: None,
        get_concepts_for_content=lambda *args, **kwargs: [],
        get_tags_for_content=lambda *args, **kwargs: [],
        add_concept_to_content=lambda *args, **kwargs: (True, "c123"),
        remove_concept_from_content=lambda *args, **kwargs: True,
        add_tag=lambda *args, **kwargs: (True, "c123"),
        get_all_concepts_with_counts=lambda *args, **kwargs: [],
        remove_all_concepts_from_content=lambda *args, **kwargs: 0,
    )

    monkeypatch.setattr(tweets_mongodb, "concept_service", dummy_concept_service)
    monkeypatch.setattr(papers_mongodb, "concept_service", dummy_concept_service)
    monkeypatch.setattr(books_mongodb, "concept_service", dummy_concept_service)

    yield

    if hasattr(mongodb.get_database, "cache_clear"):
        mongodb.get_database.cache_clear()


@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(tweets_mongodb.router, prefix="/api/tweets")
    app.include_router(papers_mongodb.router, prefix="/api/papers")
    app.include_router(books_mongodb.router, prefix="/api/books")
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


def test_tweets_list_smoke(client):
    response = client.get("/api/tweets/", params={"limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["id"] == "t1"


def test_papers_list_smoke(client):
    response = client.get("/api/papers/", params={"page": 1, "page_size": 1})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["papers"][0]["title"] == "Test paper"


def test_books_list_smoke(client):
    response = client.get("/api/books/", params={"page": 1, "page_size": 5})
    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 1
    book = payload["books"][0]
    assert book["title"] == "Test book"
    assert book["concepts"][0]["display_name"] == "Knowledge Graphs"
