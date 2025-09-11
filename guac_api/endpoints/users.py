

from .spec import RequestSpec, ResponseTypes



path = '/users'

create_user = RequestSpec(
    method="POST",
    path="",
    response_type=ResponseTypes.JSON,
)

get_user = RequestSpec(
    method='GET',
    path='/{username}',
    response_type=ResponseTypes.JSON,
)

update_user = RequestSpec(
    method='PUT',
    path='/{username}',
    response_type=ResponseTypes.JSON,
)

update_user_password = RequestSpec(
    method='PUT',
    path='/{username}/password',
    response_type=ResponseTypes.JSON,
)

update_user_group = RequestSpec(
    method='PUT',
    path='/{username}/userGroups',
    response_type=ResponseTypes.JSON,
)




get_user_permissions = RequestSpec(
    method='GET',
    path='/{username}/permissions',
    response_type=ResponseTypes.JSON,
)

get_user_effective_permissions = RequestSpec(
    method='GET',
    path='/{username}/effectivePermissions',
    response_type=ResponseTypes.JSON,
)

get_user_groups = RequestSpec(
    method='GET',
    path='/{username}/groups',
    response_type=ResponseTypes.JSON,
)

get_user_history = RequestSpec(
    method='GET',
    path='/{username}/history',
    response_type=ResponseTypes.JSON,
)

# session_url/self
get_current_user = RequestSpec(
    method='GET',
    path='/',
    response_type=ResponseTypes.JSON,
)




