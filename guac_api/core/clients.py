import abc
import contextlib
from typing import Generic, TypeVar, Unpack
import httpx
from guac_api.core.config import ClientOptions, AsyncHttpOptions, HttpOptions, GuacamoleConfig
from guac_api.core.request_spec import HttpBackend


_C = TypeVar("_C", httpx.Client, httpx.AsyncClient)
_H = TypeVar("_H", bound=ClientOptions)


def get_httpx_client_kwargs(options: ClientOptions) -> dict:
    if not (timeout := options.pop("timeout")):
        timeout = httpx.Timeout(10.0)

    if not (limits := options.pop("limits")):
        limits = httpx.Limits(
            max_connections=10,
            max_keepalive_connections=5,
            keepalive_expiry=5.0,
        )

    verify = options.pop("verify", True)
    max_redirects = options.pop("max_redirects", 20)
    headers = options.pop("headers", None)
    params = options.pop("params", None)

    events = {
        "request": options.pop("request_hooks", []),
        "response": options.pop("response_hooks", []),
    }

    return dict(
        timeout=timeout,
        limits=limits,
        verify=verify,
        max_redirects=max_redirects,
        headers=headers,
        params=params,
        mounts=options.pop("mounts", None),
        transport=options.pop("transport", None),
        event_hooks=events,
    )


class GuacamoleHttpAdapter(Generic[_C]):
    client_class: type[_C]

    def __init__(self, guac_host: str, **options: Unpack[ClientOptions]) -> None:
        self._client: _C | None = None
        self._auth_client: _C | None = None
        self.options = options
        self.host = guac_host

    def create_http_client(self, base_url: str) -> _C:
        kwargs = get_httpx_client_kwargs(self.options)
        return self.client_class(base_url=base_url, **kwargs)

    def open(
        self,
        **options: Unpack[ClientOptions]
    ) -> None:
        if options:
            self.options.update(options)

        guac_host = self.host.rstrip('/')
        url = f'{guac_host}/api'
        self._client = self.create_http_client(base_url=url)
        self._auth_client = self.create_http_client(base_url=url)

    def close(self) -> None:
        raise NotImplementedError

    async def aclose(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def create_namespace(self, path: str) -> HttpBackend:
        raise NotImplementedError

    @property
    def client(self) -> _C:
        if not self._client:
            self.open()
        return self._client  # type: ignore[return-value]

    @property
    def auth_client(self) -> _C:
        if not self._auth_client:
            self.open()
        return self._auth_client  # type: ignore[return-value]



class SyncHttpAdapter(GuacamoleHttpAdapter[httpx.Client]):
    """
    Sync HTTP Adapter for Guacamole API interactions.

    Parameters
    ----------
    GuacamoleHttpAdapter
    """

    client_class = httpx.Client

    def __init__(self, guac_host: str, **options: HttpOptions) -> None:
        super().__init__(guac_host, **options) # type: ignore[arg-type]


    def close(self) -> None:
        if self._client:
            self._client.close()

        if self._auth_client:
            self._auth_client.close()

    def create_namespace(self, path: str) -> HttpBackend:
        return HttpBackend(client=self.client, path=path)


class AsyncHttpAdapter(GuacamoleHttpAdapter[httpx.AsyncClient]):
    client_class = httpx.AsyncClient


    def __init__(self, guac_host: str, **options: AsyncHttpOptions) -> None:
        super().__init__(guac_host, **options) # type: ignore[arg-type]

    async def aclose(self) -> None:
        if self._client:
            await self._client.aclose()

        if self._auth_client:
            await self._auth_client.aclose()




