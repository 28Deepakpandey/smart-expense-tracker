"""Shared pytest fixtures for the expense tracker test suite."""
import pytest
from fastapi.testclient import TestClient

from src import storage
from src.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Provide a TestClient backed by a fresh, temporary JSON file per test.

    Each test gets its own isolated file (via monkeypatch on
    `storage.DATA_FILE`) so tests never share state or leak into each
    other, and never touch the real expenses_data.json used when
    running the server locally. `tmp_path` is a pytest built-in fixture
    that gives each test its own throwaway directory, cleaned up
    automatically.
    """
    test_data_file = tmp_path / "expenses_data.json"
    monkeypatch.setattr(storage, "DATA_FILE", test_data_file)
    return TestClient(app)
