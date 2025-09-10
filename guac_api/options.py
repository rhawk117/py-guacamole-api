


from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import timedelta
import ssl
from typing import (
    Awaitable,
    Sequence,
)
import dataclasses as dc
import httpx


RequestHookTypes = (
    Callable[[httpx.Request], None] | Callable[[httpx.Request], Awaitable[None]]
)
ResponseHookTypes = (
    Callable[[httpx.Response], None] | Callable[[httpx.Response], Awaitable[None]]
)


def _default_timeout() -> httpx.Timeout:
    return httpx.Timeout(
        timeout=10.0,
        connect=5.0,
        read=10.0,
        write=10.0,
        pool=5.0,
    )


def _default_limits() -> httpx.Limits:
    return httpx.Limits(
        max_keepalive_connections=5,
        max_connections=10,
        keepalive_expiry=5.0,
    )


@dc.dataclass(slots=True, kw_only=True)
class ClientConfig:
    timeout: httpx.Timeout = dc.field(default_factory=_default_timeout)
    limits: httpx.Limits = dc.field(default_factory=_default_limits)
    verify: bool | str | ssl.SSLContext = True
    params: Mapping[str, str] | None = None
    headers: Mapping[str, str] | None = None
    max_redirects: int = 20
    mounts: Mapping[str, httpx.BaseTransport] | None = None
    transport: httpx.BaseTransport | None = None
    hooks: Mapping[
        str,
        Sequence[RequestHookTypes | ResponseHookTypes],
    ] | None = None

@dc.dataclass(slots=True, kw_only=True)
class GuacamoleConfig:
    username: str
    password: str
    host: str
    data_source: str
    idle_timeout: timedelta = dc.field(
        default=timedelta(minutes=5),
    )

    @property
    def url(self) -> str:
        return f'{self.host.rstrip("/")}/api'

