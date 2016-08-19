import Queue
from enum import Enum
import functools
from collections import namedtuple
import logging
from multiprocessing.managers import BaseManager
import subprocess

from django.conf import settings
import httplib2
from oauth2client.client import AccessTokenRefreshError

from gchatautorespond.apps.autorespond.models import AutoResponse
from .bot import AutoRespondBot

logger = logging.getLogger(__name__)

IPCMessage = namedtuple('IPCMessage', 'type data')


class MessageType(Enum):
    stop = 1
    restart = 2
    status = 3
    status_response = 4


class WorkerIPC(BaseManager):
    """
    A Manager that provides a request and response queue to talk to a Worker cross-process.
    """
    request_queue = Queue.Queue()
    response_queue = Queue.Queue()

WorkerIPC.register('get_request_queue', callable=lambda: WorkerIPC.request_queue)
WorkerIPC.register('get_response_queue', callable=lambda: WorkerIPC.response_queue)


class Worker(object):
    """A Worker maintains multiple Bots.

    Updates are sent via a WorkerIPC.

    Typical usage::

        worker = Worker()
        worker.load()
        worker.listen_forever()
    """

    def __init__(self):
        self.autoresponds = {}
        self.ipc = WorkerIPC(address=('localhost', 50000), authkey=settings.QUEUE_AUTH_KEY)

    def load(self):
        """Start bots for any existing autoresponses."""

        for autorespond in AutoResponse.objects.all():
            self.start(autorespond)

    def listen_forever(self):
        """Block forever while receiving updates over the queue."""

        # start the manager server in a subprocess.
        self.ipc.start()
        logger.info('manager server started')

        # connect to the manager server.
        self.ipc.connect()
        logger.info('manager client conected')
        request_queue = self.ipc.get_request_queue()
        response_queue = self.ipc.get_response_queue()

        while True:
            try:
                logger.info('state: %r', self.autoresponds)
                message = request_queue.get()
                logger.info('message: %r', message)
                if message.type is MessageType.stop:
                    self.stop(message.data)
                elif message.type is MessageType.restart:
                    autorespond = AutoResponse.objects.get(id=message.data)
                    self.stop(autorespond.id)
                    self.start(autorespond)
                elif message.type is MessageType.status:
                    response_queue.put_nowait(IPCMessage(MessageType.status_response, self.get_status()))
                else:
                    logger.error('unrecognized message! %r', message)
            except:
                logging.exception('exception while processing %s', message)

    def get_status(self):
        """Return a human-readable dict representative of the worker's current state."""

        num_bots = len(self.autoresponds)
        status = 'ok' if num_bots > 0 else 'idle'

        # Shockingly, NR can't report disk usage of virtual volumes.
        df_output = subprocess.check_output(['df'])
        logging.info('df output: %r', df_output)
        df_percents = [int(line.split()[4].rstrip('%')) for line in df_output.split('\n')[1:] if line]
        max_percent = max(df_percents)
        if max_percent > 75:
            status = 'disk_warning'

        return {'status': status, 'num_bots': len(self.autoresponds), 'max_disk_percent': max_percent}

    def start(self, autorespond):
        """Start a bot for an autorespond in a new thread."""

        logger.info("starting autorespond %s", autorespond.id)
        if autorespond.id in self.autoresponds:
            logger.warning("autorespond %s already running? state: %r", autorespond.id, self.autoresponds)

        notify_email = None
        if autorespond.email_notifications:
            notify_email = autorespond.user.email

        bot = AutoRespondBot(
            autorespond.credentials.email,
            autorespond.credentials.credentials.access_token,
            autorespond.response,
            notify_email,
        )

        failed_auth_callback = functools.partial(self._bot_failed_auth,
                                                 autorespond=autorespond)
        bot.add_event_handler('failed_auth', failed_auth_callback)

        self.autoresponds[autorespond.id] = bot
        bot.connect()
        bot.process(block=False)  # starts a new thread

    def stop(self, autorespond_id):
        """Stop an already-running bot for an autorespond_id."""

        logger.info("stopping autorespond %s", autorespond_id)

        if autorespond_id not in self.autoresponds:
            logger.warning("autorespond %s not yet running", autorespond_id)
            return

        bot = self.autoresponds.pop(autorespond_id)

        # TODO waiting here prevents race conditions between start/stop, but is that necessary?
        # Worse case you have two bots running temporarily.
        bot.disconnect(wait=False)  # safe if already disconnected

        return bot

    def _bot_failed_auth(self, bot, autorespond):
        """This callback is triggered in two cases:

        * expired auth -> attempt to refresh
        * revoked auth -> remove the credentials
        """

        self.stop(autorespond.id)

        try:
            logger.info("refreshing autorespond %s credentials", autorespond.id)
            autorespond.credentials.credentials.refresh(httplib2.Http())
        except AccessTokenRefreshError:
            logger.warning("autorespond %s credentials revoked?", autorespond.id)
            autorespond.credentials.delete()
        else:
            logger.info("autorespond %s credentials refreshed", autorespond.id)
            autorespond.credentials.save()
            self.start(autorespond)
