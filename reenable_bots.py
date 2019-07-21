import django
django.setup()

import logging

from django.conf import settings
import requests
import sentry_sdk

from gchatautorespond.apps.autorespond.models import AutoResponse

logger = logging.getLogger('gchatautorespond.reenable_bots')


if __name__ == '__main__':
    try:
        logger.info('running')
        disabled_autoresponds = list(AutoResponse.objects.filter(admin_disabled=True))

        if disabled_autoresponds:
            logger.info("found %s disabled autoresponds: %s", len(disabled_autoresponds), disabled_autoresponds)
            for autorespond in disabled_autoresponds:
                autorespond.admin_disabled = False
                autorespond.save()
                requests.post("http://127.0.0.1:%s/%s/%s" % (settings.WORKER_PORT, 'restart', autorespond.id))
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise
