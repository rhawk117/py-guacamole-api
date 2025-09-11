
from .spec import RequestSpec, ResponseTypes


path = '/history'

get_users_history = RequestSpec(
    method='GET',
    path='/users',
    response_type=ResponseTypes.JSON,
)

get_connections_history = RequestSpec(
    method='GET',
    path='/connections',
    response_type=ResponseTypes.JSON,
)

get_active_connections = RequestSpec(
    method='GET',
    path='/',
    response_type=ResponseTypes.JSON,
)

