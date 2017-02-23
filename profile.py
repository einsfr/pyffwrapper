

class FFmpegProfile:

    def __init__(self, profile_dict: dict):
        self._profile_dict = profile_dict

    @property
    def inputs(self):
        return self._profile_dict['inputs']

    @property
    def outputs(self):
        return self._profile_dict['outputs']
