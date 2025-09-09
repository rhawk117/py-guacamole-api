


from __future__ import annotations

from collections.abc import Callable
import dataclasses as dc
from typing import TypedDict

import httpx



class HttpxHooks(TypedDict, total=False):
    """Event hooks for httpx.Client."""

    request: list[Callable] | None
    response: list[Callable] | None

@dc.dataclass(slots=True, kw_only=True)
class HttpOptions:
    '''
    The allowed user specified configurations for the httpx
    client.
    '''
    timeout: httpx.Timeout | float = httpx.Timeout(10.0)
    verify: bool | str | None = None
    headers: dict[str, str] | None = dc.field(default_factory=dict)
    http2: bool = False
    event_hooks: HttpxHooks | None = None
    transport: httpx.BaseTransport | None = None
    proxies: str | httpx.Proxy | dict[str, str | httpx.Proxy] | None = None
    auth: httpx.Auth | None = None
    max_in_flight: int | None = None


@dc.dataclass(slots=True, kw_only=True)
class RequestOptions:
    '''
    The allowed overrides for individual requests, these will
    either merge or override the existing HttpOptions.
    '''
    timeout: httpx.Timeout | float | None = None
    headers: dict[str, str] | None = dc.field(default_factory=dict)