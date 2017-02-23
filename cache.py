import hashlib
from collections import OrderedDict


class CacheMissException(RuntimeWarning):
    pass


class HashCache:

    def __init__(self, cache_size: int, logging_func: callable = None):
        self._cache = OrderedDict()
        self._logging_func = logging_func
        self._cache_size = cache_size
        self._cache_hits = 0
        self._cache_misses = 0

    @staticmethod
    def _get_hashed_id(item_id: str) -> str:
        return hashlib.sha1(item_id.encode()).hexdigest()

    def to_cache(self, item_id: str, item):
        self._cache[self._get_hashed_id(item_id)] = item
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    def from_cache(self, item_id: str):
        try:
            value = self._cache[self._get_hashed_id(item_id)]
        except KeyError:
            if self._logging_func:
                self._logging_func('Cache miss')
            self._cache_misses += 1
            raise CacheMissException
        else:
            if self._logging_func:
                self._logging_func('Cache hit')
            self._cache_hits += 1
            return value

    def get_stats(self):
        total_requests = self._cache_hits + self._cache_misses
        try:
            ratio = self._cache_hits / total_requests
        except ZeroDivisionError:
            ratio = 0.0
        return self._cache_hits, self._cache_misses, total_requests, ratio
