"""Bounded HTTP operations with shared per-source request serialization."""

import threading
import logging
import re
from contextlib import contextmanager
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

from .models import Budget


class CredentialFilter(logging.Filter):
    """httpx INFO logs otherwise include SerpAPI/OpenAlex query-string keys."""

    def filter(self, record):
        record.msg = re.sub(
            r"(?i)((?:api[_-]?key|token)=)[^&\s\"']+", r"\1[REDACTED]", record.getMessage()
        )
        record.args = ()
        return True


logging.getLogger("httpx").addFilter(CredentialFilter())


class SourceError(Exception):
    def __init__(self, kind, message, retryable=False, status_code=None):
        super().__init__(message)
        self.kind, self.retryable, self.status_code = kind, retryable, status_code

    def public(self):
        return {
            "kind": self.kind,
            "message": str(self),
            "retryable": self.retryable,
            "status_code": self.status_code,
        }


class Operation:
    def __init__(self, budget: Budget | None = None):
        self.budget = budget or Budget()
        self.started = time.monotonic()
        self.requests = self.items = self.download_bytes = 0

    def remaining(self):
        return max(0.0, self.budget.max_seconds - (time.monotonic() - self.started))

    def check(self):
        if not self.remaining() or self.requests >= self.budget.max_requests:
            raise SourceError("budget", "Operation request/time budget reached")

    def usage(self):
        return {
            "requests": self.requests,
            "items": self.items,
            "seconds": round(time.monotonic() - self.started, 3),
            "download_bytes": self.download_bytes,
        }


class Transport:
    def __init__(self, client=None, intervals=None):
        self.client = client or httpx.Client(follow_redirects=True)
        self.intervals = intervals or {
            "arxiv": 3.0,
            "semantic_scholar": 1.0,
            "scholar": 1.0,
            "openalex": 0.15,
            "download": 0.1,
        }
        self.locks = {s: threading.Lock() for s in self.intervals}
        self.last = {s: 0.0 for s in self.intervals}

    @contextmanager
    def slot(self, source, op):
        acquired = self.locks[source].acquire(timeout=op.remaining())
        if not acquired:
            raise SourceError("budget", "Request queue wait exceeds operation budget")
        try:
            yield
        finally:
            self.locks[source].release()

    def request(self, source, url, op, params=None, headers=None):
        for attempt in range(3):
            op.check()
            with self.slot(source, op):
                delay = max(0.0, self.last[source] + self.intervals[source] - time.monotonic())
                if delay >= op.remaining():
                    raise SourceError("budget", "Rate-limit wait exceeds operation budget")
                time.sleep(delay)
                op.check()
                op.requests += 1
                try:
                    response = self.client.get(
                        url,
                        params=params,
                        headers=headers,
                        timeout=min(20.0, op.remaining()),
                        follow_redirects=False,
                    )
                except httpx.TimeoutException:
                    raise SourceError("timeout", "Upstream request timed out", True) from None
                except httpx.HTTPError:
                    raise SourceError("network", "Upstream network request failed", True) from None
                finally:
                    self.last[source] = time.monotonic()
            status = response.status_code
            if status == 429 or 500 <= status < 600:
                if attempt < 2:
                    wait = self.retry_delay(response.headers.get("Retry-After"), 2**attempt)
                    if wait < op.remaining() and op.requests < op.budget.max_requests:
                        time.sleep(wait)
                        continue
                raise SourceError(
                    "rate_limit" if status == 429 else "upstream",
                    "Upstream rate limit or server error",
                    True,
                    status,
                )
            if 300 <= status < 400:
                raise SourceError("redirect", "Unexpected upstream API redirect")
            if status >= 400:
                kind = {
                    400: "invalid_request",
                    401: "authentication",
                    403: "permission",
                    404: "not_found",
                    402: "quota",
                }.get(status, "upstream")
                raise SourceError(kind, f"Upstream HTTP {status}", False, status)
            return response
        raise AssertionError("Unreachable retry state")

    @staticmethod
    def retry_delay(value, fallback):
        if value:
            try:
                return max(0.0, float(value))
            except ValueError:
                try:
                    return max(
                        0.0,
                        (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds(),
                    )
                except (ValueError, TypeError):
                    pass
        return float(fallback)

    def json(self, source, url, op, **kwargs):
        response = self.request(source, url, op, **kwargs)
        try:
            obj = response.json()
        except ValueError:
            raise SourceError("parse", "Upstream returned invalid JSON") from None
        if not isinstance(obj, dict):
            raise SourceError("parse", "Expected an upstream JSON object")
        if obj.get("error") or (obj.get("search_metadata") or {}).get("status") == "Error":
            raise SourceError("upstream", "Upstream returned a business error")
        return obj
