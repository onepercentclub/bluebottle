from datetime import timedelta

from django.contrib.auth.password_validation import get_default_password_validators
from django.utils.timezone import now

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.utils import override_properties
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, DateActivitySlotFactory, DateParticipantFactory,
    SlotParticipantFactory
)


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


class MemberTestCase(BluebottleTestCase):

    def setUp(self):
        self.user = BlueBottleUserFactory.create()

    def test_no_hours_spent(self):
        self.assertEqual(
            self.user.hours_spent,
            0
        )
        self.assertEqual(
            self.user.hours_planned,
            0
        )

    def test_hours_spent(self):
        activity = DateActivityFactory.create(
            slot_selection='free'
        )
        slot1 = DateActivitySlotFactory.create(
            activity=activity,
            start=now() - timedelta(days=1),
            duration=timedelta(hours=3)
        )
        slot2 = DateActivitySlotFactory.create(
            activity=activity,
            start=now() + timedelta(days=1),
            duration=timedelta(hours=2)
        )

        participant = DateParticipantFactory.create(
            activity=activity,
            user=self.user
        )

        SlotParticipantFactory.create(
            participant=participant,
            slot=slot1
        )

        SlotParticipantFactory.create(
            participant=participant,
            slot=slot2
        )

        slot1.states.finish(save=True)

        self.assertEqual(
            self.user.hours_planned,
            2
        )
        self.assertEqual(
            self.user.hours_spent,
            3
        )
