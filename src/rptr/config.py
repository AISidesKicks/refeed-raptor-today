"""Local paths and runtime settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLACES_DIR = REPO_ROOT / "lab" / "demos"
DEFAULT_DATA_DIR = REPO_ROOT / "data"
DEFAULT_DB_NAME = "rptr.sqlite3"


@dataclass(frozen=True)
class Settings:
    """Everything the app needs to find places, the index, and the UI."""

    places_dir: Path
    data_dir: Path
    database_path: Path
    static_dir: Path

    @classmethod
    def from_env(cls) -> Settings:
        places_dir = Path(os.environ.get("RPTR_PLACES_DIR", DEFAULT_PLACES_DIR))
        data_dir = Path(os.environ.get("RPTR_DATA_DIR", DEFAULT_DATA_DIR))
        database_path = Path(os.environ.get("RPTR_DB", data_dir / DEFAULT_DB_NAME))
        return cls(
            places_dir=places_dir.expanduser().resolve(),
            data_dir=data_dir.expanduser().resolve(),
            database_path=database_path.expanduser().resolve(),
            static_dir=(Path(__file__).resolve().parent / "static").resolve(),
        )
