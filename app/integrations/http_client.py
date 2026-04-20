import random
import threading
import time
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import UpstreamServiceException
from app.core.logging import get_logger

logger = get_logger(__name__)


class ResilientHttpClient:
    def __init__(self):
        self._client = httpx.Client(timeout=settings.external_request_timeout_seconds)
        self._provider_lock = threading.Lock()
        self._last_call_ts: dict[str, float] = {}

    def request_json(
        self,
        provider: str,
        method: str,
        url: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        min_interval_ms: int = 0,
    ) -> Any:
        merged_headers = {"User-Agent": settings.external_user_agent}
        if headers:
            merged_headers.update(headers)

        attempt = 0
        max_attempts = max(settings.external_max_retries + 1, 1)

        while attempt < max_attempts:
            attempt += 1
            self._respect_min_interval(provider, min_interval_ms)
            try:
                response = self._client.request(method=method, url=url, params=params, headers=merged_headers)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempt >= max_attempts:
                    raise UpstreamServiceException(
                        message=f"{provider} request failed after retries",
                        details=[{"reason": str(exc)}],
                    ) from exc
                self._sleep_backoff(attempt)
                continue

            if response.status_code == 429:
                if attempt >= max_attempts:
                    raise UpstreamServiceException(
                        message=f"{provider} rate limit reached",
                        details=[{"status_code": response.status_code}],
                    )
                self._sleep_retry_after(response.headers.get("Retry-After"), attempt)
                continue

            if response.status_code >= 500 or response.status_code == 408:
                if attempt >= max_attempts:
                    raise UpstreamServiceException(
                        message=f"{provider} service unavailable",
                        details=[{"status_code": response.status_code, "body": response.text[:300]}],
                    )
                self._sleep_backoff(attempt)
                continue

            if response.status_code >= 400:
                raise UpstreamServiceException(
                    message=f"{provider} returned non-success status",
                    details=[{"status_code": response.status_code, "body": response.text[:300]}],
                )

            try:
                return response.json()
            except ValueError as exc:
                raise UpstreamServiceException(
                    message=f"{provider} returned invalid JSON",
                    details=[{"status_code": response.status_code}],
                ) from exc

        raise UpstreamServiceException(message=f"{provider} request failed")

    def _respect_min_interval(self, provider: str, min_interval_ms: int) -> None:
        if min_interval_ms <= 0:
            return
        with self._provider_lock:
            now = time.monotonic()
            last_call = self._last_call_ts.get(provider)
            min_interval_s = min_interval_ms / 1000
            if last_call is not None:
                elapsed = now - last_call
                if elapsed < min_interval_s:
                    sleep_for = min_interval_s - elapsed
                    logger.debug("provider_throttle_sleep", extra={"provider": provider, "sleep_s": sleep_for})
                    time.sleep(sleep_for)
            self._last_call_ts[provider] = time.monotonic()

    def _sleep_backoff(self, attempt: int) -> None:
        delay = min(
            settings.external_backoff_base_seconds * (2 ** (attempt - 1)),
            settings.external_backoff_max_seconds,
        )
        jitter = random.uniform(0, 0.25)
        time.sleep(delay + jitter)

    def _sleep_retry_after(self, retry_after_header: str | None, attempt: int) -> None:
        if not retry_after_header:
            self._sleep_backoff(attempt)
            return

        try:
            retry_after = float(retry_after_header)
            time.sleep(max(retry_after, 0.0))
            return
        except ValueError:
            pass

        try:
            retry_dt = parsedate_to_datetime(retry_after_header)
            now_ts = time.time()
            sleep_for = retry_dt.timestamp() - now_ts
            time.sleep(max(sleep_for, 0.0))
        except Exception:
            self._sleep_backoff(attempt)
