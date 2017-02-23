import logging

from .ffprobe import FFprobeFrameCommand
from .cache import HashCache, CacheMissException
from .factory import ffprobe_factory


class AbstractFieldModeSolver:

    IS_MIXED_OR_UNKNOWN = 0
    IS_INTERLACED_TFF = 1
    IS_INTERLACED_BFF = 2
    IS_PROGRESSIVE = 3

    DECISIONS = {
        IS_MIXED_OR_UNKNOWN: 'MIXED OR UNKNOWN',
        IS_INTERLACED_TFF: 'INTERLACED TFF',
        IS_INTERLACED_BFF: 'INTERLACED BFF',
        IS_PROGRESSIVE: 'PROGRESSIVE'
    }

    def solve(self, input_url: str, video_stream_number: int) -> int:
        raise NotImplementedError


class FFprobeFieldModeSolver(AbstractFieldModeSolver):

    READ_INTERVALS = '%+#10'

    def __init__(self):
        self._ffprobe_frame_cmd = ffprobe_factory.get_ffprobe_command(FFprobeFrameCommand)
        self._cache = HashCache(10, logging.debug)

    def _solve(self, total_count: int, tff_counf: int, bff_count: int, progressive_count: int) -> int:
        if tff_counf == total_count:
            return self.IS_INTERLACED_TFF
        if bff_count == total_count:
            return self.IS_INTERLACED_BFF
        if progressive_count == total_count:
            return self.IS_PROGRESSIVE
        return self.IS_MIXED_OR_UNKNOWN

    @staticmethod
    def _collect(v_frame_list: list) -> tuple:
        tff_count = 0
        bff_count = 0
        progressive_count = 0
        total_count = len(v_frame_list)
        for f in v_frame_list:
            if f['interlaced_frame'] == 1:
                if f['top_field_first'] == 1:
                    tff_count += 1
                else:
                    bff_count += 1
            else:
                if f['top_field_first'] == 1:
                    tff_count += 1
                else:
                    progressive_count += 1
        return total_count, tff_count, bff_count, progressive_count

    def solve(self, input_url: str, video_stream_number: int) -> int:
        cache_id = '{}{}'.format(input_url, video_stream_number)
        logging.debug('Trying to get field mode from cache...')
        try:
            result = self._cache.from_cache(cache_id)
        except CacheMissException:
            pass
        else:
            return result
        logging.info('Decoding some frames to determine video stream field mode...')
        v_frame_list = self._ffprobe_frame_cmd.exec(
            input_url,
            'v:{}'.format(video_stream_number),
            self.READ_INTERVALS
        )['frames']
        collected = self._collect(v_frame_list)
        logging.debug('FFprobe result: total - {}, tff count - {}, bff count - {}, progressive count - {}'.format(
            *collected
        ))
        decision = self._solve(*collected)
        logging.info('Stream determined as {}'.format(self.DECISIONS[decision]))
        self._cache.to_cache(cache_id, decision)
        return decision
