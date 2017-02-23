import logging
import os

from .cache import HashCache, CacheMissException
from .ffprobe import FFprobeInfoCommand
from .field_mode_solver import FFprobeFieldModeSolver
from .factory import ffprobe_factory


class FFprobeMetadataResult:

    def __init__(self, input_url: str, info: dict, int_prog_solver: FFprobeFieldModeSolver):
        self._input_url = input_url
        self._info = info
        self._int_prog_solver = int_prog_solver
        self._av_streams_found = False
        self._v_streams_numbers = []
        self._a_streams_numbers = []
        self._field_mode = {}
        self._filename = ''
        self._filename_ext = ''

    def _find_av_streams(self):
        logging.debug('Searching for video and audio streams...')
        for n, s in enumerate(self._info['streams']):
            if s['codec_type'] == 'video':
                self._v_streams_numbers.append(n)
            elif s['codec_type'] == 'audio':
                self._a_streams_numbers.append(n)
        logging.debug('Found {} video stream(s) and {} audio stream(s)'.format(
            len(self._v_streams_numbers), len(self._a_streams_numbers)
        ))
        self._av_streams_found = True

    @property
    def v_streams(self) -> dict:
        if not self._av_streams_found:
            self._find_av_streams()
        return {self._info['streams'][n]['index']: self._info['streams'][n] for n in self._v_streams_numbers}

    @property
    def a_streams(self) -> dict:
        if not self._av_streams_found:
            self._find_av_streams()
        return {self._info['streams'][n]['index']: self._info['streams'][n] for n in self._a_streams_numbers}

    @property
    def format(self) -> dict:
        return self._info['format']

    @property
    def filename(self) -> str:
        if not self._filename:
            self._filename = os.path.splitext(self.filename_ext)[0]
        return self._filename

    @property
    def filename_ext(self) -> str:
        if not self._filename_ext:
            self._filename_ext = os.path.split(self._input_url)[1]
        return self._filename_ext

    def get_field_mode(self, stream_number: int) -> int:
        if stream_number not in self._field_mode:
            self._field_mode[stream_number] = self._int_prog_solver.solve(self._input_url, stream_number)
        return self._field_mode[stream_number]

    def __str__(self):
        return {
            'a_streams': self.a_streams,
            'filename': self.filename,
            'filename_ext': self.filename_ext,
            'format': self.format,
            'v_streams': self.v_streams,
        }


class FFprobeMetadataCollector:

    def __init__(self):
        logging.debug('Fetching FFprobeInfoCommand object...')
        self._ffprobe_info = ffprobe_factory.get_ffprobe_command(FFprobeInfoCommand)
        logging.debug('Fetching FFprobeFieldModeSolver object...')
        self._int_prog_solver = ffprobe_factory.get_ffprobe_field_mode_solver(FFprobeFieldModeSolver)
        self._cache = HashCache(10, logging.debug)

    def get_metadata(self, input_url: str) -> FFprobeMetadataResult:
        logging.debug('Trying to get file metadata from cache...')
        try:
            cached_value = self._cache.from_cache(input_url)
        except CacheMissException:
            pass
        else:
            return cached_value
        result = FFprobeMetadataResult(
            input_url,
            self._ffprobe_info.exec(input_url, show_programs=False),
            self._int_prog_solver
        )
        self._cache.to_cache(input_url, result)
        return result
