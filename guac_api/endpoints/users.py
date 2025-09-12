
from typing import Any, Literal, Sequence, TypedDict
import typing
from aiohttp.web_routedef import static
import httpx
from guac_api.request_spec import AsyncApiRouter, RequestSpec, ContentType, SyncApiRouter
from guac_api.endpoints.types import UserAttributes, UserPermissionKind, ConnectionPermission, PermissionSchema

class UsersEndpoints:
    path = '/users'

    def list_users(self) -> RequestSpec:
        return RequestSpec.get('')

    def get(self) -> RequestSpec:
        return RequestSpec.get('/{username}')

    def get_permissions(self) -> RequestSpec:
        return RequestSpec.get('/{username}/permissions')

    def get_effective_permissions(self) -> RequestSpec:
        return RequestSpec.get('/{username}/effectivePermissions')

    def get_groups(self) -> RequestSpec:
        return RequestSpec.get('/{username}/userGroups')

    def get_history(self) -> RequestSpec:
        return RequestSpec.get('/{username}/history')

    def create(self) -> RequestSpec:
        return RequestSpec.post(
            '',
            content_type=ContentType.JSON,
        )

    def update(self) -> RequestSpec:
        return RequestSpec.patch(
            '/{username}',
            content_type=ContentType.JSON,
        )

    def change_password(self) -> RequestSpec:
        return RequestSpec.patch(
            '/{username}/password',
            content_type=ContentType.JSON,
        )

    def update_group(self) -> RequestSpec:
        return RequestSpec.patch(
            '/{username}/userGroups',
            content_type=ContentType.JSON,
        )

    def delete(self) -> RequestSpec:
        return RequestSpec.delete('/{username}')

    def update_connection_permissions(self) -> RequestSpec:
        return RequestSpec.patch(
            '/{username}/permissions/connections',
            content_type=ContentType.JSON,
        )





class UserUtils:

    @staticmethod
    def get_attributes_body(attributes: UserAttributes | None) -> dict[str, Any]:
        if not attributes:
            return {}
        return {
            'disabled': attributes.get('disabled', False),
            'expired': attributes.get('expired', False),
            'access-window-start': attributes.get('access_window_start', ''),
            'access-window-end': attributes.get('access_window_end', ''),
            'valid-from': attributes.get('valid_from', ''),
            'valid-until': attributes.get('valid_until', ''),
            'timezone': attributes.get('timezone', ''),
            'guac-full-name': attributes.get('guac_full_name', ''),
            'guac-organization': attributes.get('guac_organization', ''),
            'guac-organization-role': attributes.get('guac_organization_role', '')
        }

    @staticmethod
    def get_groups_body(group_names: Sequence[str], operation: Literal['add', 'remove']) -> list[dict[str, str]]:
        return [
            {'op': operation, 'name': name, 'path': '/'}
            for name in group_names
        ]

    @staticmethod
    def get_connection_permission_path(permission_kind: ConnectionPermission) -> str:
        '''
        Gets the proper permission schema path for the given connection permission kind.

        Parameters
        ----------
        permission_kind : ConnectionPermission

        Returns
        -------
        str

        Raises
        ------
        ValueError
        '''
        match permission_kind:
            case 'connection':
                return '/connections'
            case 'group':
                return '/connectionGroups'
            case 'sharing-profile':
                return '/sharingProfiles'
            case 'active-connections':
                return '/activeConnections'
            case _:
                raise ValueError(f"Invalid permission kind: {permission_kind}")


    @staticmethod
    def get_connection_permissions_body(
        identifiers: str | list[str],
        permission_kind: ConnectionPermission,
        operation: Literal['add', 'remove'],
    ) -> list[PermissionSchema]:
        '''
        Creates a list of permission schema dictionaries for updating
        connection permissions.

        Parameters
        ----------
        identifiers : str | list[str]
        permission_kind : ConnectionPermission
        operation : Literal[&#39;add&#39;, &#39;remove&#39;]

        Returns
        -------
        list[PermissionSchema]
        '''
        if isinstance(identifiers, str):
            identifiers = [identifiers]
        path = UserUtils.get_connection_permission_path(permission_kind)

        return [
            PermissionSchema(
                op=operation,
                path=path,
                value=identifier
            )
            for identifier in identifiers
        ]

    @staticmethod
    def update_user_permission_body(
        username: str,
        permission_kind: list[UserPermissionKind],
        operation: Literal['add', 'remove'],
    ) -> list[PermissionSchema]:

        permissions = []

        for kind in permission_kind:
            path = '/systemPermissions'
            if kind == 'UPDATE':
                path = f'/userPermissions/{username}'

            permissions.append(
                PermissionSchema(
                    op=operation,
                    path=path,
                    value=kind
                )
            )


        return permissions



