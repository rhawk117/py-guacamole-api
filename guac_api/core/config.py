





from collections.abc import Mapping
from datetime import timedelta
import ssl
from typing import Awaitable, Callable, Generic, Sequence, TypeVar, TypedDict

import httpx


T = TypeVar('T', bound=httpx.BaseTransport | httpx.AsyncBaseTransport)

SyncHooks = Callable[[httpx.Request], None] | Callable[[httpx.Response], None]
AsyncHooks = Callable[[httpx.Request], Awaitable[None]] | Callable[[httpx.Response], Awaitable[None]]




class ClientOptions(
    Generic[T],
    TypedDict,
    total=False,
):
    timeout: httpx.Timeout | float | None
    limits: httpx.Limits
    verify: bool | str | ssl.SSLContext
    params: dict[str, str]
    headers: dict[str, str]
    max_redirects: int
    mounts: Mapping[str, T]
    transport: T



class AsyncHttpOptions(
    ClientOptions[httpx.AsyncBaseTransport],
    total=False
):
    request_hooks: Sequence[Callable[[httpx.Request], Awaitable[None]]]
    response_hooks: Sequence[Callable[[httpx.Response], Awaitable[None]]]

class HttpOptions(
    ClientOptions[httpx.BaseTransport],
    total=False
):
    request_hooks: Sequence[Callable[[httpx.Request], None]]
    response_hooks: Sequence[Callable[[httpx.Response], None]]


class GuacamoleConfig(TypedDict):
    username: str
    password: str
    host: str
    data_source: str
    idle_timeout: float | timedelta


