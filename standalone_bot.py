"""gchatautorespond standalone (self-hosted) bot.

Use `auth` once to perform oauth and store a credentials file to the working directory.
Then, use `run` to start a bot from that credentials file.

Use SIGTERM to gracefully quiet or SIGQUIT to quit immediately.
Will exit and delete a credentials file upon revocation.

Usage:
  standalone_bot.py auth
  standalone_bot.py run <email> <autoresponse>
  standalone_bot.py (-h | --help)

Options:
  -h --help     Show this screen.
"""
from __future__ import print_function

from builtins import input
import os

from docopt import docopt
import httplib2  # included with oauth2client
from oauth2client.client import OAuth2WebServerFlow, AccessTokenRefreshError
import oauth2client.file

import warnings
warnings.filterwarnings('ignore', 'test worker credentials unavailable',)

os.environ['DJANGO_SETTINGS_MODULE'] = 'gchatautorespond.settings_standalone'
import django
django.setup()

from gchatautorespond.lib.chatworker.bot import AutoRespondBot


class StandaloneBot(AutoRespondBot):
    """An AutoResponseBot meant to be run from a shell.

    It's able to manage its own auth.
    """

    def __init__(self, *args, **kwargs):
        super(StandaloneBot, self).__init__(*args, **kwargs)

        self.add_event_handler('failed_auth', self.failed_auth)

    def failed_auth(self, _):
        """This event handler is triggered in two cases:

        * expired auth -> attempt to refresh and reconnect
        * revoked auth -> shutdown
        """

        credentials = self.get_oauth_credentials()

        try:
            self.logger.info("refreshing credentials")
            credentials.refresh(httplib2.Http())
        except AccessTokenRefreshError:
            self.logger.warning("credentials revoked?")
            self.oauth_storage.delete()
            self.disconnect()
        else:
            self.logger.info("credentials refreshed")
            self.password = credentials.access_token
            self.credentials['access_token'] = credentials.access_token
            self.oauth_storage.put(credentials)
            self.reconnect()

    @property
    def oauth_filename(self):
        return "%s.oauth_credentials" % self.email

    @property
    def oauth_storage(self):
        return oauth2client.file.Storage(self.oauth_filename)

    def get_oauth_credentials(self):
        oauth_credentials = self.oauth_storage.get()
        if oauth_credentials is None:
            raise IOError("could not retrieve oauth credentials from %r. Have you run `auth`?" % self.oauth_filename)

        return oauth_credentials

    def connect(self):
        oauth_credentials = self.get_oauth_credentials()
        self.password = oauth_credentials.access_token

        return super(StandaloneBot, self).connect()


def perform_oauth():
    """Provides a series of prompts for a user to follow to authenticate.
    Returns ``oauth2client.client.OAuth2Credentials`` when successful.
    In most cases, this should only be run once per machine to store
    credentials to disk, then never be needed again.

    If the user refuses to give access,
    ``oauth2client.client.FlowExchangeError`` is raised.
    """

    # This is a separate project from the hosted version, since we can't protect the client secret.
    flow = OAuth2WebServerFlow(
        '996043626456-32qgmel3mi3t27k32veicv1dmmf3t06s.apps.googleusercontent.com',
        'gnmF3W2Q8Ull9AO09Z-1esqd',
        ' '.join(['https://www.googleapis.com/auth/googletalk', 'email']),
        'urn:ietf:wg:oauth:2.0:oob',
    )

    auth_uri = flow.step1_get_authorize_url()
    print()
    print("Visit the following url:\n %s" % auth_uri)

    code = input("Follow the prompts, then paste the auth code here and hit enter: ")

    credentials = flow.step2_exchange(code)

    storage = StandaloneBot(credentials.id_token['email'], None, None, None, None, None).oauth_storage
    storage.put(credentials)

    return credentials


if __name__ == '__main__':
    arguments = docopt(__doc__)

    if arguments['auth']:
        perform_oauth()
    elif arguments['run']:
        bot = StandaloneBot(arguments['<email>'], None, None, arguments['<autoresponse>'], False, None)
        bot.connect()
        bot.process(block=True)
