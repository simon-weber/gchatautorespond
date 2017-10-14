import datetime
import logging

from django.db import IntegrityError

from gchatautorespond.apps.autorespond.models import LastResponse

logger = logging.getLogger(__name__)


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

    def _set(self, id, time):
        raise NotImplementedError

    def _get(self, id):
        raise NotImplementedError


class MemoryThrottler(Throttler):
    def __init__(self, *args, **kwargs):
        super(MemoryThrottler, self).__init__(*args, **kwargs)
        self._datetimes = {}

    def _set(self, id, time):
        self._datetimes[id] = time

    def _get(self, id):
        return self._datetimes.get(id)


class DbThrottler(Throttler):
    def __init__(self, autorespond_id, *args, **kwargs):
        super(DbThrottler, self).__init__(*args, **kwargs)
        self._autorespond_id = autorespond_id

    def _set(self, id, time):
        try:
            LastResponse.objects.update_or_create(
                autorespond_id=self._autorespond_id, bare_jid=id,
                defaults={'last_response_time': time}
            )
        except IntegrityError:
            logger.exception("failed to save LastResponse(%s, %s) at %s", self._autorespond_id, id, time)

    def _get(self, id):
        try:
            return LastResponse.objects.get(autorespond_id=self._autorespond_id, bare_jid=id).last_response_time
        except LastResponse.DoesNotExist:
            return None