class SyncUserRouter(SyncApiRouter):
    def __init__(self, client: httpx.Client, session_path: str) -> None:
        super().__init__(client, path=f"{session_path}/{UsersEndpoints.path}")
        self.endpoint = UsersEndpoints()

    def list_users(self) -> dict:
        spec = self.endpoint.list_users()
        return self.request(spec)

    def get_user(self, username: str) -> dict:
        spec = self.endpoint.get()
        return self.request(spec, path_params={'username': username})

    def get_permissions(self, username: str) -> dict:
        spec = self.endpoint.get_permissions()
        return self.request(spec, path_params={'username': username})

    def get_effective_permissions(self, username: str) -> dict:
        spec = self.endpoint.get_effective_permissions()
        return self.request(spec, path_params={'username': username})

    def get_groups(self, username: str) -> dict:
        spec = self.endpoint.get_groups()
        return self.request(spec, path_params={'username': username})

    def get_history(self, username: str) -> dict:
        spec = self.endpoint.get_history()
        return self.request(spec, path_params={'username': username})

    def create_user(
        self,
        *,
        username: str,
        password: str,
        attributes: UserAttributes | None = None,
    ) -> dict:
        spec = self.endpoint.create()

        attributes = attributes or {}

        return self.request(spec, body={
            'username': username,
            'password': password,
            'attributes': UserUtils.get_attributes_body(attributes),
        })

    def update_user(
        self,
        username: str,
        *,
        attributes: UserAttributes,
    ) -> dict:
        spec = self.endpoint.update()
        return self.request(
            spec,
            path_params={'username': username},
            body={
                'username': username,
                'attributes': UserUtils.get_attributes_body(attributes),
            }
        )

    def change_password(
        self,
        *,
        username: str,
        old_password: str,
        new_password: str,
    ) -> dict:
        spec = self.endpoint.change_password()
        return self.request(
            spec,
            path_params={'username': username},
            body={
                'oldPassword': old_password,
                'newPassword': new_password,
            }
        )

    def update_group(
        self,
        *,
        username: str,
        operation: Literal['add', 'remove'],
        group_names: Sequence[str],
    ) -> dict:
        spec = self.endpoint.update_group()
        return self.request(
            spec,
            path_params={'username': username},
            body=UserUtils.get_groups_body(group_names, operation)
        )

    def delete(self, username: str) -> dict:
        spec = self.endpoint.delete()
        return self.request(spec, path_params={'username': username})

    def update_connection_permissions(
        self,
        *,
        username: str,
        permission_kind: ConnectionPermission,
        operation: Literal['add', 'remove'],
        identifiers: str | list[str],
    ) -> dict:
        spec = self.endpoint.update_connection_permissions()
        body = UserUtils.get_connection_permissions_body(
            identifiers,
            permission_kind,
            operation
        )
        return self.request(
            spec,
            path_params={'username': username},
            body=typing.cast(list[dict], body)
        )

    def update_user_permissions(
        self,
        *,
        username: str,
        permission_kind: list[UserPermissionKind],
        operation: Literal['add', 'remove'],
    ) -> dict:
        spec = self.endpoint.update_connection_permissions()
        body = UserUtils.update_user_permission_body(
            username,
            permission_kind,
            operation
        )
        return self.request(
            spec,
            path_params={'username': username},
            body=typing.cast(list[dict], body)
        )

