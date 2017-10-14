import datetime


class Throttler(object):
    def __init__(self, throttle_delta):
        self.throttle_delta = throttle_delta

    def update(self, id):
        self._set(id, datetime.datetime.now())

    def is_throttled(self, id):
        last_time = self._get(id)
        if last_time is None:
            return False

        return (datetime.datetime.now() - last_time) < self.throttle_delta

    def _set(self, id, datetime):
        raise NotImplementedError

    def _get(self, id):
        raise NotImplementedError


class MemoryThrottler(Throttler):
    def __init__(self, *args, **kwargs):
        super(MemoryThrottler, self).__init__(*args, **kwargs)
        self._datetimes = {}

    def _set(self, id, datetime):
        self._datetimes[id] = datetime

    def _get(self, id):
        return self._datetimes.get(id)
