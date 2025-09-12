
import httpx
from guac_api.request_spec import AsyncApiRouter, RequestSpec, SyncApiRouter



class HistoryEndpoint:
    path = '/history'

    def get_users(self) -> RequestSpec:
        return RequestSpec.get("/users")

    def get_connections(self) -> RequestSpec:
        return RequestSpec.get("/connections")


class SyncHistoryRouter(SyncApiRouter):
    def __init__(self, client: httpx.Client) -> None:
        super().__init__(client, path=HistoryEndpoint.path)
        self.endpoint = HistoryEndpoint()

    def get_users(self) -> dict:
        spec = self.endpoint.get_users()
        return self.request(spec)

    def get_connections(self) -> dict:
        spec = self.endpoint.get_connections()
        return self.request(spec)

class AsyncHistoryRouter(AsyncApiRouter):
    def __init__(self, client: httpx.AsyncClient, session_path: str) -> None:
        super().__init__(client, path=f"{session_path}/{HistoryEndpoint.path}")
        self.endpoint = HistoryEndpoint()

    async def get_users(self) -> dict:
        spec = self.endpoint.get_users()
        return await self.async_request(spec)

    async def get_connections(self) -> dict:
        spec = self.endpoint.get_connections()
        return await self.async_request(spec)
