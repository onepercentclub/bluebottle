from django.test import TestCase
from django.conf import settings
from django.db.models import loading
from django.core.management import call_command


class BaseUserTestCase(TestCase):
    def _pre_setup(self):
        #Override the pre_setup method of TestCase parent to initialize the baseuser test app during testing.
        self._original_installed_apps = list(settings.INSTALLED_APPS)
        settings.INSTALLED_APPS += ('bluebottle.bb_accounts.tests.baseuser',)
        loading.cache.loaded = False
        call_command('syncdb', interactive=False, verbosity=0)
        super(BaseUserTestCase, self)._pre_setup()

    def _post_teardown(self):
        super(BaseUserTestCase, self)._post_teardown()
        settings.INSTALLED_APPS = self._original_installed_apps
        loading.cache.loaded = False



