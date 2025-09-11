from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Mapping, TypedDict


class ResponseTypes(IntEnum):
    JSON = 1
    TEXT = 2
    BYTES = 3
    RAW = 4
    NONE = 5

class RequestParams(TypedDict, total=False):
    query: Mapping[str, Any]
    path: Mapping[str, Any]
    headers: Mapping[str, str]
    body: Any
    form: Mapping[str, Any]


@dataclass(slots=True)
class RequestSpec:
    method: str
    path: str
    headers: Mapping[str, str] | None = None
    timeout: float | None = None
    response_type: ResponseTypes = ResponseTypes.JSON





