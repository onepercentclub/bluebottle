import locale
from builtins import range

from django.conf import settings
from django.db import IntegrityError, connections
from django_slowtests.testrunner import DiscoverSlowestTestsRunner
from djmoney.contrib.exchange.models import ExchangeBackend, Rate

from bluebottle.test.utils import InitProjectDataMixin


class MultiTenantRunner(DiscoverSlowestTestsRunner, InitProjectDataMixin):
    def setup_databases(self, *args, **kwargs):
        self.keepdb = getattr(settings, 'KEEPDB', self.keepdb)
        parallel = self.parallel
        self.parallel = 0
        result = super(MultiTenantRunner, self).setup_databases(**kwargs)
        self.parallel = parallel
        # Set local explicitly so test also run on OSX
        locale.setlocale(locale.LC_ALL, 'en_GB.UTF-8')

        try:
            backend, _created = ExchangeBackend.objects.get_or_create(
                base_currency='USD',
                name='openexchangerates.org'
            )
            Rate.objects.update_or_create(backend=backend, currency='USD', defaults={'value': 1})
            Rate.objects.update_or_create(backend=backend, currency='EUR', defaults={'value': 1.5})
            Rate.objects.update_or_create(backend=backend, currency='XOF', defaults={'value': 1000})
            Rate.objects.update_or_create(backend=backend, currency='NGN', defaults={'value': 500})
            Rate.objects.update_or_create(backend=backend, currency='UGX', defaults={'value': 5000})
            Rate.objects.update_or_create(backend=backend, currency='KES', defaults={'value': 100})
        except IntegrityError:
            pass

        if parallel > 1:
            base_conn = connections['default']
            base_db_name = base_conn.settings_dict['NAME']

            # IMPORTANT: no open connections to the template DB
            base_conn.close()

            with base_conn.cursor() as cursor:
                print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% DB MAGIC %%%%%%%%%%%%%%%%%%%%%%%%%%%")
                print(f"Using db {base_db_name}")
                for index in range(1, parallel + 1):
                    clone_db_name = f"{base_db_name}_{index}"
                    cursor.execute(f'DROP DATABASE IF EXISTS "{clone_db_name}"')
                    cursor.execute(
                        f'CREATE DATABASE "{clone_db_name}" TEMPLATE "{base_db_name}"'
                    )
                    print(f"Cloning database to {clone_db_name}")

        return result

    def run_checks(self, *args, **kwargs):
        return
