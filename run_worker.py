import django
django.setup()

from django.conf import settings
from gevent.wsgi import WSGIServer

from gchatautorespond.lib.chatworker import Worker, app


if __name__ == '__main__':
    worker = Worker()
    worker.load()

    app.config['worker'] = worker
    server = WSGIServer(('localhost', settings.WORKER_PORT), app)
    server.serve_forever()
