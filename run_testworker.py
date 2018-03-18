from gevent import monkey
monkey.patch_all()

import django
django.setup()

import logging

from django.conf import settings
from gevent.wsgi import WSGIServer
from raven.contrib.flask import Sentry

from gchatautorespond.lib.chatworker.testworker import TestWorker, app


if __name__ == '__main__':
    worker = TestWorker(settings.TEST_CREDENTIALS)
    worker.start()

    app.config['worker'] = worker
    app.config['LOGGER_NAME'] = 'gchatautorespond.testworker'
    app.config.update({'SENTRY_' + k.upper(): v for (k, v) in settings.RAVEN_CONFIG.items()
                      if k != 'dsn'})

    if 'dsn' in settings.RAVEN_CONFIG:
        sentry = Sentry(app, dsn=settings.RAVEN_CONFIG['dsn'],
                        logging=True, level=logging.ERROR)

    server = WSGIServer(('127.0.0.1', settings.TESTWORKER_PORT), app)
    server.serve_forever()
