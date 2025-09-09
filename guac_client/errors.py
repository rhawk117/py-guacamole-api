from __future__ import annotations
import httpx


class GuacError(Exception):
    """Base package exception."""


class HttpError(GuacError):
    """
    Errors raised from HTTP requests in the API client
    with details that can be programmatically inspected /
    excepted.
    """


    def __init__(
        self,
        status: int,
        detail: str,
        code: str | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        self.status: int = status
        self.detail: str = detail
        self.code: str | None = code
        self.response: httpx.Response | None = response
        super().__init__(f"HTTP {status}, {detail}" + (f" (code={code})" if code else ""))

class AuthError(HttpError): ...


class PermissionError(HttpError): ...


class NotFoundError(HttpError): ...


class RateLimitError(HttpError): ...


class ServerError(HttpError): ...


class DecodeError(HttpError): ...


class TransportError(HttpError): ...


class TokenRefreshError(HttpError): ...


def get_error_by_status(status: int) -> type[HttpError]:
    '''
    Get the appropriate exception class for a given HTTP status code.

    Parameters
    ----------
    status : int

    Returns
    -------
    type[HttpError]
    '''
    match status:
        case 401:
            return AuthError
        case 403:
            return PermissionError
        case 404:
            return NotFoundError
        case 408 | 429:
            return RateLimitError
        case s if 500 <= s < 600:
            return ServerError
        case _:
            return HttpError


def raise_for_response(resp: httpx.Response) -> None:
    '''
    Raise an appropriate exception for a given HTTP response.

    Parameters
    ----------
    resp : httpx.Response

    Raises
    ------
    exception_cls
    '''
    if 200 <= resp.status_code < 300:
        return

    try:
        data = resp.json()
        code = data.get("code") or str(resp.status_code)
        detail: str = data.get("message") or data.get("error") or resp.text
    except Exception:
        detail = resp.text or f"Guacamole API Request Failed, HTTP {resp.status_code}"
        code = str(resp.status_code)

    kwargs = {
        'status': resp.status_code,
        'detail': detail,
        'code': code,
        'response': resp,
    }

    exception_cls = get_error_by_status(resp.status_code)
    raise exception_cls(**kwargs)


