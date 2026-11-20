"""Explicit configuration, no secret values in public capability reports."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    cache_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("PAPER_SEARCH_CACHE_DIR", Path.home() / ".cache" / "paper-search-mcp")
        )
    )
    keys: dict[str, str] = field(default_factory=dict, repr=False)

    @classmethod
    def from_env(cls):
        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        return cls(
            keys={
                s: os.getenv(k, "")
                for s, k in {
                    "semantic_scholar": "SEMANTIC_SCHOLAR_API_KEY",
                    "scholar": "SERPAPI_KEY",
                    "openalex": "OPENALEX_API_KEY",
                }.items()
            }
        )
