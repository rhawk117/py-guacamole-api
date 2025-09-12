

import httpx
from guac_api.request_spec import AsyncApiRouter, RequestSpec, ContentType, SyncApiRouter



class SchemaEndpoints:
    path = '/schema'

    def get_user_attributes(self) -> RequestSpec:
        return RequestSpec.get('/userAttributes')

    def get_user_group_attributes(self) -> RequestSpec:
        return RequestSpec.get('/userGroupAttributes')


    def get_connection_attributes(self) -> RequestSpec:
        return RequestSpec.get('/connectionAttributes')

    def get_sharing_profile_attributes(self) -> RequestSpec:
        return RequestSpec.get('/sharingProfileAttributes')

    def get_connection_group_attributes(self) -> RequestSpec:
        return RequestSpec.get('/connectionGroupAttributes')


class SyncSchemaRouter(SyncApiRouter):

    def __init__(self, client: httpx.Client, session_path: str) -> None:
        super().__init__(client, path=f"{session_path}/{SchemaEndpoints.path}")
        self.endpoint = SchemaEndpoints()


    def get_user_attributes(self) -> dict:
        spec = self.endpoint.get_user_attributes()
        return self.request(spec)

    def get_user_group_attributes(self) -> dict:
        spec = self.endpoint.get_user_group_attributes()
        return self.request(spec)

    def get_connection_attributes(self) -> dict:
        spec = self.endpoint.get_connection_attributes()
        return self.request(spec)

    def get_sharing_profile_attributes(self) -> dict:
        spec = self.endpoint.get_sharing_profile_attributes()
        return self.request(spec)

    def get_connection_group_attributes(self) -> dict:
        spec = self.endpoint.get_connection_group_attributes()
        return self.request(spec)

class AsyncSchemaRouter(AsyncApiRouter):
    def __init__(self, client: httpx.AsyncClient, session_path: str) -> None:
        super().__init__(client, path=f"{session_path}/{SchemaEndpoints.path}")
        self.endpoint = SchemaEndpoints()


    async def get_user_attributes(self) -> dict:
        spec = self.endpoint.get_user_attributes()
        return await self.async_request(spec)

    async def get_user_group_attributes(self) -> dict:
        spec = self.endpoint.get_user_group_attributes()
        return await self.async_request(spec)

    async def get_connection_attributes(self) -> dict:
        spec = self.endpoint.get_connection_attributes()
        return await self.async_request(spec)

    async def get_sharing_profile_attributes(self) -> dict:
        spec = self.endpoint.get_sharing_profile_attributes()
        return await self.async_request(spec)

    async def get_connection_group_attributes(self) -> dict:
        spec = self.endpoint.get_connection_group_attributes()
        return await self.async_request(spec)