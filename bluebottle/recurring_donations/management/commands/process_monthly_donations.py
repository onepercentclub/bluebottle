import sys
import logging

from django.core.management.base import BaseCommand

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from ...tasks import (
    prepare_monthly_batch, process_monthly_batch,
    process_single_monthly_order
)
PAYMENT_METHOD = 'docdataDirectdebit'

logger = logging.getLogger(__name__)


#
# First step:
# ./manage.py process_monthly_donations --prepare
# ./manage.py process_monthly_donations --process
#
# ./manage.py process_monthly_donations --process-single bart@1procentclub.nl
#

class Command(BaseCommand):
    help = 'Process monthly donations.'
    requires_model_validation = True

    verbosity_loglevel = {
        '0': logging.ERROR,  # 0 means no output.
        '1': logging.WARNING,  # 1 means normal output (default).
        '2': logging.INFO,  # 2 means verbose output.
        '3': logging.DEBUG  # 3 means very verbose output.
    }

    def add_arguments(self, parser):
        parser.add_argument('--tenant', '-t', action='store', dest='tenant',
                            help="The tenant to run the recurring donations for.")

        parser.add_argument('--no-email', action='store_true', dest='no_email',
                            default=False,
                            help="Don't send the monthly donation email to users (when processing).")

        parser.add_argument('--prepare', action='store_true', dest='prepare',
                            default=False,
                            help="Prepare the monthly donations and create records that can be processed later.")

        parser.add_argument('--process', action='store_true', dest='process',
                            default=False,
                            help="Process the prepared records.")

        parser.add_argument('--process-single', action='store', dest='process_single',
                            default=False,
                            metavar='<someone@gmail.com>',
                            help="Process only the MonthlyOrder for specified e-mail address.")

    def handle(self, **options):
        logger = logging.getLogger('console')

        send_email = not options['no_email']

        try:
            client = Client.objects.get(client_name=options['tenant'])
        except Client.DoesNotExist:
            logger.error("You must specify a valid tenant with -t or --tenant.")
            tenants = Client.objects.all().values_list('client_name', flat=True)
            logger.info("Valid tenants are: {0}".format(", ".join(tenants)))
            sys.exit(1)

        with LocalTenant(client, clear_tenant=True):
            if options['prepare']:
                prepare_monthly_batch()

            if options['process']:
                process_monthly_batch(tenant=client, monthly_batch=None, send_email=send_email)
            if options['process_single']:
                process_single_monthly_order(options['process_single'], None,
                                             send_email)
