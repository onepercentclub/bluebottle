import logging
import sys

from django.contrib.auth.hashers import get_hasher
from django.core.management.base import BaseCommand
from django.db import connection

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.members.models import Member

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--tenant', '-t', action='store', dest='tenant',
                            help="The tenant to run the recurring donations for.")

    def handle(self, *args, **options):
        """
        Converts passwords with the default wordpress phpass algorithm
        to be readable by Django.
        """
        try:
            client = Client.objects.get(client_name=options['tenant'])
            connection.set_tenant(client)

        except Client.DoesNotExist:
            logger.error("You must specify a valid tenant with -t or --tenant.")
            tenants = Client.objects.all().values_list('client_name', flat=True)
            logger.info("Valid tenants are: {0}".format(", ".join(tenants)))
            sys.exit(1)

        with LocalTenant(client, clear_tenant=True):
            hasher = get_hasher('phpass')
            users = Member.objects.filter(password__startswith='$P$B')
            for user in users:
                user.password = hasher.from_orig(user.password)
                user.save()

            print "%s User passwords converted" % len(users)
