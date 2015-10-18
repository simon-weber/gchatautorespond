from django.core.management.base import BaseCommand

from gchatautorespond.lib.chatworker import Worker


class Command(BaseCommand):
    help = 'Runs the bots'

    def handle(self, *args, **options):
        worker = Worker()
        worker.load()
        worker.listen_forever()
