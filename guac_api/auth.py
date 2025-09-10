
import asyncio
from datetime import timedelta
import threading
import time
from typing import Generic, NamedTuple, Self, TypeVar, TypedDict

import httpx
import dataclasses as dc
from guac_api.options import GuacamoleConfig
from guac_api.errors import AuthError

class GuacToken(NamedTuple):
    token: str
    created_at: float


C = TypeVar("C", bound=httpx.Client | httpx.AsyncClient)


class _Credentials(TypedDict):
    username: str
    password: str


@dc.dataclass
class _AuthClient(Generic[C]):
    '''
    A base class for both the synchronous and asynchronous
    Guacamole authentication clients.
    '''
    _client: C
    _credentials: _Credentials
    _url: str

    @classmethod
    def from_config(cls, config: GuacamoleConfig, client: C) -> Self:
        '''
        Factory method to create an AuthClient from a GuacamoleConfig.

        Parameters
        ----------
        config : GuacamoleConfig
        client : C

        Returns
        -------
        Self
        '''
        return cls(
            _client=client,
            _credentials={"username": config.username, "password": config.password},
            _url=f"{config.url}/api/tokens",
        )

    def _check_token_response(self, token_response: httpx.Response) -> str:
        '''
        Validates a token response from the Guacamole server.

        Parameters
        ----------
        token_response : httpx.Response

        Returns
        -------
        str

        Raises
        ------
        AuthError
            _The `authToken` is missing or the response status is not 2xx._
        '''
        try:
            token_response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise AuthError(
                status=e.response.status_code,
                detail="Failed to authenticate with Guacamole server",
                response=e.response,
            ) from e

        data = token_response.json()
        if not (token := data.get("authToken")):
            raise AuthError(
                status=token_response.status_code,
                detail="Authentication response missing authToken",
                response=token_response,
            )
        return token


class AsyncAuthClient(_AuthClient[httpx.AsyncClient]):
    '''
    An asynchronous implementation of the Guacamole authentication client.
    '''
    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_token(self, *, credentials: _Credentials | None = None) -> GuacToken:
        '''
        Requests a new authentication token from the Guacamole server.

        Parameters
        ----------
        credentials : _Credentials | None, optional
            The credentials to use other than the default ones
            that were provided at initialization time, by default None

        Returns
        -------
        GuacToken
        '''
        credentials = credentials or self._credentials
        resp = await self._client.post(self._url, data=credentials)
        token = self._check_token_response(resp)
        return GuacToken(token=token, created_at=time.time())

    async def delete_token(self, token: str) -> None:
        url = f"{self._url}/{token}"
        await self._client.delete(url)


class SyncAuthClient(_AuthClient[httpx.Client]):
    def close(self) -> None:
        self._client.close()

    def get_token(self, *, credentials: _Credentials | None = None) -> GuacToken:
        """
        Requests a new authentication token from the Guacamole server.

        Parameters
        ----------
        credentials : _Credentials | None, optional
            The credentials to use other than the default ones
            that were provided at initialization time, by default None

        Returns
        -------
        GuacToken
        """
        credentials = credentials or self._credentials
        resp = self._client.post(self._url, data=credentials)
        token = self._check_token_response(resp)
        return GuacToken(token=token, created_at=time.time())

    def delete_token(self, token: str) -> None:
        '''
        Deletes/invalidates a token on the Guacamole server.

        Parameters
        ----------
        token : str
            _The token string to delete._
        '''
        url = f"{self._url}/{token}"
        self._client.delete(url)


def has_token_expired(token: GuacToken | None, idle_timeout: float) -> bool:
    if not token:
        return True
    elapsed = time.time() - token.created_at
    return elapsed >= idle_timeout


@dc.dataclass
class _TokenProvider:
    _idle_timeout: float
    _token: GuacToken | None

    @property
    def expired(self) -> bool:
        return has_token_expired(self._token, self._idle_timeout)


