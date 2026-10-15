"""Test settings for Amanus Learn AI API."""

import os
import socket
from urllib.parse import unquote, urlparse

from .base import *

DEBUG = False
TESTING = True


def _test_db_host_resolvable(hostname: str | None) -> bool:
    if not hostname:
        return False
    if hostname in ("localhost", "127.0.0.1", "::1"):
        return True
    try:
        socket.gethostbyname(hostname)
        return True
    except (socket.gaierror, OSError):
        return False


# Use PostgreSQL (with pgvector) when DATABASE_URL is provided AND its host is
# reachable (e.g. in CI, where the pgvector service runs on localhost). Otherwise
# fall back to fast in-memory SQLite for local unit tests, so a docker-internal
# DATABASE_URL (host "postgres") does not break local runs.
_database_url = os.getenv("DATABASE_URL")
if (
    _database_url
    and _database_url.startswith(("postgresql://", "postgres://"))
    and _test_db_host_resolvable(urlparse(_database_url).hostname)
):
    _url = urlparse(_database_url)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _url.path.lstrip("/"),
            "USER": unquote(_url.username) if _url.username else "",
            "PASSWORD": unquote(_url.password) if _url.password else "",
            "HOST": _url.hostname,
            "PORT": _url.port or 5432,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

# Fast password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Eager celery execution during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Storage backend for tests
STORAGE_BACKEND = "local"

# Disable rate limiting throttles for test runs
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
}

# Use local-memory cache in tests (no Redis dependency)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "amanus-tests",
    }
}

# Tests rely on the deterministic mock AI provider
ALLOW_MOCK_AI_PROVIDER = True
