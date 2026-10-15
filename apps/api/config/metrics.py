"""Application metrics exposed at ``/metrics`` in Prometheus text format.

Cardinality rules: only low-cardinality labels (provider, operation, metric,
outcome) — never user, organization or document identifiers.
"""

import time
from contextlib import contextmanager
from typing import Iterator

from prometheus_client import Counter, Histogram

AI_REQUEST_DURATION = Histogram(
    "amanus_ai_request_duration_seconds",
    "Latency of AI provider generation calls in seconds",
    labelnames=("provider", "operation", "status"),
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
)

QUOTA_RESERVATIONS = Counter(
    "amanus_quota_reservations_total",
    "Quota reservation attempts by usage metric and outcome",
    labelnames=("metric", "outcome"),
)

QUOTA_COMMITS = Counter(
    "amanus_quota_commits_total",
    "Quota reservation outcomes by usage metric (committed or released)",
    labelnames=("metric", "outcome"),
)


@contextmanager
def timed_ai_call(provider: str, operation: str) -> Iterator[None]:
    """Times an AI provider call and records duration/status in AI_REQUEST_DURATION."""
    start = time.monotonic()
    status = "success"
    try:
        yield
    except BaseException:
        status = "error"
        raise
    finally:
        AI_REQUEST_DURATION.labels(
            provider=provider, operation=operation, status=status
        ).observe(time.monotonic() - start)


def observe_quota_reservation(metric: str, outcome: str) -> None:
    QUOTA_RESERVATIONS.labels(metric=metric, outcome=outcome).inc()


def observe_quota_commit(metric: str, outcome: str) -> None:
    QUOTA_COMMITS.labels(metric=metric, outcome=outcome).inc()
