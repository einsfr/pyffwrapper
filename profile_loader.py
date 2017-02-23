import logging
import jsonschema

from .profile_data_parser import AbstractProfileDataParser
from .profile_data_provider import AbstractProfileDataProvider
from .profile import FFmpegProfile


profile_loader = None


class ProfileLoader:

    PROFILE_SCHEMA = {
        'title': 'Profile',
        'type': 'object',
        'properties': {
            'inputs': {
                'title': 'Profile inputs list',
                'type': 'array',
                'items': {
                    'title': 'Profile input',
                    'type': 'object',
                    'properties': {
                        'parameters': {
                            'title': 'Profile input\'s parameters',
                            'type': 'array',
                            'items': {
                                'title': 'Profile input\'s parameter',
                                'type': 'string'
                            }
                        }
                    },
                    'required': ['parameters', ]
                },
                'minItems': 1
            },
            'outputs': {
                'title': 'Profile outputs list',
                'type': 'array',
                'items': {
                    'title': 'Profile output',
                    'type': 'object',
                    'properties': {
                        'parameters': {
                            'title': 'Profile output\'s parameters',
                            'type': 'array',
                            'items': {
                                'title': 'Profile output\'s parameter',
                                'type': 'string'
                            }
                        },
                        'filename': {
                            'title': 'Profile output\'s filename',
                            'type': 'string'
                        }
                    },
                    'required': ['parameters', 'filename', ]
                },
                'minItems': 1
            }
        },
        'required': ['inputs', 'outputs']
    }

    def __init__(self, data_provider: AbstractProfileDataProvider,
                 data_parser: AbstractProfileDataParser):
        self._data_provider = data_provider
        self._data_parser = data_parser

    def get_profile(self, profile_name: str, **kwargs) -> FFmpegProfile:
        profile_data = self._data_provider.get_profile_data(profile_name, **kwargs)
        profile_dict = self._data_parser.parse_profile_data(profile_data)
        self._validate_profile(profile_dict)
        return FFmpegProfile(profile_dict)

    @classmethod
    def _validate_profile(cls, profile_dict):
        logging.debug('Validating profile...')
        jsonschema.validate(profile_dict, cls.PROFILE_SCHEMA)
