import base64
import datetime
import logging
import os
import pickle
import re

import braintree
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.utils import BadDsn

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_DIR = os.path.join(BASE_DIR, 'secrets')


def get_secret(filename):
    with open(os.path.join(SECRETS_DIR, filename)) as f:
        return f.read().strip()


DEBUG = False
SECRET_KEY = get_secret('secret_key.txt')

GA_CODE = 'UA-69242364-1'
SEND_GA_EVENTS = True

SCHEME = 'https://'
HOST = 'gchat.simon.codes'
ALLOWED_HOSTS = [HOST]
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

PORT = 8000
WORKER_PORT = 50001
TESTWORKER_PORT = 50002

GOOGLE_OAUTH2_CLIENT_SECRETS_JSON = os.path.join(SECRETS_DIR, 'client_secrets.json')
OAUTH_SCOPE = ' '.join(['https://www.googleapis.com/auth/googletalk', 'profile', 'email'])
OAUTH_REDIRECT_URI = "%s%s/%s" % (SCHEME, HOST, 'autorespond/oauth2callback/')

# This is a CredentialsField, not a GoogleCredentials.
try:
    TEST_CREDENTIALS = pickle.loads(base64.b64decode(get_secret('test_account.credentialrow')))
except:
    logging.warning("test worker credentials unavailable", exc_info=True)
    TEST_CREDENTIALS = None


LOGIN_URL = '/'

try:
    with open(os.path.join(BASE_DIR, 'release.sha')) as f:
        RELEASE = f.read().strip()
except:
    RELEASE = str(datetime.datetime.now())

# Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'

# Braintree
BRAINTREE_MERCHANT_ID = get_secret('bt_prod.merchant_id')
BRAINTREE_PUBLIC_KEY = get_secret('bt_prod.public_key')
BRAINTREE_PRIVATE_KEY = get_secret('bt_prod.private_key')
braintree.Configuration.configure(braintree.Environment.Production,
                                  merchant_id=BRAINTREE_MERCHANT_ID,
                                  public_key=BRAINTREE_PUBLIC_KEY,
                                  private_key=BRAINTREE_PRIVATE_KEY)
PRICE_REPR = '$2'
PLAN_ID = 'monthly_v0'


# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Adding this fixes a 1.9 upgrade warning, but also requires that we
    # set up the db to support Sites.
    # 'django.contrib.sites',

    'gchatautorespond.apps.autorespond',
    'gchatautorespond.apps.licensing',

    # Putting the admin app after our own prevents overriding
    # password reset templates.
    'django.contrib.admin',

    'djmail',
    'registration',
    'bootstrap3',
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'gchatautorespond.apps.autorespond.middleware.CacheDefaultOffMiddleware',
)

ROOT_URLCONF = 'gchatautorespond.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gchatautorespond.wsgi.application'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s: %(asctime)s - %(name)s: %(message)s'
        },
        'withfile': {
            'format': '%(levelname)s: %(asctime)s - %(name)s (%(module)s:%(lineno)s): %(message)s'
        },
    },
    'handlers': {
        'console_simple': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'console_verbose': {
            'class': 'logging.StreamHandler',
            'formatter': 'withfile',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console_simple'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'WARNING'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console_simple'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'sleekxmpp': {
            'handlers': ['console_simple'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': False,
        },
        'gchatautorespond': {
            'handlers': ['console_verbose'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

# The code directory gets wiped when deploying, so in prod we want
# the db up a level so it doesn't get deleted.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/opt/gchatautorespond/gchatautorespond_db.sqlite3',
    }
}

# Email
EMAIL_BACKEND = 'djmail.backends.async.EmailBackend'
DJMAIL_REAL_BACKEND = 'django_amazon_ses.EmailBackend'
AWS_ACCESS_KEY_ID = get_secret('ses.id')
AWS_SECRET_ACCESS_KEY = get_secret('ses.key')
DEFAULT_FROM_EMAIL = 'GChat Autoresponder <noreply@gchat.simon.codes>'

ADMINS = (('Simon', 'simon@simonmweber.com'),)
SERVER_EMAIL = DEFAULT_FROM_EMAIL
REGISTRATION_EMAIL_HTML = False


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = '/assets/'
STATIC_ROOT = '/opt/gchatautorespond/assets'


# Django Registration
ACCOUNT_ACTIVATION_DAYS = 1


# Sentry
_patterns = [re.compile(r"\[%s=\d\d*\] " % param) for param in ('log_id', 'bot_id')]
def _sub(s):
    r = s
    for p in _patterns:
        r = re.sub(p, '', r)
    return r
def _before_send(event, hint):
    message = event.get('logentry', {}).get('message')
    if message:
        event['logentry']['message'] = _sub(message)

    return event

sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.WARNING,
)
try:
    sentry_sdk.init(
        before_send=_before_send,
        dsn=get_secret('sentry.dsn'),
        release=RELEASE,
        integrations=[
            DjangoIntegration(),
            FlaskIntegration(),
            sentry_logging,
        ],
    )
except BadDsn:
    logging.warning("sentry unavailable", exc_info=True)


BOOTSTRAP3 = {
    'horizontal_label_class': 'col-md-3',
    'horizontal_field_class': 'col-md-9',
}
