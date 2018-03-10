from collections import deque, defaultdict
import datetime
import functools
import httplib
import logging
import subprocess

from flask import Flask, jsonify
import httplib2
from oauth2client.client import AccessTokenRefreshError

from gchatautorespond.apps.autorespond.models import AutoResponse
from .bot import AutoRespondBot, ContextFilter
from .throttle import DbThrottler

logger = logging.getLogger(__name__)

# This app provides an api to the Worker.
app = Flask(__name__)


@app.route('/status')
def status():
    return jsonify(app.config['worker'].get_status())


@app.route('/stop/<int:autorespond_id>', methods=['POST'])
def stop(autorespond_id):
    ContextFilter.context.log_id = autorespond_id
    app.config['worker'].stop(autorespond_id)
    return ('', httplib.NO_CONTENT)


@app.route('/restart/<int:autorespond_id>', methods=['POST'])
def restart(autorespond_id):
    ContextFilter.context.log_id = autorespond_id
    autorespond = AutoResponse.objects.get(id=autorespond_id)

    app.config['worker'].stop(autorespond.id)
    app.config['worker'].start(autorespond)

    return ('', httplib.NO_CONTENT)


class Worker(object):
    """A Worker maintains multiple Bots.

    Typical usage::

        worker = Worker()
        worker.load()
        # serve app with some wsgi server
    """

    # If a bot disconnects this many times in the period, it will be shut down.
    max_disconnects = 3
    disconnect_period = datetime.timedelta(minutes=1)

    def __init__(self):
        self.autoresponds = {}

        # Map autorespond ids onto the last N times they disconnected.
        self.disconnects = defaultdict(lambda: deque(maxlen=self.max_disconnects))

    def load(self):
        """Start bots for any existing autoresponses."""

        for autorespond in AutoResponse.objects.all():
            self.start(autorespond)
            logger.info('loaded %r', autorespond.credentials.email)

    def get_status(self):
        """Return a human-readable dict representative of the worker's current state."""

        num_bots = len(self.autoresponds)
        status = 'ok' if num_bots > 0 else 'idle'

        # Shockingly, NR can't report disk usage of virtual volumes.
        df_output = subprocess.check_output(['df'])
        df_percents = [int(line.split()[4].rstrip('%')) for line in df_output.split('\n')[1:] if line]
        max_percent = max(df_percents)
        if max_percent > 75:
            status = 'disk_warning'

        return {'status': status,
                'num_bots': len(self.autoresponds),
                'max_disk_percent': max_percent,
                'bots': self.autoresponds.keys(),
                }

    def start(self, autorespond):
        """Start a bot for an autorespond in a new thread."""

        logger.info("starting autorespond %s", autorespond.id)

        if autorespond.id in self.autoresponds:
            logger.warning("autorespond %s already running? state: %r", autorespond.id, self.autoresponds)

        if autorespond.admin_disabled:
            logger.warning("refusing to start disabled autorespond %s", autorespond.id)
            return

        if not autorespond.user.currentlicense.license.is_active:
            logger.warning("refusing to start autorespond for inactive account %s", autorespond.user)
            return

        excluded_users = list(autorespond.excludeduser_set.all())
        excluded_names = []
        notify_overrides = {}
        for user in excluded_users:
            excluded_names.append(user.name)
            if user.email_notifications != user.DEFAULT:
                notify_overrides[user.name] = True if user.email_notifications == user.ALWAYS else False

        bot = AutoRespondBot(
            autorespond.credentials.email,
            autorespond.credentials.credentials.access_token,
            autorespond.id,
            autorespond.response,
            autorespond.email_notifications,
            autorespond.user.email,
            DbThrottler(autorespond.id, datetime.timedelta(minutes=autorespond.throttle_mins)),
            True,
            excluded_names,
            notify_overrides,
        )

        failed_auth_callback = functools.partial(self._bot_failed_auth,
                                                 autorespond=autorespond)
        bot.add_event_handler('failed_auth', failed_auth_callback)

        disconnect_callback = functools.partial(self._bot_disconnected,
                                                bot=bot,
                                                autorespond=autorespond)
        bot.add_event_handler('disconnected', disconnect_callback)

        logger.info("registering bot %s to autorespond %s", bot.bot_id, autorespond.id)
        self.autoresponds[autorespond.id] = bot
        bot.connect()
        bot.process(block=False)  # starts a new thread

    def stop(self, autorespond_id):
        """Stop an already-running bot for an autorespond_id."""

        logger.info("stopping autorespond %s", autorespond_id)

        if autorespond_id not in self.autoresponds:
            logger.info("autorespond %s not yet running", autorespond_id)
            return

        bot = self.autoresponds.pop(autorespond_id)
        logger.info("popped bot %s for autorespond %s", bot.bot_id, autorespond_id)

        # TODO consider waiting here, then triggering abort if it fails.
        bot.disconnect(wait=False, send_close=False)  # safe if already disconnected

        return bot

    def _bot_disconnected(self, event, bot, autorespond):
        """Stop bots that are constantly disconnecting and reconnecting,"""

        logger.info("bot %s has disconnected for autorespond %s", bot.bot_id, autorespond.id)

        disconnects = self.disconnects[autorespond.id]

        now = datetime.datetime.now()
        disconnects.append(now)

        if ((len(disconnects) == self.max_disconnects
             and disconnects[0] > (now - self.disconnect_period))):
            logger.warning("disabling flapping bot for autorespond %s (%r) after disconnects %r",
                           autorespond.id, autorespond.credentials.email, disconnects)

            self.stop(autorespond.id)
            autorespond.admin_disabled = True
            autorespond.save()

    def _bot_failed_auth(self, event, autorespond):
        """Handle two cases:

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
