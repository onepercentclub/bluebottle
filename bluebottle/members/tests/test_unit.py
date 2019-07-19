from django.contrib.auth.password_validation import get_default_password_validators

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.members.models import CustomMemberField, CustomMemberFieldSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.utils import override_properties


class TestMemberPlatformSettings(BluebottleTestCase):

    def test_extra_member_fields(self):
        member = BlueBottleUserFactory.create()
        custom = CustomMemberFieldSettings.objects.create(name='Extra Info')

        # Check that the slug is set correctly
        self.assertEqual(custom.slug, 'extra-info')

        # Check that the project doesn't have extra field yet
        member.refresh_from_db()
        self.assertEqual(member.extra.count(), 0)

        CustomMemberField.objects.create(member=member, value='This is nice!', field=custom)

        # And now it should be there
        member.refresh_from_db()
        self.assertEqual(member.extra.count(), 1)


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
