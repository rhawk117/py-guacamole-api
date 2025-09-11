from .spec import RequestSpec, ResponseTypes


url = "{host}/api/scheme/data/{data_source}"


path = "/scheme"

get_users = RequestSpec(
    method='GET',
    path='/userAttributes',
    response_type=ResponseTypes.JSON,
)

get_groups = RequestSpec(
    method='GET',
    path='/groupAttributes',
    response_type=ResponseTypes.JSON,
)

get_connections = RequestSpec(
    method='GET',
    path='/connectionAttributes',
    response_type=ResponseTypes.JSON,
)

get_sharing_profiles = RequestSpec(
    method='GET',
    path='/sharingProfileAttributes',
    response_type=ResponseTypes.JSON,
)

get_connection_groups = RequestSpec(
    method='GET',
    path='/connectionGroupAttributes',
    response_type=ResponseTypes.JSON,
)

get_protocols = RequestSpec(
    method='GET',
    path='/protocols',
    response_type=ResponseTypes.JSON,
)



