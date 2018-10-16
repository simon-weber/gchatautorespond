"""
Send an email to the django admins.
Intended for use from the shell (eg to alert on failed crontasks).
"""

import django
django.setup()

import logging
import sys

from django.core.mail import mail_admins

logger = logging.getLogger('gchatautorespond.send_admin_email')

if __name__ == '__main__':
    try:
        subject = sys.argv[1]
        body = sys.argv[2]
        mail_admins(subject, body, fail_silently=False)
    except:
        logger.exception("failed to send admin email %s", subject)
