"""Tests for the MongoDB configuration helpers."""

import os
from types import SimpleNamespace

import pytest

from app.database import mongodb


@pytest.fixture(autouse=True)
def reset_mongo_helpers():
    """Clear cached Mongo settings/clients before and after each test."""
    mongodb.get_client.cache_clear()
    mongodb.get_settings.cache_clear()
    yield
    mongodb.get_client.cache_clear()
    mongodb.get_settings.cache_clear()


def test_get_settings_reads_environment(monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "mongodb://example:27018/?retryWrites=true")
    monkeypatch.setenv("MONGODB_DB", "analytics")
    monkeypatch.setenv("MONGODB_REPLICA_SET", "rs0")
    monkeypatch.setenv("MONGODB_APP_NAME", "smarttrendtracer-tests")
    monkeypatch.setenv("MONGODB_OPTIONS", "tls=true, retryWrites=false")

    settings = mongodb.get_settings()

    assert settings.uri == "mongodb://example:27018/?retryWrites=true"
    assert settings.database == "analytics"
    assert settings.replica_set == "rs0"
    assert settings.app_name == "smarttrendtracer-tests"
    assert settings.options == {"tls": "true", "retryWrites": "false"}


def test_get_client_is_cached(monkeypatch):
    calls = []

    class DummyAdmin:
        def __init__(self):
            self.commands = []

        def command(self, name):
            self.commands.append(name)

    class DummyClient:
        def __init__(self, uri, **kwargs):
            calls.append((uri, kwargs))
            self.admin = DummyAdmin()

        def __getitem__(self, name):
            return {"_db_name": name}

    monkeypatch.setattr(mongodb, "MongoClient", DummyClient)

    client1 = mongodb.get_client()
    client2 = mongodb.get_client()

    assert client1 is client2
    assert len(calls) == 1
    assert calls[0][0] == os.getenv("MONGODB_URI", "mongodb://localhost:27017/")


def test_get_database_uses_shared_client(monkeypatch):
    class DummyClient:
        instances = 0

        def __init__(self, uri, **kwargs):
            DummyClient.instances += 1
            self._uri = uri

        def __getitem__(self, name):
            return SimpleNamespace(name=name, uri=self._uri)

    monkeypatch.setattr(mongodb, "MongoClient", DummyClient)

    db1 = mongodb.get_database()
    db2 = mongodb.get_database()

    assert db1.name == os.getenv("MONGODB_DB", "smarttrendtracer")
    assert db2.name == db1.name
    assert DummyClient.instances == 1
