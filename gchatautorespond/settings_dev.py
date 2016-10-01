from .settings import *  # noqa

DEBUG = True
SECRET_KEY = 'dev_secret_key'

SEND_GA_EVENTS = False

SCHEME = 'http://'
HOST = '127.0.0.1'
ALLOWED_HOSTS = [HOST]
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'gchat_db.sqlite3')
    }
}

DJMAIL_REAL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

RAVEN_CONFIG.pop('dsn')
