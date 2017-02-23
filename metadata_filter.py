import logging
import re

from .metadata_collector import FFprobeMetadataCollector, FFprobeMetadataResult
from .exceptions import UnknownFilterSelector, UnknownMetadataParameter, WrongConditionType, UnknownOperator,\
    ConditionPairProcessingException, UnknownStreamType, StreamIndexOutOfRange
from .factory import ffprobe_factory


class FFprobeMetadataFilter:

    STREAM_SELECTOR_RE = r'^stream:(v|a):(\d+)$'
    COUNT_SELECTOR_RE = r'^count:(v|a)$'

    def __init__(self):
        logging.debug('Fetching FFprobeMetadataCollector object...')
        self._ff_metadata_collector = ffprobe_factory.get_ffprobe_metadata_collector(FFprobeMetadataCollector)
        self._stream_selector_re = re.compile(self.STREAM_SELECTOR_RE, re.IGNORECASE)
        self._count_selector_re = re.compile(self.COUNT_SELECTOR_RE, re.IGNORECASE)

    def filter(self, input_url: str, filter_params: dict) -> bool:
        logging.debug('Filtering started with parameters: {}'.format(filter_params))
        input_meta = self._ff_metadata_collector.get_metadata(input_url)
        for selector, selector_data in filter_params.items():
            logging.debug('Processing selector "{}"...'.format(selector))
            result = False
            if selector.lower() == 'format':
                logging.debug('This is a format selector')
                result = self._filter_format(input_meta, selector_data)
            else:
                matched = False

                match = self._stream_selector_re.match(selector)
                if match:
                    logging.debug('This is a stream selector')
                    matched = True
                    result = self._filter_stream(*match.groups(), input_meta, selector_data)

                match = self._count_selector_re.match(selector)
                if match:
                    logging.debug('This is a count selector')
                    matched = True
                    result = self._filter_count(*match.groups(), input_meta, selector_data)

                if not matched:
                    raise UnknownFilterSelector(selector)
            if result:
                logging.debug('Passed')
            else:
                logging.debug('Failed')
                return False
        logging.debug('Filter passed')
        return True

    def _filter_format(self, input_meta: FFprobeMetadataResult, selector_data: dict) -> bool:
        format_data = input_meta.format
        for param, condition in selector_data.items():
            try:
                param_value = format_data[param]
                logging.debug('Format parameter name: {}, value: {}, condition: {}'.format(
                    param, param_value, condition))
            except KeyError as e:
                raise UnknownMetadataParameter(param) from e
            if not self._process_condition(param_value, condition):
                return False
        return True

    def _filter_stream(self, s_type: str, s_index: str, input_meta: FFprobeMetadataResult, selector_data) -> bool:
        s_index = int(s_index)
        try:
            all_streams_data = getattr(input_meta, '{}_streams'.format(s_type))
        except AttributeError as e:
            raise UnknownStreamType(s_type) from e
        if len(all_streams_data) < s_index:
            raise StreamIndexOutOfRange(s_index)
        stream_data = all_streams_data[s_index]
        for param, condition in selector_data.items():
            try:
                param_value = stream_data[param]
                logging.debug('Stream parameter name: {}, value: {}, condition: {}'.format(
                    param, param_value, condition))
            except KeyError as e:
                if param == 'field_mode':
                    param_value = input_meta.get_field_mode(s_index)
                    logging.debug('Stream field mode is {}, condition: {}'.format(param_value, condition))
                else:
                    raise UnknownMetadataParameter(param) from e
            if not self._process_condition(param_value, condition):
                return False
        return True

    def _filter_count(self, s_type: str, input_meta: FFprobeMetadataResult, selector_data) -> bool:
        if s_type == 'v':
            vs_count = len(input_meta.v_streams)
            logging.debug('Video streams count: {}, condition: {}'.format(vs_count, selector_data))
            return self._process_condition(vs_count, selector_data)
        elif s_type == 'a':
            as_count = len(input_meta.a_streams)
            logging.debug('Audio streams count: {}, condition: {}'.format(as_count, selector_data))
            return self._process_condition(as_count, selector_data)
        else:
            raise UnknownStreamType(s_type)

    def _process_condition(self, value, condition) -> bool:
        t = type(condition)
        if t in [int, float, str]:
            logging.debug('Condition is a simple value')
            return self._process_cond_pair(value, 'eq', condition)
        elif t == list:
            if type(condition[0]) == str:
                logging.debug('Condition is a [operator, value] list')
                return self._process_cond_pair(value, *condition)
            elif type(condition[0]) == list:
                logging.debug('Condition is a list of [operator, value] lists')
                return all(map(lambda x: self._process_cond_pair(value, *x), condition))
        else:
            raise WrongConditionType(type(condition))

    def _process_cond_pair(self, value_left, operator: str, value_right) -> bool:
        operator = operator.lower()
        try:
            value_left_typed = type(value_right)(value_left)
        except ValueError as e:
            raise ConditionPairProcessingException(value_left, operator, value_right) from e
        try:
            if operator == 'eq':
                return value_left_typed == value_right
            elif operator == 'neq':
                return value_left_typed != value_right
            elif operator == 'gt':
                return value_left_typed > value_right
            elif operator == 'gte':
                return value_left_typed >= value_right
            elif operator == 'lt':
                return value_left_typed < value_right
            elif operator == 'lte':
                return value_left_typed <= value_right
            else:
                raise UnknownOperator(operator)
        except UnknownOperator as e:
            raise e
        except Exception as e:
            raise ConditionPairProcessingException(value_left_typed, operator, value_right) from e
