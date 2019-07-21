from .settings import *  # noqa

DEBUG = True
SECRET_KEY = 'dev_secret_key'

SEND_GA_EVENTS = False

SCHEME = 'http://'
HOST = '127.0.0.1'
ALLOWED_HOSTS = ['*']
PORT = 8000

BRAINTREE_MERCHANT_ID = get_secret('bt_sandbox.merchant_id')
BRAINTREE_PUBLIC_KEY = get_secret('bt_sandbox.public_key')
BRAINTREE_PRIVATE_KEY = get_secret('bt_sandbox.private_key')

braintree.Configuration.configure(braintree.Environment.Sandbox,
                                  merchant_id=BRAINTREE_MERCHANT_ID,
                                  public_key=BRAINTREE_PUBLIC_KEY,
                                  private_key=BRAINTREE_PRIVATE_KEY)

OAUTH_REDIRECT_URI = "%s%s:%s/%s" % (SCHEME, HOST, PORT, 'autorespond/oauth2callback/')

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

if os.environ.get('IN_CODE_DB', 'false') == 'true':
    # expected to be true when run outside a vm
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'gchatautorespond_db.sqlite3')
        }
    }

DJMAIL_REAL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# disable sentry
sentry_sdk.init(dsn='')  # noqa: F405
