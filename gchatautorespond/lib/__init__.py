from concurrent.futures import ThreadPoolExecutor
import hashlib
import logging

import google_measurement_protocol as gmp


logger = logging.getLogger(__name__)
thread_pool = ThreadPoolExecutor(4)


def report_ga_event_async(client_id, **event_kwargs):
    """
    Report a Universal Analytics event in another thread.

    client_id will be hashed before sending.

    event_kwargs must have category and action, and may have label and value.
    """
    from django.conf import settings

    # client ids should not be PII.
    h = hashlib.sha1()
    h.update(str(client_id).encode())
    client_id = h.hexdigest()

    if settings.SEND_GA_EVENTS:
        logger.info("queueing event %s: %r", client_id, event_kwargs)
        thread_pool.submit(settings.GA_CODE, _report_event, client_id, **event_kwargs)


def _report_event(ga_code, client_id, **event_kwargs):
    event = gmp.Event(**event_kwargs)
    gmp.report(ga_code, client_id, event)
    logger.info("reported event %s: %r", client_id, event_kwargs)