@dc.dataclass
class SyncTokenProvider(_TokenProvider):
    '''
    A thread-safe synchronous token provider that refreshes tokens on demand
    by keeping track of the token's creation time and an idle timeout.
    '''
    _client: SyncAuthClient
    _lock: threading.Lock

    @classmethod
    def from_config(cls, config: GuacamoleConfig, client: httpx.Client) -> Self:
        auth_client = SyncAuthClient.from_config(config, client)
        idle_timeout = config.idle_timeout or timedelta(minutes=5)
        return cls(
            _client=auth_client,
            _lock=threading.Lock(),
            _idle_timeout=idle_timeout.total_seconds(),
            _token=None,
        )

    def get_token(self) -> str:
        '''
        Gets a valid token, refreshing it if necessary.
        Is thread-safe.

        Returns
        -------
        str
            _The session token_

        Raises
        ------
        AuthError
            _If unable to obtain a valid token._
        '''
        with self._lock:
            if not self._token or self.expired:
                self._token = self._client.get_token()
        return self._token.token

    def close(self) -> None:
        self._client.close()


@dc.dataclass
class AsyncTokenProvider(_TokenProvider):
    _client: AsyncAuthClient
    _lock: asyncio.Lock

    @classmethod
    def from_config(cls, config: GuacamoleConfig, client: httpx.AsyncClient) -> Self:
        auth_client = AsyncAuthClient.from_config(config, client)
        idle_timeout = config.idle_timeout or timedelta(minutes=5)
        return cls(
            _client=auth_client,
            _lock=asyncio.Lock(),
            _idle_timeout=idle_timeout.total_seconds(),
            _token=None,
        )

    async def get_token(self) -> str:
        '''
        Gets a valid token, refreshing it if necessary.
        Is thread-safe.

        Returns
        -------
        str
            _The session token_

        Raises
        ------
        AuthError
            _If unable to obtain a valid token._
        '''
        async with self._lock:
            if not self._token or self.expired:
                self._token = await self._client.get_token()
        return self._token.token

    async def aclose(self) -> None:
        await self._client.aclose()




class GuacamoleSession(httpx.Auth):
    '''
    An httpx.Auth implementation that handles Guacamole token-based authentication,
    and automatically refreshes tokens as needed when they expire as long as the
    credentials don't become stale.

    It supports both synchronous and asynchronous token providers, but only one
    should be provided at initialization time. If you call the associated public
    getter for the provider that wasn't configured, a ValueError will be raised.
    '''
    requires_response_body = True

    def __init__(
        self,
        *,
        sync_backend: SyncTokenProvider | None = None,
        async_backend: AsyncTokenProvider | None = None,
    ) -> None:
        if not sync_backend and not async_backend:
            raise ValueError("Either token_provider or async_backend must be provided")

        self._sync_backend = sync_backend
        self._async_backend = async_backend

    @property
    def async_provider(self) -> AsyncTokenProvider:
        if not self._async_backend:
            raise ValueError("No async token provider configured")
        return self._async_backend

    @property
    def sync_provider(self) -> SyncTokenProvider:
        if not self._sync_backend:
            raise ValueError("No sync token provider configured")
        return self._sync_backend

    def set_token_param(self, request: httpx.Request, token: str) -> None:
        request.url = request.url.copy_add_param("token", token)

    def auth_flow(self, request: httpx.Request):
        token = self.sync_provider.get_token()
        self.set_token_param(request, token)
        response = yield request
        if response.status_code == 401:
            token = self.sync_provider.get_token()
            self.set_token_param(request, token)
            yield request

    async def async_auth_flow(self, request: httpx.Request):
        token = await self.async_provider.get_token()
        self.set_token_param(request, token)
        response = yield request
        if response.status_code == 401:
            token = await self.async_provider.get_token()
            self.set_token_param(request, token)
            yield request

    def get_provider(self) -> SyncTokenProvider | AsyncTokenProvider:
        '''
        Gets the configured token provider, either synchronous or asynchronous.

        Returns
        -------
        SyncTokenProvider | AsyncTokenProvider

        Raises
        ------
        ValueError
        '''
        if self._sync_backend:
            return self._sync_backend

        if self._async_backend:
            return self._async_backend

        raise ValueError("how did we get here?")
