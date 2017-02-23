import json


class AbstractProfileDataParser:

    def parse_profile_data(self, profile_data, **kwargs) -> dict:
        raise NotImplementedError


class JsonProfileDataParser(AbstractProfileDataParser):

    def parse_profile_data(self, profile_data, **kwargs) -> dict:
        return json.loads(profile_data)
