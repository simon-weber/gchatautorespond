# Note that this won't work with gevent, since you need to patch it earlier.
# Just switch to a normal script with manual setup for that.

from django.core.management.base import BaseCommand

from gchatautorespond.lib.chatworker import Worker


class Command(BaseCommand):
    help = 'Runs the bots'

    def handle(self, *args, **options):
        worker = Worker()
        worker.load()
        worker.listen_forever()
