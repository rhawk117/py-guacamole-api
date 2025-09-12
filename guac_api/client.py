import abc
from datetime import timedelta
from typing import Self, Unpack
from guac_api.clients import (
    AsyncHttpAdapter,
    HttpOptions,
    AsyncHttpOptions,
    SyncHttpAdapter,
)
import dataclasses as dc

@dc.dataclass
class GuacamoleConfig:
    host: str
    username: str
    password: str
    data_source: str
    idle_timeout: timedelta = timedelta(minutes=30)



class SyncGuacAPI:
    def __init__(self, config: GuacamoleConfig) -> None:
        self.config: GuacamoleConfig = config
        self._adapter: SyncHttpAdapter = SyncHttpAdapter(
            guac_host=self.config.host
        )


    def configure_client(self, **options: Unpack[HttpOptions]) -> None:
        self._adapter.open(**options)

    def __enter__(self, **options: Unpack[HttpOptions]) -> "SyncGuacAPI":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._adapter.close()

    def dispose(self) -> None:
        self._adapter.close()
class AsyncGuacAPI:
    def __init__(self, config: GuacamoleConfig) -> None:
        self.config = config
        self._adapter = AsyncHttpAdapter(
            guac_host=self.config.host
        )

    def configure_client(
        self,
        *,
        timeout: httpx.Timeout | float | None = 10.0,

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

    async def __aenter__(self, **options: Unpack[AsyncHttpOptions]) -> Self:
        self._adapter.open(**options)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self._adapter.aclose()

    async def dispose(self) -> None:
        await self._adapter.aclose()


guac = AsyncGuacAPI(
    GuacamoleConfig(
        host="http://localhost:8080/guacamole",
        username="guacadmin",
        password="guacadmin",
        data_source="postgresql",
    )
)
guac.configure_client(
)