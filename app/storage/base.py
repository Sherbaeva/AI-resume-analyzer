"""Abstract storage interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StorageFile:
    path: str        # relative path inside storage dir
    filename: str    # original filename
    size: int        # bytes
    hash: str        # sha256 hex digest


class StorageService(ABC):
    @abstractmethod
    def save(self, file_bytes: bytes, filename: str) -> StorageFile:
        """Persist file_bytes and return StorageFile metadata."""
        ...

    @abstractmethod
    def get(self, path: str) -> bytes:
        """Return raw bytes for the given relative path."""
        ...

    @abstractmethod
    def delete(self, path: str) -> None:
        """Remove the file at path."""
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Return True if the file exists at path."""
        ...
