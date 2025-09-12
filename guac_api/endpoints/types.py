

from typing import Literal, TypedDict


class UserAttributes(TypedDict, total=False):
    disabled: bool
    expired: bool
    access_window_start: str
    access_window_end: str
    valid_from: str
    valid_until: str
    timezone: str
    guac_full_name: str
    guac_organization: str
    guac_organization_role: str


ConnectionPermission = Literal[
    'connection',
    'group',
    'sharing-profile',
    'active-connections'
]
UserPermissionKind = Literal[
    'ADMINSTER', 'CREATE_USER', 'CREATE_USER_GROUP',
    'CREATE_CONNECTION', 'CREATE_CONNECTION_GROUP',
    'CREATE_SHARING_PROFILE', 'UPDATE'
]


class PermissionSchema(TypedDict):
    op: Literal['add', 'remove']
    value: str
    path: str
