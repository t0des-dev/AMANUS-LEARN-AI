"""YAML-backed fixtures for the deterministic MockAIProvider.

The mock responses live in ``apps/ai/fixtures/mock/*.yaml`` so they can be
edited without touching provider code. Files are loaded lazily, cached in
process, and deep-copied per call so callers can never corrupt the cache.
"""

import copy
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "mock"


@lru_cache(maxsize=None)
def _load(name: str) -> Any:
    path = FIXTURES_DIR / f"{name}.yaml"
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def fixture(name: str) -> Any:
    """Returns a deep copy of the named JSON-response fixture."""
    return copy.deepcopy(_load(name))


def fixture_text(name: str) -> str:
    """Returns a plain-text response from ``text_responses.yaml``."""
    return str(_load("text_responses")[name])
