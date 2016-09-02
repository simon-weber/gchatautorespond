from gevent import monkey
monkey.patch_all()

import django
django.setup()

import logging
from threading import Thread

from django.conf import settings
from gevent.wsgi import WSGIServer
from raven.contrib.flask import Sentry

from gchatautorespond.lib.chatworker import Worker, app


if __name__ == '__main__':
    worker = Worker()

    # Loading takes some time; don't block the api while it goes on.
    thread = Thread(target=worker.load)
    thread.start()

    app.config['worker'] = worker
    app.config.update({'SENTRY_' + k.upper(): v for (k, v) in settings.RAVEN_CONFIG.items()
                      if k != 'dsn'})

    sentry = Sentry(app, dsn=settings.RAVEN_CONFIG['dsn'],
                    logging=True, level=logging.ERROR)

    server = WSGIServer(('127.0.0.1', settings.WORKER_PORT), app)
    server.serve_forever()
