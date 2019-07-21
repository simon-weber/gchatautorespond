from gevent import monkey
monkey.patch_all()

import django
django.setup()

import logging

from django.conf import settings
from gevent.pywsgi import WSGIServer

from gchatautorespond.lib.chatworker.testworker import TestWorker, app


if __name__ == '__main__':
    worker = TestWorker(settings.TEST_CREDENTIALS)
    worker.start()

    app.config['worker'] = worker
    app.config['LOGGER_NAME'] = 'gchatautorespond.testworker'

    server = WSGIServer(('127.0.0.1', settings.TESTWORKER_PORT), app)
    server.serve_forever()
