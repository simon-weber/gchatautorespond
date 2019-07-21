from gevent import monkey
monkey.patch_all()

import django
django.setup()

import logging
from threading import Thread

from django.conf import settings
from gevent.pywsgi import WSGIServer

from gchatautorespond.lib.chatworker.worker import Worker, app
from gchatautorespond.lib.chatworker.bot import ContextFilter


if __name__ == '__main__':
    worker = Worker()

    # Loading takes some time; don't block the api while it goes on.
    thread = Thread(target=worker.load)
    thread.start()

    app.config['worker'] = worker
    app.config['LOGGER_NAME'] = 'gchatautorespond.worker'

    # Add the ContextFilter to all stream handlers.
    # It can't be attached to the loggers since that wouldn't handle subloggers,
    # nor can it be attached to null/sentry handlers, since it'd produce output twice.
    handlers = set()
    for logger_name in settings.LOGGING['loggers']:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handlers.add(handler)
    for handler in handlers:
        handler.addFilter(ContextFilter)

    server = WSGIServer(('127.0.0.1', settings.WORKER_PORT), app)
    server.serve_forever()
