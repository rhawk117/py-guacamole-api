
from __future__ import annotations

from collections.abc import Generator, Mapping
import contextlib
from datetime import timedelta
from typing import Any, AsyncGenerator, Self
import httpx
from guac_api.auth import GuacamoleSession, TokensClient, AsyncGuacamoleSession, AsyncTokensClient
from guac_api.options import ClientConfig, GuacamoleConfig
import dataclasses as dc







class Guacamole:

    def __init__(
        self,
        guac_config: GuacamoleConfig,
        *,
        client_config: ClientConfig | None = None,
        mounts: Mapping[str, httpx.BaseTransport | None] | None = None,
        transport: httpx.BaseTransport | None = None,
        idle_token_timeout: timedelta | None = None,
    ) -> None:
        self.config: GuacamoleConfig = guac_config

        client_config = client_config or ClientConfig()
        client_kwargs: dict[str, Any] = dc.asdict(client_config)
        client_kwargs.update({
            'base_url': guac_config.url,
            'mounts': mounts or client_kwargs.get('mounts'),
            'transport': transport or client_kwargs.get('transport'),
        })


        self.tokens: TokensClient = TokensClient(
            client=httpx.Client(**client_kwargs)
        )
        self._session: GuacamoleSession = GuacamoleSession(
            tokens_client=self.tokens,
            idle_timeout=idle_token_timeout,
            crendetials={
                'username': guac_config.username,
                'password': guac_config.password,
            },
        )
        self._client: httpx.Client = httpx.Client(**client_kwargs)

    def dispose(self) -> None:
        self._client.close()
        self.tokens.client.close()


    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any) -> None:
        self.dispose()

    @classmethod
    @contextlib.contextmanager
    def life_cycle(
        cls,
        guac_config: GuacamoleConfig,
        *,
        client_config: ClientConfig | None = None,
        mounts: Mapping[str, httpx.BaseTransport | None] | None = None,
        transport: httpx.BaseTransport | None = None,
        idle_token_timeout: timedelta | None = None,
    )  -> Generator[Self, Any, None]:
        client = cls(
            guac_config,
            client_config=client_config,
            mounts=mounts,
            transport=transport,
            idle_token_timeout=idle_token_timeout,
        )
        try:
            yield client
        finally:
            client.dispose()




class AsyncGuacamole:
    def __init__(
        self,
        guac_config: GuacamoleConfig,
        *,
        client_config: ClientConfig | None = None,
        mounts: Mapping[str, httpx.AsyncBaseTransport | None] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        idle_token_timeout: timedelta | None = None,
    ) -> None:
        self.config: GuacamoleConfig = guac_config

        client_config = client_config or ClientConfig()
        client_kwargs: dict[str, Any] = dc.asdict(client_config)
        client_kwargs.update({
            'base_url': guac_config.url,
            'mounts': mounts or client_kwargs.get('mounts'),
            'transport': transport or client_kwargs.get('transport'),
        })


        self.tokens: AsyncTokensClient = AsyncTokensClient(
            client=httpx.AsyncClient(**client_kwargs)
        )
        self._session: AsyncGuacamoleSession = AsyncGuacamoleSession(
            tokens_client=self.tokens,
            idle_timeout=idle_token_timeout,
            credentials={
                'username': guac_config.username,
                'password': guac_config.password,
            },
        )
        self._client: httpx.AsyncClient = httpx.AsyncClient(**client_kwargs)

    async def dispose(self) -> None:
        await self._client.aclose()
        await self.tokens.client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.dispose()

    @classmethod
    @contextlib.asynccontextmanager
    async def life_cycle(
        cls,
        guac_config: GuacamoleConfig,
        *,
        client_config: ClientConfig | None = None,
        mounts: Mapping[str, httpx.AsyncBaseTransport | None] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        idle_token_timeout: timedelta | None = None,
    )  -> AsyncGenerator[Self, Any]:
        client = cls(
            guac_config,
            client_config=client_config,
            mounts=mounts,
            transport=transport,
            idle_token_timeout=idle_token_timeout,
        )
        try:
            yield client
        finally:
            await client.dispose()







