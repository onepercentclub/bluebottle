import mock

from django.utils import unittest

from bluebottle.common.tasks import _send_celery_mail
from bluebottle.clients import properties

class TestCeleryMailTenant(unittest.TestCase):

    def test_tenant_setup_celery(self):
        """ verify that, once send() is called, a tenant has been setup """
        # we can't assign to a variable in a nested scope but we can
        # append to a list from a higher scope
        tenant_during_send = []

        msg = mock.Mock()
        tenant = mock.Mock()

        def intercept_send(*kw, **args):
            tenant_during_send.append(properties.tenant)

        msg.send = intercept_send

        _send_celery_mail(msg, tenant, send=True)

        self.assertTrue(tenant_during_send[0] is tenant)

    def test_tenant_setup_celery_reset(self):
        """ after _send_celery_mail finishes, the tenant should be cleared
            again """
        msg = mock.Mock()
        tenant = mock.Mock()

        _send_celery_mail(msg, tenant, send=False)

        self.assertFalse(hasattr(properties, 'tenant'))
        self.assertEquals(properties.tenant_properties, {})
