


from dataclasses import dataclass
from enum import IntEnum
from .spec import RequestSpec, ResponseTypes

url = ''

get_patches = RequestSpec(
    method='GET',
    path='/patches',
    response_type=ResponseTypes.JSON,
)

get_languages = RequestSpec(
    method='GET',
    path='/languages',
    response_type=ResponseTypes.JSON,
)

get_session_extensions = RequestSpec(
    method='GET',
    path='/session/ext/{data_source}',
)