class AsyncUserRouter(AsyncApiRouter):
    def __init__(self, client: httpx.AsyncClient, session_path: str) -> None:
        super().__init__(client, path=f"{session_path}/{UsersEndpoints.path}")
        self.endpoint = UsersEndpoints()

    async def list_users(self) -> dict:
        spec = self.endpoint.list_users()
        return await self.async_request(spec)

    async def get_user(self, username: str) -> dict:
        spec = self.endpoint.get()
        return await self.async_request(spec, path_params={'username': username})

    async def get_permissions(self, username: str) -> dict:
        spec = self.endpoint.get_permissions()
        return await self.async_request(spec, path_params={'username': username})

    async def get_effective_permissions(self, username: str) -> dict:
        spec = self.endpoint.get_effective_permissions()
        return await self.async_request(spec, path_params={'username': username})

    async def get_groups(self, username: str) -> dict:
        spec = self.endpoint.get_groups()
        return await self.async_request(spec, path_params={'username': username})

    async def get_history(self, username: str) -> dict:
        spec = self.endpoint.get_history()
        return await self.async_request(spec, path_params={'username': username})

    async def create_user(
        self,
        *,
        username: str,
        password: str,
        attributes: UserAttributes | None = None,
    ) -> dict:
        spec = self.endpoint.create()

        attributes = attributes or {}

        return await self.async_request(spec, body={
            'username': username,
            'password': password,
            'attributes': UserUtils.get_attributes_body(attributes),
        })

    async def update_user(
        self,
        username: str,
        *,
        attributes: UserAttributes,
    ) -> dict:
        spec = self.endpoint.update()
        return await self.async_request(
            spec,
            path_params={'username': username},
            body={
                'username': username,
                'attributes': UserUtils.get_attributes_body(attributes),
            }
        )

    async def change_password(
        self,
        *,
        username: str,
        old_password: str,
        new_password: str,
    ) -> dict:
        spec = self.endpoint.change_password()
        return await self.async_request(
            spec,
            path_params={'username': username},
            body={
                'oldPassword': old_password,
                'newPassword': new_password,
            }
        )

    async def update_group(
        self,
        *,
        username: str,
        operation: Literal['add', 'remove'],
        group_names: Sequence[str],
    ) -> dict:
        spec = self.endpoint.update_group()
        return await self.async_request(
            spec,
            path_params={'username': username},
            body=UserUtils.get_groups_body(group_names, operation)
        )

    async def delete(self, username: str) -> dict:
        spec = self.endpoint.delete()
        return await self.async_request(spec, path_params={'username': username})

    async def update_connection_permissions(
        self,
        *,
        username: str,
        permission_kind: ConnectionPermission,
        operation: Literal['add', 'remove'],
        identifiers: str | list[str],
    ) -> dict:
        spec = self.endpoint.update_connection_permissions()
        body = UserUtils.get_connection_permissions_body(
            identifiers,
            permission_kind,
            operation
        )
        return await self.async_request(
            spec,
            path_params={'username': username},
            body=typing.cast(list[dict], body)
        )

    async def update_user_permissions(
        self,
        *,
        username: str,
        permission_kind: list[UserPermissionKind],
        operation: Literal['add', 'remove'],
    ) -> dict:
        spec = self.endpoint.update_connection_permissions()
        body = UserUtils.update_user_permission_body(
            username,
            permission_kind,
            operation
        )
        return await self.async_request(
            spec,
            path_params={'username': username},
            body=typing.cast(list[dict], body)
        )


