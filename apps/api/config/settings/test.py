"""Test settings for Amanus Learn AI API."""

from .base import *

DEBUG = False
TESTING = True

# Fast in-memory SQLite database for unit tests
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
