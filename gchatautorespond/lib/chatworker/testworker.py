import http.client
import logging

from flask import Flask
import httplib2
from oauth2client.client import AccessTokenRefreshError

from .bot import MessageBot

logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/message/<email>', methods=['POST'])
def message(email):
    app.config['worker'].send_to(email)
    return ('', http.client.NO_CONTENT)


class TestWorker:
    """A TestWorker runs a bot that can send messages to other bots."""

    message = ('Hello! This is your Autoresponder test message.'
               '\nIf you did not request one, email support@gchat.simon.codes for help.')

    def __init__(self, raw_credentials):
        print(raw_credentials)
        print(raw_credentials.__dict__)
        self.raw_credentials = raw_credentials

    def start(self):
        self.bot = MessageBot(self.raw_credentials.id_token['email'], self.raw_credentials.access_token)

        failed_auth_callback = self._bot_failed_auth
        self.bot.add_event_handler('failed_auth', failed_auth_callback)

        self.bot.connect()
        self.bot.process(block=False)

    def stop(self):
        self.bot.disconnect(wait=False, send_close=False)

    def send_to(self, address):
        logger.info("sending to %r", address)
        self.bot.send_to(address, self.message)

    def _bot_failed_auth(self, event):
        """Handle two cases:

        * expired auth -> attempt to refresh
        * revoked auth -> remove the credentials
        """
        self.stop()

        try:
            logger.info("refreshing test bot credentials")
            self.raw_credentials.refresh(httplib2.Http())
        except AccessTokenRefreshError:
            logger.error("test bot credentials revoked?")
        else:
            logger.info("test bot credentials refreshed")
            self.start()
