"""Test: LocalStorageService."""
import pytest
from app.storage.local import LocalStorageService


@pytest.fixture
def storage(tmp_path):
    return LocalStorageService(storage_dir=str(tmp_path))


def test_save_and_get(storage):
    data = b"hello world resume content"
    stored = storage.save(data, "resume.txt")
    assert stored.size == len(data)
    assert len(stored.hash) == 64  # sha256 hex

    retrieved = storage.get(stored.path)
    assert retrieved == data


def test_deduplication(storage):
    data = b"same content"
    stored1 = storage.save(data, "a.txt")
    stored2 = storage.save(data, "b.txt")
    assert stored1.path == stored2.path
    assert stored1.hash == stored2.hash


def test_exists(storage):
    data = b"exists test"
    stored = storage.save(data, "e.txt")
    assert storage.exists(stored.path) is True
    assert storage.exists("resumes/nonexistent.txt") is False


def test_delete(storage):
    data = b"delete me"
    stored = storage.save(data, "d.txt")
    assert storage.exists(stored.path) is True
    storage.delete(stored.path)
    assert storage.exists(stored.path) is False


def test_get_nonexistent(storage):
    with pytest.raises(FileNotFoundError):
        storage.get("resumes/doesnotexist.txt")
