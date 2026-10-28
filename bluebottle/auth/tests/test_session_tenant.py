from http.cookies import SimpleCookie

from django.conf import settings
from django.db import connection
from django.urls import reverse

from bluebottle.clients.models import Client
from bluebottle.clients.session_backends import TENANT_SESSION_KEY
from bluebottle.clients.utils import LocalTenant
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import ApiClient, BluebottleTestCase


class SessionTenantIsolationTest(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.other_tenant = Client.objects.get(schema_name='test2')
        self.addCleanup(connection.set_tenant, self.tenant)

        self.user = BlueBottleUserFactory.create(is_staff=True)
        self.user.password = ''
        self.user.save()

        with LocalTenant(self.other_tenant):
            self.other_user = BlueBottleUserFactory.create(pk=self.user.pk, is_staff=True)
            self.other_user.password = ''
            self.other_user.save()

        self.client.force_login(self.user)

    def test_session_works_on_own_tenant(self):
        response = self.client.get(reverse('user-current'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.user.pk)

    def test_session_is_not_valid_on_other_tenant_api(self):
        response = self.client.get(
            reverse('user-current'), HTTP_HOST=self.other_tenant.domain_url
        )
        self.assertNotEqual(response.status_code, 200)

    def test_replay_on_other_tenant_leaves_original_session_intact(self):
        attacker = ApiClient(self.other_tenant)
        attacker.cookies = SimpleCookie({
            settings.SESSION_COOKIE_NAME: self.client.cookies[settings.SESSION_COOKIE_NAME].value
        })
        self.assertNotEqual(attacker.get(reverse('user-current')).status_code, 200)
        connection.set_tenant(self.tenant)

        response = self.client.get(reverse('user-current'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.user.pk)

    def test_session_without_tenant_is_ignored(self):
        session = self.client.session
        data = session.load()
        data.pop(TENANT_SESSION_KEY)
        session.model.objects.filter(session_key=session.session_key).update(
            session_data=session.encode(data)
        )

        response = self.client.get(reverse('user-current'))
        self.assertNotEqual(response.status_code, 200)

    def test_session_is_not_valid_on_other_tenant_admin(self):
        response = self.client.get(
            reverse('admin:index'), HTTP_HOST=self.other_tenant.domain_url
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])
