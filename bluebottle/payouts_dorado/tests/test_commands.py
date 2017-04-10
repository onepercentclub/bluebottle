import json
from StringIO import StringIO


from django.db import connection
from django.test import TestCase
from django.core.management import call_command

from rest_framework.authtoken.models import Token
from tenant_schemas.utils import get_tenant_model
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class ExportKeysTest(TestCase):
    def setUp(self):
        super(ExportKeysTest, self).setUp()
        for tenant in get_tenant_model().objects.all():
            connection.set_tenant(tenant)
            user = BlueBottleUserFactory.create(
                email='test@example.com'
            )
            Token.objects.create(user=user)

    def test_all(self):
        out = StringIO()
        call_command('export_keys', 'test@example.com', '--all', stdout=out)
        result = json.loads(out.getvalue())

        self.assertEqual(len(result), 2)

        for token in result:
            self.assertTrue(token['domain'])
            self.assertTrue(token['api_key'])
            self.assertTrue(token['name'])
            self.assertTrue('fees' in token)
            self.assertEqual(token['fees']['over_target'], 0.05)
            self.assertEqual(token['fees']['under_target'], 0.05)

    def test_tenant(self):
        out = StringIO()
        tenant = get_tenant_model().objects.all()[0]
        call_command(
            'export_keys', 'test@example.com', '--tenant', tenant.client_name, stdout=out
        )
        result = json.loads(out.getvalue())

        self.assertEqual(len(result), 1)

        for token in result:
            self.assertTrue(token['domain'])
            self.assertTrue(token['api_key'])
            self.assertTrue(token['name'])
            self.assertEqual(token['fees']['over_target'], 0.05)
            self.assertEqual(token['fees']['under_target'], 0.05)
