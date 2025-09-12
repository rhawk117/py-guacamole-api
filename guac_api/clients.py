import abc
from collections.abc import Callable
import contextlib
from datetime import timedelta
import ssl
from typing import Generic, TypeVar, Unpack
import httpx
from guac_api.config import ClientOptions, AsyncHttpOptions, HttpOptions
from guac_api.request_spec import HttpBackend


_C = TypeVar("_C", httpx.Client, httpx.AsyncClient)
_H = TypeVar("_H", bound=ClientOptions)



class _GuacamoleAPI(Generic[_C]):
    client_class: type[_C]

    def __init__(
        self,
        *,
        username: str,
        password: str,
        host: str,
        data_source: str,
        idle_timeout: float | timedelta | None = None,
    ) -> None:
        self.username = username
        self.password = password
        self.data_source = data_source
        idle_timeout = (
            idle_timeout.total_seconds()
            if isinstance(idle_timeout, timedelta)
            else idle_timeout
        )
        self.idle_timeout = idle_timeout or 300.0  # default to 5 minutes
        self.host = host.rstrip("/")
        self._client: _C | None = None
        self._auth_client: _C | None = None

    @property
    def api_url(self) -> str:
        return f"{self.host}/api"


    def configure(
        self,
        *,
        timeout: httpx.Timeout | float | None = 10.0,
        limit: httpx.Limits | None = None,
        verify: bool | str | ssl.SSLContext = True,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        max_redirects: int = 20,
        mounts: dict[str, httpx.BaseTransport] | None = None,
        transport: httpx.BaseTransport | None = None,
        request_hooks: list[Callable[[httpx.Request], None]] | None = None,
        response_hooks: list[Callable[[httpx.Response], None]] | None = None,
    ) -> None:
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
        if self._client or self._auth_client:
            raise RuntimeError("Clients are already configured. Please close them before reconfiguring.")
        kwargs = {
            "timeout": timeout,
            "limits": limit,
            "verify": verify,
            "params": params,
            "headers": headers,
            "max_redirects": max_redirects,
            "mounts": mounts,
            "transport": transport,
            'event_hooks': {
                "request": request_hooks or [],
                "response": response_hooks or [],
            }
        }
        self._client = self.client_class(
            base_url=self.api_url,
            **kwargs
        )
        self._auth_client = self.client_class(
            base_url=self.api_url,
            **kwargs
        )

    @property
    def client(self) -> _C:
        if not self._client or not self._auth_client:
            self.configure()
        return self._client # type: ignore[return-value]

    @property
    def auth_client(self) -> _C:
        if not self._client or not self._auth_client:
            self.configure()
        return self._auth_client # type: ignore[return-value]

class GuacamoleClient(_GuacamoleAPI[httpx.Client]):
    """
    Sync HTTP Adapter for Guacamole API interactions.

    Parameters
    ----------
    GuacamoleHttpAdapter
    """

    client_class = httpx.Client


    def close(self) -> None:
        if self._client:
            self._client.close()

        if self._auth_client:
            self._auth_client.close()


class AsyncGuacamoleClient(_GuacamoleAPI[httpx.AsyncClient]):
    client_class = httpx.AsyncClient

    async def aclose(self) -> None:
        if self._client:
            await self._client.aclose()

        if self._auth_client:
            await self._auth_client.aclose()

