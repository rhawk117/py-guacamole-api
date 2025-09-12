

import contextlib
import dataclasses as dc
from datetime import timedelta
import enum
import time
from typing import Generic, Literal, Self, TypeVar, TypedDict, Unpack
import urllib
import urllib.parse
import httpx
from guac_api.errors import raise_for_response


class SessionToken:

    def __init__(self, idle_timeout: timedelta | None) -> None:
        self._token: str | None = None
        self._created_at: float = -1
        idle_timeout = idle_timeout or timedelta(minutes=5)
        self.idle_timeout: float = idle_timeout.total_seconds()

    def _has_expired(self) -> bool:
        if self._created_at < 0:
            return True
        if self.idle_timeout <= 0:
            return False
        return (time.time() - self._created_at) > self.idle_timeout

    def touch(self) -> None:
        self._created_at = time.time()

    def get_token(self) -> str | None:
        if self._has_expired():
            self._token = None
        return self._token

    def set_token(self, token: str) -> None:
        self._token = token
        self._created_at = time.time()


HTTPMethods = Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH']


class ContentType(enum.Enum):
    JSON = 'application/json'
    FORM = 'application/x-www-form-urlencoded'
    MULTIPART = 'multipart/form-data'
    UNSET = ''


def build_path(
    base_path: str,
    path_params: dict[str, str] | None = None,
) -> str:
    '''
    Build a URL path by substituting path parameters into the base path.

    Parameters
    ----------
    base_path : str
    path_params : dict[str, str] | None, optional

    Returns
    -------
    str

    Raises
    ------
    ValueError
    '''
    if not path_params:
        return base_path

    try:
        escaped_params = {k: urllib.parse.quote(
            v, safe='') for k, v in path_params.items()}
        return base_path.format(**escaped_params)
    except KeyError as e:
        raise ValueError(f"Missing path parameter: {e}") from e


class RequestParams(TypedDict, total=False):
    path_params: dict[str, str]
    body: dict | list[dict]
    form: dict[str, str]
    query_params: dict[str, str]

class RequestOptions(TypedDict, total=False):
    timeout: float
    headers: dict[str, str]


@dc.dataclass(slots=True)
class RequestSpec:
    _method: HTTPMethods
    path: str
    content_type: ContentType = ContentType.UNSET

    def create_request(
        self,
        client: httpx.Client | httpx.AsyncClient,
        router_path: str = '',
        **params: Unpack[RequestParams],
    ) -> httpx.Request:

        body = params.get('body')
        form = params.get('form')

        if self._method == 'GET' and bool(body or form):
            raise ValueError("GET requests cannot have a body or form data")

        path = router_path + self.path
        path = build_path(path, params.get('path_params'))

        headers = {}
        if self.content_type != ContentType.UNSET:
            headers['Content-Type'] = self.content_type.value

        return client.build_request(
            url=path,
            method=self._method,
            params=params.get('query_params'),
            json=body if self.content_type == ContentType.JSON else None,
            data=form if self.content_type == ContentType.FORM else None,
        )

    @classmethod
    def get(
        cls,
        path: str,
        *,
        content_type: ContentType = ContentType.UNSET,
    ) -> Self:
        return cls(
            _method='GET',
            path=path,
            content_type=content_type
        )

    @classmethod
    def post(
        cls,
        path: str,
        *,
        content_type: ContentType = ContentType.JSON,
    ) -> Self:
        return cls(
            _method='POST',
            path=path,
            content_type=content_type
        )

    @classmethod
    def put(
        cls,
        path: str,
        *,
        content_type: ContentType = ContentType.JSON,
    ) -> Self:
        return cls(
            _method='PUT',
            path=path,
            content_type=content_type
        )

    @classmethod
    def delete(
        cls,
        path: str,
        *,
        content_type: ContentType = ContentType.UNSET,
    ) -> Self:
        return cls(
            _method='DELETE',
            path=path,
            content_type=content_type
        )

    @classmethod
    def patch(
        cls,
        path: str,
        *,
        content_type: ContentType = ContentType.JSON,
    ) -> Self:
        return cls(
            _method='PATCH',
            path=path,
            content_type=content_type
        )


C = TypeVar('C', httpx.Client, httpx.AsyncClient)


class ApiRouter(Generic[C]):
    '''
    Base class for HTTP backends.
    '''

    def __init__(
        self,
        client: C,
        *,
        path: str = '',
    ) -> None:
        self._client: C = client
        self.path: str = path

    def get_response_json(self, response: httpx.Response) -> dict:
        raise_for_response(response)
        if response.status_code == 204:
            return {}
        try:
            return response.json()
        except ValueError as e:
            raise ValueError("Response content is not valid JSON") from e


    def request(self, spec: RequestSpec, **params: Unpack[RequestParams]) -> httpx.Response:
        raise NotImplementedError


    async def async_request(self, spec: RequestSpec, **params: Unpack[RequestParams]) -> httpx.Response:
        raise NotImplementedError





class SyncApiRouter(ApiRouter[httpx.Client]):
    def request(self, spec: RequestSpec, **params: Unpack[RequestParams]) -> dict:
        request = spec.create_request(
            self._client,
            self.path,
            **params
        )
        try:
            response = self._client.send(request)
        except httpx.HTTPError as e:
            raise ConnectionError("HTTP request failed") from e
        return self.get_response_json(response)




class AsyncApiRouter(ApiRouter[httpx.AsyncClient]):
    async def async_request(self, spec: RequestSpec, **params: Unpack[RequestParams]) -> dict:
        request = spec.create_request(
            self._client,
            self.path,
            **params
        )
        try:
            response = await self._client.send(request)
        except httpx.HTTPError as e:
            raise ConnectionError("HTTP request failed") from e
        return self.get_response_json(response)