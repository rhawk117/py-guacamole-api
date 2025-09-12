


from dataclasses import dataclass
from enum import IntEnum

from httpx._client import Client
from guac_api.request_spec import RequestSpec, ContentType, SyncApiRouter



class RootEndpoints:
    path = ''

    def get_patches(self) -> RequestSpec:
        return RequestSpec.get('/patches')

    def get_languages(self) -> RequestSpec:
        return RequestSpec.get('/languages')

    def get_extensions(self) -> RequestSpec:
        return RequestSpec.get('/session/ext/{data_source}')




class SyncRootRouter(SyncApiRouter):
    endpoints = RootEndpoints()

    def __init__(
        self,
        client: Client,
        data_source: str
    ) -> None:
        super().__init__(client, path=RootEndpoints.path)
        self.data_source = data_source

    def get_patches(self) -> dict:
        spec = self.endpoints.get_patches()
        return self.request(spec)

    def get_languages(self) -> dict:
        spec = self.endpoints.get_languages()
        return self.request(spec)

    def get_extensions(self) -> dict:
        spec = self.endpoints.get_extensions()
        return self.request(spec, path_params={'data_source': self.data_source})


