from .settings_dev import *  # noqa

GOOGLE_OAUTH2_CLIENT_SECRETS_JSON = os.path.join(BASE_DIR, 'standalone_oauth.json')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get('DJ_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('DJ_EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = "GChat Autoresponder <%s>" % EMAIL_HOST_USER
