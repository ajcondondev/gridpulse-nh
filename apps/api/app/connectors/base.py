from abc import ABC, abstractmethod
from pathlib import Path


class BaseConnector(ABC):
    source_id: str

    @abstractmethod
    def fetch(self) -> dict:
        """Pull raw data from the source. Returns a dict with at minimum 'dataframe' and 'fetched_at'."""
        ...

    @abstractmethod
    def clean(self, raw_path: Path):
        """Read raw data from raw_path, clean it, and return a pandas DataFrame."""
        ...
