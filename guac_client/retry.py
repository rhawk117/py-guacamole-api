from __future__ import annotations

import asyncio
from contextlib import suppress
import random
import time
from dataclasses import dataclass
from typing import Protocol

import httpx


class ShouldRetryHook(Protocol):
    def __call__(
        self,
        request: httpx.Request,
        attempt: int,
        result: httpx.Response | Exception,
    ) -> bool: ...


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    '''
    How to handle, when and how often to retry
    HTTP requests that fail due to transport
    issues or certain HTTP status codes.
    '''
    max_attempts: int = 3
    retry_methods: frozenset[str] = frozenset(
        {"GET", "HEAD", "OPTIONS", "TRACE", "PUT", "DELETE"}
    )
    retry_statuses: frozenset[int] = frozenset(
        {
            429,
            500,
            502,
            503,
            504,
            408,
        }
    )
    retry_on_exceptions: tuple[type[Exception], ...] = (
        httpx.ConnectError,
        httpx.ReadTimeout,
        httpx.ConnectTimeout,
        httpx.RemoteProtocolError,
    )
    respect_retry_after: bool = True
    base_delay: float = 0.25
    max_delay: float = 8.0
    backoff_multiplier: float = 2.0
    jitter: tuple[float, float] = (0.0, 0.25)
    should_retry_hook: ShouldRetryHook | None = None


def extract_retry_after_seconds(response: httpx.Response) -> float | None:
    """
    Tries to get the number of seconds to wait from the
    Retry-After header in the response.

    Parameters
    ----------
    response : httpx.Response

    Returns
    -------
    float | None
    """
    retry_after_header = response.headers.get("Retry-After")
    if not retry_after_header:
        return None

    try:
        return max(0.0, float(retry_after_header))
    except ValueError:
        return None


def calculate_delay(
    attempt: int, policy: RetryPolicy, response: httpx.Response | None
) -> float:
    """
    Calculate the delay before the next retry attempt.

    Parameters
    ----------
    attempt : int
    policy : RetryPolicy
    response : httpx.Response | None

    Returns
    -------
    float
    """
    if response is not None and policy.respect_retry_after:
        retry_after_delay = extract_retry_after_seconds(response)
        if retry_after_delay is not None:
            jitter_amount = random.uniform(*policy.jitter)
            return min(policy.max_delay, retry_after_delay + jitter_amount)

    base_delay = policy.base_delay * (policy.backoff_multiplier ** (attempt - 1))
    delay_with_cap = min(base_delay, policy.max_delay)
    jitter_amount = random.uniform(*policy.jitter)

    return delay_with_cap + jitter_amount


def should_retry_request(
    request: httpx.Request,
    attempt: int,
    result: httpx.Response | Exception,
    policy: RetryPolicy,
) -> bool:
    """
    Determine if a request should be retried based on the result

    Parameters
    ----------
    request : httpx.Request
    attempt : int
    result : httpx.Response | Exception
    policy : RetryPolicy

    Returns
    -------
    bool
    """
    should_retry = False

    if isinstance(result, Exception):
        should_retry = isinstance(result, policy.retry_on_exceptions)
    else:
        should_retry = result.status_code in policy.retry_statuses

    if should_retry and request.method.upper() not in policy.retry_methods:
        should_retry = False

    if policy.should_retry_hook:
        with suppress(Exception):
            should_retry = policy.should_retry_hook(request, attempt, result)

    return should_retry


def send_with_retries_sync(
    client: httpx.Client, request: httpx.Request, policy: RetryPolicy
) -> httpx.Response:
    """
    Sends a HTTP request with retry logic (synchronous).

    Parameters
    ----------
    client : httpx.Client
    request : httpx.Request
    policy : RetryPolicy

    Returns
    -------
    httpx.Response

    Raises
    ------
    last_exception
    """
    attempt = 1
    last_exception = None
    while attempt <= policy.max_attempts:
        result: httpx.Response | Exception
        try:
            result = client.send(request, stream=False)
        except Exception as exc:
            result = exc
            last_exception = exc

        if attempt < policy.max_attempts and should_retry_request(
            request, attempt, result, policy
        ):
            response_for_delay = result if isinstance(result, httpx.Response) else None
            delay = calculate_delay(attempt, policy, response_for_delay)
            time.sleep(delay)
            attempt += 1
            continue

        if isinstance(result, Exception):
            raise result

        return result

    assert last_exception is not None
    raise last_exception


async def send_with_retries_async(
    client: httpx.AsyncClient, request: httpx.Request, policy: RetryPolicy
) -> httpx.Response:
    '''
    Sends a HTTP request with retry logic (asynchronous).

    Parameters
    ----------
    client : httpx.AsyncClient
    request : httpx.Request
    policy : RetryPolicy

    Returns
    -------
    httpx.Response

    Raises
    ------
    last_exception
    '''
    attempt = 1
    last_exception = None
    while attempt <= policy.max_attempts:
        result: httpx.Response | Exception
        try:
            result = await client.send(request, stream=False)
        except Exception as exc:
            result = exc
            last_exception = exc

        if attempt < policy.max_attempts and should_retry_request(
            request, attempt, result, policy
        ):
            response_for_delay = result if isinstance(result, httpx.Response) else None
            delay = calculate_delay(attempt, policy, response_for_delay)
            await asyncio.sleep(delay)
            attempt += 1
            continue

        if isinstance(result, Exception):
            raise result
        return result

    assert last_exception is not None
    raise last_exception