import datetime
import os

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
PORT = 8000
WORKER_PORT = 50001

CLIENT_SECRETS_PATH = os.path.join(SECRETS_DIR, 'client_secrets.json')
OAUTH_SCOPE = ' '.join(['https://www.googleapis.com/auth/googletalk', 'email'])
OAUTH_REDIRECT_URI = "%s%s/%s" % (SCHEME, HOST, 'autorespond/oauth2callback/')

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

    # Putting the admin app after our own prevents overriding
    # password reset templates.
    'django.contrib.admin',

    'djmail',
    'djsupervisor',
    'registration',
    'raven.contrib.django.raven_compat',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'gchatautorespond.middleware.ExceptionMiddleware',
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

SUPERVISOR_LOG_DIR = '/var/log/supervisord'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
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
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
    },
    'loggers': {
        '': {
            'level': 'WARNING',
            'handlers': ['sentry'],
        },
        'django': {
            'handlers': ['console_simple'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'WARNING'),
        },
        'django.request': {
            'handlers': ['console_simple'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'sleekxmpp': {
            'handlers': ['console_simple'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'gchatautorespond': {
            'handlers': ['console_verbose'],
            'level': 'INFO',
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
        'NAME': os.path.join(BASE_DIR, '..', 'gchat_db.sqlite3')
    }
}

# Email
EMAIL_BACKEND = 'djmail.backends.async.EmailBackend'
DJMAIL_REAL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.sparkpostmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = get_secret('sparkpost.user')
EMAIL_HOST_PASSWORD = get_secret('sparkpost.password')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'noreply@gchat.simon.codes'

ADMINS = (('Simon', 'simon@simonmweber.com'),)
SERVER_EMAIL = DEFAULT_FROM_EMAIL


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'assets')
STATIC_URL = '/assets/'


# Django Registration
ACCOUNT_ACTIVATION_DAYS = 1


# Sentry
RAVEN_CONFIG = {
    'dsn': get_secret('raven.dsn'),
    'release': RELEASE,
}
