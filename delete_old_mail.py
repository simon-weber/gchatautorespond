import django
django.setup()

import datetime
import logging

from djmail.models import Message
from django.core.mail import mail_admins
import sentry_sdk

OLD_CUTOFF = datetime.timedelta(days=30)

logger = logging.getLogger('gchatautorespond.delete_old_mail')


if __name__ == '__main__':
    try:
        logger.info('running')
        cutoff = datetime.datetime.now() - OLD_CUTOFF
        old_messages = Message.objects.filter(created_at__lt=cutoff)

        unsent_messages = list(old_messages.filter(sent_at=None))
        if unsent_messages:
            contents = repr([m.__dict__ for m in unsent_messages])
            logger.warning("unsent messages found:", extra={'data': {'messages': contents}})
            logger.info(contents)
            mail_admins('unsent email detected', contents)

        logger.info("deleting %s old messages", old_messages.count())
        old_messages.delete()
        logger.info("done")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise
