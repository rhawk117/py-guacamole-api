
import httpx
from guac_api.request_spec import AsyncApiRouter, RequestSpec, ContentType, SyncApiRouter




class SharingProfileEndpoints:
    path = '/sharingProfiles'

    def get_sharing_profiles(self) -> RequestSpec:
        return RequestSpec.get('')

    def create_sharing_profile(self) -> RequestSpec:
        return RequestSpec.post('', content_type=ContentType.JSON)

    def update_sharing_profile(self) -> RequestSpec:
        return RequestSpec.post('/{sharing_profile_id}', content_type=ContentType.JSON)

    def delete_sharing_profile(self) -> RequestSpec:
        return RequestSpec.delete('/{sharing_profile_id}')

    def get_parameters(self) -> RequestSpec:
        return RequestSpec.get('/{sharing_profile_id}/parameters')

class SyncSharingProfileRouter(SyncApiRouter):
    def __init__(self, client: httpx.Client, session_path: str) -> None:
        super().__init__(client, path=f"{session_path}/{SharingProfileEndpoints.path}")
        self.endpoint = SharingProfileEndpoints()

    def get_sharing_profiles(self) -> dict:
        spec = self.endpoint.get_sharing_profiles()
        return self.request(spec)

    def create_sharing_profile(
        self,
        primary_identifier: str,
        name: str,
        read_only: bool = False
    ) -> dict:
        spec = self.endpoint.create_sharing_profile()
        return self.request(spec, body={
            'primaryConnectionIdentifier': primary_identifier,
            'name': name,
            'parameters': {
                'read-only': str(read_only).lower()
            },
            'attributes': {}
        })

    def update_sharing_profile(
        self,
        identifier: str,
        *,
        primary_identifier: str,
        name: str,
        read_only: bool = False
    ) -> dict:
        spec = self.endpoint.update_sharing_profile()
        return self.request(spec, path_params={'sharing_profile_id': identifier}, body={
            'primaryConnectionIdentifier': primary_identifier,
            'name': name,
            'parameters': {
                'read-only': str(read_only).lower()
            },
            'attributes': {}
        })

    def delete_sharing_profile(self, identifier: str) -> None:
        spec = self.endpoint.delete_sharing_profile()
        self.request(spec, path_params={'sharing_profile_id': identifier})

    def get_parameters(self, identifier: str) -> dict:
        spec = self.endpoint.get_parameters()
        return self.request(spec, path_params={'sharing_profile_id': identifier})


class AsyncSharingProfileRouter(AsyncApiRouter):
    def __init__(self, client: httpx.AsyncClient, session_path: str) -> None:
        super().__init__(client, path=f"{session_path}/{SharingProfileEndpoints.path}")
        self.endpoint = SharingProfileEndpoints()

    async def get_sharing_profiles(self) -> dict:
        spec = self.endpoint.get_sharing_profiles()
        return await self.async_request(spec)

    async def create_sharing_profile(
        self,
        *,
        primary_identifier: str,
        name: str,
        read_only: bool = False
    ) -> dict:
        spec = self.endpoint.create_sharing_profile()
        return await self.async_request(spec, body={
            'primaryConnectionIdentifier': primary_identifier,
            'name': name,
            'parameters': {
                'read-only': str(read_only).lower()
            },
            'attributes': {}
        })

    async def update_sharing_profile(
        self,
        identifier: str,
        *,
        primary_identifier: str,
        name: str,
        read_only: bool = False
    ) -> dict:
        spec = self.endpoint.update_sharing_profile()
        return await self.async_request(spec, path_params={'sharing_profile_id': identifier}, body={
            'primaryConnectionIdentifier': primary_identifier,
            'name': name,
            'parameters': {
                'read-only': str(read_only).lower()
            },
            'attributes': {}
        })

    async def delete_sharing_profile(self, identifier: str) -> None:
        spec = self.endpoint.delete_sharing_profile()
        await self.async_request(spec, path_params={'sharing_profile_id': identifier})

    async def get_parameters(self, identifier: str) -> dict:
        spec = self.endpoint.get_parameters()
        return await self.async_request(spec, path_params={'sharing_profile_id': identifier})