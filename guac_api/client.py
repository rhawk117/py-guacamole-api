import abc
from typing import Unpack
from guac_api.core.clients import (
    AsyncHttpAdapter,
    GuacamoleConfig,
    HttpBackend,
    HttpOptions,
    AsyncHttpOptions,
    ClientOptions,
    SyncHttpAdapter
)

class _GuacAPI(abc.ABC):
    def __init__(self, config: GuacamoleConfig) -> None:
        self._config = config

    @property
    def host(self) -> str:
        return self._config["host"]

    @property
    def username(self) -> str | None:
        return self._config.get("username")

    @property
    def data_source(self) -> str | None:
        return self._config.get("data_source")

    @abc.abstractmethod
    def configure(self, **options) -> None: ...


class SyncGuacAPI(_GuacAPI):
    def __init__(self, config: GuacamoleConfig) -> None:
        super().__init__(config)
        self._adapter = SyncHttpAdapter(guac_host=self.host)

    def configure_client(self, **options: Unpack[HttpOptions]) -> None:
        self._adapter.open(**options)

    def __enter__(self) -> "SyncGuacAPI":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._adapter.close()


class AsyncGuacAPI(_GuacAPI):
    def __init__(self, config: GuacamoleConfig) -> None:
        super().__init__(config)
        self._adapter = AsyncHttpAdapter(guac_host=self.host)

    def configure_client(self, **options: Unpack[AsyncHttpOptions]) -> None:
        self._adapter.open(**options)

    async def __aenter__(self) -> "AsyncGuacAPI":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self._adapter.aclose()
