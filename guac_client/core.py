from __future__ import annotations

import base64
import dataclasses as dc
import typing

import httpx



HttpMethods = typing.Literal[
    "GET",
    "HEAD",
    "POST",
    "PUT",
    "DELETE",
    "OPTIONS",
]

@dc.dataclass(slots=True, kw_only=True)
class RequestSpec:
    '''
    The template for a request to be made by the client.
    '''
    method: HttpMethods = 'GET'
    path: str
    params: dict[str, typing.Any] | None = None
    json: typing.Any | None = None
    data: typing.Any | None = None
    headers: dict[str, str] | None = None


def build_url(host: str, path_prefix: str | None, path: str) -> str:
    '''
    Construct a full URL from the host, optional path prefix,
    and request path.
    '''
    path_prefix = (path_prefix or '').rstrip('/')

    return f"{host.rstrip('/')}{path_prefix}/api/{path}"

def build_request(
    host: str,
    path_prefix: str | None,
    spec: RequestSpec,
    *,
    token: str | None = None,
) -> httpx.Request:
    '''
    Construct an httpx.Request from the given parameters.
    '''
    url = build_url(host, path_prefix, spec.path)


    headers = spec.headers or {}
    params = spec.params or {}
    if token:
        params['token'] = token

    return httpx.Request(
        method=spec.method,
        url=url,
        params=params,
        json=spec.json,
        data=spec.data,
        headers=headers,
    )

def decode_response(resp: httpx.Response) -> typing.Any:
    '''
    Decode the response content based on the Content-Type header.

    Parameters
    ----------
    resp : httpx.Response

    Returns
    -------
    typing.Any
        The decoded response content.
    '''
    if resp.status_code == 204:
        return None

    content_type = resp.headers.get("content-type", '')
    return resp.json() if 'json' in content_type else resp.text

def encode_client_url_token(
    identifier: str,
    *,
    type_: str,
    data_source: str
) -> str:
    '''
    Encode a client URL token for use in connection URLs.

    Parameters
    ----------
    identifier : str
        The identifier of the object (e.g. connection ID).
    type_ : str
        The type of the object (e.g. "c" for connection).
    data_source : str
        The data source identifier.

    Returns
    -------
    str
        The encoded client URL token.
    '''
    raw = f"{identifier}\u0000{type_}\u0000{data_source}".encode("utf-8", "strict")
    return base64.b64encode(raw).decode("ascii")