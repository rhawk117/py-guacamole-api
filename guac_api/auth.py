import abc
import asyncio
from datetime import timedelta
import threading
import time
from typing import TYPE_CHECKING, Generic, NamedTuple, Self, TypeVar, TypedDict

import httpx
import dataclasses as dc
from guac_api.errors import AuthError

if TYPE_CHECKING:
    from .options import ClientConfig

class GuacToken(NamedTuple):
    token: str
    created_at: float


C = TypeVar("C", bound=httpx.Client | httpx.AsyncClient)


class _Credentials(TypedDict):
    username: str
    password: str


@dc.dataclass
class _AuthClient(Generic[C]):
    """
    A base class for both the synchronous and asynchronous
    Guacamole authentication clients.
    """

    client: C
    _url: str = dc.field(init=False, default="/tokens")

    def create_token_request(self, credentials: _Credentials) -> httpx.Request:
        return self.client.build_request(
            method="POST",
            url=self._url,
            data=credentials,
        )

    def _extract_token(self, token_response: httpx.Response) -> GuacToken:
        """
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
        """
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
        return GuacToken(token=token, created_at=time.time())

    def delete_token_request(self, token: str) -> httpx.Request:
        url = f"{self._url}/{token}"
        return self.client.build_request(
            method="DELETE",
            url=url,
        )


class AsyncTokensClient(_AuthClient[httpx.AsyncClient]):
    """
    An asynchronous implementation of the Guacamole authentication client.
    """

    async def get_token(self, credentials: _Credentials) -> GuacToken:
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

        request = self.create_token_request(credentials)
        resp = await self.client.send(request)
        return self._extract_token(resp)

    async def delete_token(self, token: str | None = None) -> None:
        url = f"{self._url}/{token}"
        await self.client.delete(url)


class TokensClient(_AuthClient[httpx.Client]):
    def get_token(self, credentials: _Credentials) -> GuacToken:
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
        request = self.create_token_request(credentials)
        resp = self.client.send(request)
        return self._extract_token(resp)

    def delete_token(self, token: str) -> None:
        """
        Deletes/invalidates a token on the Guacamole server.

        Parameters
        ----------
        token : str
            _The token string to delete._
        """
        url = f"{self._url}/{token}"
        self.client.delete(url)




def has_token_expired(token: GuacToken | None, idle_timeout: float) -> bool:
    """
    Checks if a token has expired based on its creation time and the idle timeout.

    Parameters
    ----------
    token : GuacToken
        The token to check.
    idle_timeout : float
        The idle timeout in seconds.

    Returns
    -------
    bool
        True if the token has expired, False otherwise.
    """
    if not token:
        return True

    elapsed = time.time() - token.created_at
    return elapsed >= idle_timeout


class GuacamoleSession(httpx.Auth):
    requires_response_body = True

    def __init__(
        self,
        crendetials: _Credentials,
        tokens_client: TokensClient,
        *,
        idle_timeout: timedelta | None = None,
    ) -> None:
        idle_timeout = idle_timeout or timedelta(minutes=5)
        self._idle_timeout: float = idle_timeout.total_seconds()
        self._credentials = crendetials
        self.token: GuacToken | None = None
        self._lock: threading.Lock = threading.Lock()
        self._tokens_client: TokensClient = tokens_client

    def set_token_param(self, request: httpx.Request, token: str) -> None:
        request.url = request.url.copy_add_param("token", token)

    def _touch(self) -> None:
        """
        Updates the token's creation time to the current time,
        effectively resetting the idle timeout.
        """
        if self.token:
            self.token = GuacToken(
                token=self.token.token,
                created_at=time.time()
            )

    def get_token(self) -> str:
        with self._lock:
            if has_token_expired(self.token, self._idle_timeout):
                self.token = self._tokens_client.get_token(self._credentials)
            else:
                self._touch()

        return self.token.token # type: ignore[return-value]

    def auth_flow(self, request: httpx.Request):
        token = self.get_token()
        self.set_token_param(request, token)
        response = yield request
        if response.status_code == 401:
            token = self.get_token()
            self.set_token_param(request, token)
            yield request

    @classmethod
    def from_credentials(
        cls,
        guac_host: str,
        *,
        credentials: _Credentials,
        client_config: ClientConfig | None = None,
        idle_timeout: timedelta | None = None,
    ) -> Self:
        client_config = client_config or ClientConfig()
        client_kwargs = dc.asdict(client_config)
        client_kwargs['base_url'] = guac_host.rstrip('/')

        tokens_client = TokensClient(
            client=httpx.Client(**client_kwargs)
        )
        return cls(
            crendetials=credentials,
            tokens_client=tokens_client,
            idle_timeout=idle_timeout,
        )

    def dispose(self) -> None:
        self._tokens_client.client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args) -> None:
        self.dispose()

class AsyncGuacamoleSession(httpx.Auth):
    requires_response_body = True

    def __init__(
        self,
        credentials: _Credentials,
        tokens_client: AsyncTokensClient,
        *,
        idle_timeout: timedelta | None = None,
    ) -> None:
        idle_timeout = idle_timeout or timedelta(minutes=5)
        self._idle_timeout: float = idle_timeout.total_seconds()
        self._credentials = credentials
        self.token: GuacToken | None = None
        self._lock: asyncio.Lock = asyncio.Lock()
        self._tokens_client: AsyncTokensClient = tokens_client

    def set_token_param(self, request: httpx.Request, token: str) -> None:
        request.url = request.url.copy_add_param("token", token)

    async def _touch(self) -> None:
        """
        Updates the token's creation time to the current time,
        effectively resetting the idle timeout.
        """
        if self.token:
            self.token = GuacToken(
                token=self.token.token,
                created_at=time.time()
            )

    async def get_token(self) -> str:
        async with self._lock:
            if has_token_expired(self.token, self._idle_timeout):
                self.token = await self._tokens_client.get_token(self._credentials)
            else:
                await self._touch()

        return self.token.token # type: ignore[return-value]

    async def auth_flow(self, request: httpx.Request):
        token = await self.get_token()
        self.set_token_param(request, token)
        response = yield request
        if response.status_code == 401:
            token = await self.get_token()
            self.set_token_param(request, token)
            yield request

    @classmethod
    def from_credentials(
        cls,
        guac_host: str,
        *,
        credentials: _Credentials,
        client_config: ClientConfig | None = None,
        idle_timeout: timedelta | None = None,
    ) -> Self:
        client_config = client_config or ClientConfig()
        client_kwargs = dc.asdict(client_config)
        client_kwargs['base_url'] = guac_host.rstrip('/')

        tokens_client = AsyncTokensClient(
            client=httpx.AsyncClient(**client_kwargs)
        )
        return cls(
            credentials=credentials,
            tokens_client=tokens_client,
            idle_timeout=idle_timeout,
        )