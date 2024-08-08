import datetime
from datetime import timedelta
from unittest import mock

from django.contrib.auth.password_validation import get_default_password_validators
from django.utils.timezone import now
from pytz import UTC

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.utils import override_properties
from bluebottle.initiatives.tests.factories import InitiativeFactory
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
            initiative=InitiativeFactory.create(status="approved")
        )
        activity.states.publish(save=True)
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

        self.assertEqual(
            self.user.hours_planned,
            2
        )
        self.assertEqual(
            self.user.hours_spent,
            3
        )

    def asserTimeSpent(self, when, expected):
        from bluebottle.members import models
        with mock.patch.object(models, 'now', return_value=when):
            self.assertEqual(
                self.user.hours_spent,
                expected
            )

    def test_hours_spent_fiscal_year(self):

        jan20 = datetime.datetime(2020, 1, 3, tzinfo=UTC)
        feb20 = datetime.datetime(2020, 2, 3, tzinfo=UTC)
        aug20 = datetime.datetime(2020, 8, 3, tzinfo=UTC)
        nov20 = datetime.datetime(2020, 11, 3, tzinfo=UTC)
        nov19 = datetime.datetime(2019, 11, 3, tzinfo=UTC)

        activity = DateActivityFactory.create(
            initiative=InitiativeFactory.create(status="approved")
        )
        activity.states.publish(save=True)

        slot1 = DateActivitySlotFactory.create(
            activity=activity,
            start=jan20,
            duration=timedelta(hours=1)
        )
        slot2 = DateActivitySlotFactory.create(
            activity=activity,
            start=feb20,
            duration=timedelta(hours=2)
        )
        slot3 = DateActivitySlotFactory.create(
            activity=activity,
            start=aug20,
            duration=timedelta(hours=4)
        )
        slot4 = DateActivitySlotFactory.create(
            activity=activity,
            start=nov20,
            duration=timedelta(hours=8)
        )
        slot5 = DateActivitySlotFactory.create(
            activity=activity,
            start=nov19,
            duration=timedelta(hours=20)
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

        SlotParticipantFactory.create(
            participant=participant,
            slot=slot3
        )

        SlotParticipantFactory.create(
            participant=participant,
            slot=slot4
        )

        SlotParticipantFactory.create(
            participant=participant,
            slot=slot5
        )

        platform_settings = MemberPlatformSettings.load()
        platform_settings.fiscal_month_offset = 0
        platform_settings.save()

        sep20 = datetime.datetime(2020, 9, 15, tzinfo=UTC)
        self.asserTimeSpent(sep20, 15)

        sep19 = datetime.datetime(2019, 9, 15, tzinfo=UTC)
        self.asserTimeSpent(sep19, 20)

        platform_settings.fiscal_month_offset = -4
        platform_settings.save()

        sep20 = datetime.datetime(2020, 9, 15, tzinfo=UTC)
        self.asserTimeSpent(sep20, 8)

        sep19 = datetime.datetime(2019, 9, 15, tzinfo=UTC)
        self.asserTimeSpent(sep19, 27)

        platform_settings.fiscal_month_offset = 2
        platform_settings.save()

        sep20 = datetime.datetime(2020, 9, 15, tzinfo=UTC)
        self.asserTimeSpent(sep20, 12)

        sep19 = datetime.datetime(2019, 9, 15, tzinfo=UTC)
        self.asserTimeSpent(sep19, 23)
