import mock

from django.utils import unittest

from bluebottle.common.tasks import _send_celery_mail
from bluebottle.clients import properties

class TestCeleryMailTenant(unittest.TestCase):

    def test_tenant_setup_celery(self):
        """ verify that, once send() is called, a tenant has been setup """

        class interceptor(object):
            tenant = None

            def __call__(self, *kw, **args):
                self.tenant = properties.tenant

        intercept_send = interceptor()

        msg = mock.Mock(send=intercept_send)
        tenant = mock.Mock()

        _send_celery_mail(msg, tenant, send=True)

        self.assertTrue(intercept_send.tenant is tenant)

    def test_tenant_setup_celery_reset(self):
        """ after _send_celery_mail finishes, the tenant should be cleared
            again """
        msg = mock.Mock()
        tenant = mock.Mock()

        _send_celery_mail(msg, tenant, send=False)

        self.assertFalse(hasattr(properties, 'tenant'))
        self.assertEquals(properties.tenant_properties, {})
