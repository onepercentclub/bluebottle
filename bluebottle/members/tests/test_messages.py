from urllib.parse import urlparse, parse_qs

from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.http import base36_to_int
from rest_framework import status

from bluebottle.members.messages import PasswordResetMessage
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import NotificationTestCase, JSONAPITestClient


class PasswordResetMessageTestCase(NotificationTestCase):
    message_class = PasswordResetMessage

    def setUp(self):
        super().setUp()
        self.obj = BlueBottleUserFactory.create(password='old-password')
        self.create()

    def get_reset_link(self):
        links = self._html.find_all('a', {'class': 'action-email'})
        self.assertEqual(len(links), 1)
        return urlparse(links[0]['href'])

    def get_uid_and_token(self):
        token = parse_qs(self.get_reset_link().query)['token'][0]
        uid, token = token.split('-', 1)
        return uid, token

    def test_recipients(self):
        self.assertRecipients([self.obj])

    def test_subject(self):
        self.assertSubject('Password reset for Test')

    def test_body(self):
        self.assertBodyContains("Seems you've requested a password reset for Test")

    def test_reset_link(self):
        link = self.get_reset_link()
        self.assertEqual(link.path, '/auth/set-password/')
        self.assertIn('token', parse_qs(link.query))

    def test_uid_and_token_valid(self):
        uid, token = self.get_uid_and_token()

        self.assertEqual(base36_to_int(uid), self.obj.pk)
        self.assertTrue(default_token_generator.check_token(self.obj, token))

    def test_reset_password_with_token(self):
        uid, token = self.get_uid_and_token()
        client = JSONAPITestClient()
        url = reverse('password-reset-confirm')
        data = {
            'data': {
                'type': 'reset-token-confirmations',
                'attributes': {
                    'token': f'{uid}-{token}',
                    'password': 'some-new-password',
                },
            }
        }

        response = client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(response.json()['data']['attributes']['jwt-token'])

        self.obj.refresh_from_db()
        self.assertTrue(self.obj.check_password('some-new-password'))
        self.assertFalse(self.obj.check_password('old-password'))

        # The token can only be used once
        response = client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
