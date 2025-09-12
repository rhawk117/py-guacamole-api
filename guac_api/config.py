





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
    '''
    Options for configuring HTTP clients.

    Parameters
    ----------
    timeout : httpx.Timeout | float | None
        Timeout configuration for the client. If None, defaults to 10 seconds.
    limits : httpx.Limits
        Connection limits for the client. If not provided, defaults to:
            - max_connections=10
            - max_keepalive_connections=5
            - keepalive_expiry=5.0 seconds
    verify : bool | str | ssl.SSLContext
        SSL verification settings. Can be a boolean, path to a CA bundle, or an SSL context.
        Defaults to True.
    params : dict[str, str]
        Default query parameters to include in every request.
    headers : dict[str, str]
        Default headers to include in every request.
    max_redirects : int
        Maximum number of redirects to follow. Defaults to 20.
    mounts : Mapping[str, T]
        A mapping of URL prefixes to custom transports.
    transport : T
        A custom transport instance.
    request_hooks : Sequence[SyncHooks] | Sequence[AsyncHooks]
        A sequence of hooks to be called on each request.
    response_hooks : Sequence[SyncHooks] | Sequence[AsyncHooks]
        A sequence of hooks to be called on each response.
    '''
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




