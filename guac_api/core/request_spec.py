


import contextlib
import dataclasses as dc
from datetime import timedelta
import enum
import time
from typing import Generic, Literal, Self, TypeVar, TypedDict, Unpack
import urllib
import urllib.parse
import httpx








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
        escaped_params = {k: urllib.parse.quote(v, safe='') for k, v in path_params.items()}
        return base_path.format(**escaped_params)
    except KeyError as e:
        raise ValueError(f"Missing path parameter: {e}") from e



class RequestParams(TypedDict, total=False):
    path_params: dict[str, str]
    body: dict
    form: dict[str, str]
    query_params: dict[str, str]
    timeout: float


@dc.dataclass(slots=True)
class RequestSpec:
    _method: HTTPMethods
    path: str
    content_type: ContentType = ContentType.UNSET


    def create_request(
        self,
        client: httpx.Client | httpx.AsyncClient,
        **params: Unpack[RequestParams]
    ) -> httpx.Request:

        body = params.get('body')
        form = params.get('form')

        if self._method == 'GET' and bool(body or form):
            raise ValueError("GET requests cannot have a body or form data")


        path = build_path(self.path, params.get('path_params'))

        return client.build_request(
            url=path,
            method=self._method,
            params=params.get('query_params'),
            json=body if self.content_type == ContentType.JSON else None,
            data=form if self.content_type == ContentType.FORM else None,
            timeout=params.get('timeout'),
        )

    @classmethod
    def get(
        cls,
        *,
        path: str,
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
        *,
        path: str,
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
        *,
        path: str,
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
        *,
        path: str,
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
        *,
        path: str,
        content_type: ContentType = ContentType.JSON,
    ) -> Self:
        return cls(
            _method='PATCH',
            path=path,
            content_type=content_type
        )





C = TypeVar('C', httpx.Client, httpx.AsyncClient)

class HttpBackend(Generic[C]):


    def __init__(
        self,
        client: C,
        *,
        path: str = '',
    ) -> None:
        self._client: C = client
        self.path: str = path

    def build_request(
        self,
        spec: RequestSpec,
        **params: Unpack[RequestParams]
    ) -> httpx.Request:
        return spec.create_request(self._client, **params)

    def send_sync( self, request: httpx.Request) -> httpx.Response:
        raise NotImplementedError

    def stream(self, request: httpx.Request) -> httpx.Response:
        raise NotImplementedError

    async def send_async(self, request: httpx.Request) -> httpx.Response:
        raise NotImplementedError

    async def stream_async(self, request: httpx.Request) -> httpx.Response:
        raise NotImplementedError


class SyncRequestBackend(HttpBackend[httpx.Client]):
    def send_sync(self, request: httpx.Request) -> httpx.Response:
        return self._client.send(request)

    @contextlib.contextmanager
    def stream(self, request: httpx.Request) :
        with self._client.stream(
            request.method,
            request.url,
            headers=request.headers,
            params=request.url.params,
            content=request.content,
        ) as response:
            yield response

    def __call__(self, spec: RequestSpec, **params: Unpack[RequestParams]) -> httpx.Response:
        request = self.build_request(spec, **params)
        return self.send_sync(request)



class AsyncRequestBackend(HttpBackend[httpx.AsyncClient]):
    async def send_async(self, request: httpx.Request) -> httpx.Response:
        return await self._client.send(request)

    @contextlib.asynccontextmanager
    async def stream_async(self, request: httpx.Request) :
        async with self._client.stream(
            request.method,
            request.url,
            headers=request.headers,
            params=request.url.params,
            content=request.content,
        ) as response:
            yield response

    async def __call__(self, spec: RequestSpec, **params: Unpack[RequestParams]) -> httpx.Response:
        request = self.build_request(spec, **params)
        return await self.send_async(request)




