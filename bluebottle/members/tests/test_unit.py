from django.contrib.auth.password_validation import get_default_password_validators

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.utils import override_properties


class TestMonkeyPatchPasswordValidators(BluebottleTestCase):
    password_validators = [
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            'OPTIONS': {
                'min_length': 10,
            }
        },
    ]

    def test_validators_taken_from_settings_by_default(self):
        validators = get_default_password_validators()
        self.assertEqual(validators[0].min_length, 8)

    def test_validators_taken_from_properties(self):
        with override_properties(AUTH_PASSWORD_VALIDATORS=self.password_validators):
            validators = get_default_password_validators()
            self.assertEqual(validators[0].min_length, 10)

    def test_validators_different_tenant(self):
        with override_properties(AUTH_PASSWORD_VALIDATORS=self.password_validators):
            validators = get_default_password_validators()
            self.assertEqual(validators[0].min_length, 10)

            with LocalTenant(Client.objects.get(client_name='test2')):
                validators = get_default_password_validators()
                self.assertEqual(validators[0].min_length, 8)
