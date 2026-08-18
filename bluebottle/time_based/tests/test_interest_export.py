from datetime import date, timedelta
from io import BytesIO

from django.urls import reverse
from django.utils.timezone import now
from openpyxl import load_workbook
from rest_framework import status

from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase
from bluebottle.time_based.views.exports import format_slot_worksheet_title
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
    InterestFactory,
    PeriodicActivityFactory,
    PeriodicParticipantFactory,
    ScheduleActivityFactory,
    ScheduleParticipantFactory,
    TeamFactory,
)


INTEREST_HEADERS = ('Email', 'Name', 'Registration Date', 'Status')


def get_sheet_by_title(workbook, title):
    for sheet in workbook.worksheets:
        if sheet.title == title:
            return sheet
    return None


def get_interest_sheets(workbook):
    return [sheet for sheet in workbook.worksheets if sheet.title.startswith('Interested')]


def get_interest_sheet_for_slot(workbook, slot):
    return get_sheet_by_title(
        workbook,
        format_slot_worksheet_title(slot, prefix='Interested '),
    )


class ActivityExportSetUpMixin:
    factory = None
    participant_factory = None
    url_name = None
    activity_defaults = {}

    def setUpActivityExport(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = True
        initiative_settings.save()

        self.activity = self.factory.create(
            **self.activity_defaults,
            review_title='document',
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
        )
        self.participant_factory.create_batch(
            4,
            activity=self.activity,
        )

        response = self.client.get(
            reverse(self.url_name, args=(self.activity.pk,)),
            HTTP_AUTHORIZATION="JWT {0}".format(self.activity.owner.get_jwt_token())
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.url = response.json()['data']['attributes']['participants-export-url']['url']


class InterestExportAssertionsMixin:
    def create_interest(self, **kwargs):
        return InterestFactory.create(activity=self.activity, slot=None, **kwargs)

    def download_export(self, user=None):
        self.perform_get(user=user or self.activity.owner)
        self.assertStatus(status.HTTP_200_OK)
        return load_workbook(filename=BytesIO(self.response.content))

    def assert_interest_sheet(self, workbook, interests):
        sheet = get_sheet_by_title(workbook, 'Interested')
        self.assertIsNotNone(sheet)
        self.assertEqual(tuple(sheet.values)[0], INTEREST_HEADERS)

        rows = list(sheet.values)[1:]
        self.assertEqual(len(rows), len(interests))

        for row, interest in zip(rows, interests):
            self.assertEqual(row[0], interest.user.email)
            self.assertEqual(row[1], interest.user.full_name)
            self.assertEqual(row[2], interest.created.strftime('%d-%m-%y %H:%M'))
            self.assertEqual(row[3], 'Interested')

    def assert_no_interest_sheet(self, workbook):
        self.assertEqual(get_interest_sheets(workbook), [])

    def assert_interest_sheet_for_slot(self, workbook, slot, interests):
        sheet = get_interest_sheet_for_slot(workbook, slot)
        self.assertIsNotNone(sheet)
        self.assertEqual(tuple(sheet.values)[0], INTEREST_HEADERS)

        rows = list(sheet.values)[1:]
        self.assertEqual(len(rows), len(interests))

        for row, interest in zip(rows, interests):
            self.assertEqual(row[0], interest.user.email)
            self.assertEqual(row[1], interest.user.full_name)
            self.assertEqual(row[2], interest.created.strftime('%d-%m-%y %H:%M'))
            self.assertEqual(row[3], 'Interested')


class DeadlineInterestExportTestCase(
    ActivityExportSetUpMixin, InterestExportAssertionsMixin, APITestCase
):
    factory = DeadlineActivityFactory
    participant_factory = DeadlineParticipantFactory
    url_name = 'deadline-detail'

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }

    def setUp(self):
        super().setUp()
        self.setUpActivityExport()

    def test_export_includes_interested_members(self):
        interests = [
            self.create_interest(user=BlueBottleUserFactory.create()),
            self.create_interest(user=BlueBottleUserFactory.create()),
        ]

        workbook = self.download_export()

        self.assertEqual(len(workbook.worksheets), 2)
        self.assert_interest_sheet(workbook, interests)

    def test_export_without_interested_members(self):
        workbook = self.download_export()

        self.assertEqual(len(workbook.worksheets), 1)
        self.assert_no_interest_sheet(workbook)

    def test_export_orders_interested_members_by_created_date(self):
        older_user = BlueBottleUserFactory.create()
        newer_user = BlueBottleUserFactory.create()
        older = self.create_interest(
            user=older_user,
            created=now() - timedelta(days=2),
        )
        newer = self.create_interest(
            user=newer_user,
            created=now() - timedelta(days=1),
        )

        workbook = self.download_export()

        self.assert_interest_sheet(workbook, [older, newer])

    def test_export_excludes_slot_level_interests(self):
        date_activity = DateActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
        )
        slot = DateActivitySlotFactory.create(activity=date_activity)
        included = self.create_interest(user=BlueBottleUserFactory.create())
        InterestFactory.create(
            activity=self.activity,
            slot=slot,
            user=BlueBottleUserFactory.create(),
        )

        workbook = self.download_export()

        self.assertEqual(len(workbook.worksheets), 2)
        self.assert_interest_sheet(workbook, [included])


class InterestExportPermissionTestCase(
    ActivityExportSetUpMixin, InterestExportAssertionsMixin, APITestCase
):
    factory = DeadlineActivityFactory
    participant_factory = DeadlineParticipantFactory
    url_name = 'deadline-detail'

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }

    def setUp(self):
        super().setUp()
        self.setUpActivityExport()
        self.create_interest(user=BlueBottleUserFactory.create())

    def test_export_invalid_signature(self):
        self.url = self.url + '111'
        self.perform_get(user=self.activity.owner)

        self.assertStatus(status.HTTP_404_NOT_FOUND)

    def test_export_url_not_available_to_other_user(self):
        other_user = BlueBottleUserFactory.create()

        response = self.client.get(
            reverse(self.url_name, args=(self.activity.pk,)),
            HTTP_AUTHORIZATION="JWT {0}".format(other_user.get_jwt_token())
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(
            response.json()['data']['attributes']['participants-export-url']
        )

    def test_export_url_disabled_when_setting_off(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = False
        initiative_settings.save()

        response = self.client.get(
            reverse(self.url_name, args=(self.activity.pk,)),
            HTTP_AUTHORIZATION="JWT {0}".format(self.activity.owner.get_jwt_token())
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(
            response.json()['data']['attributes']['participants-export-url']
        )


class ScheduleInterestExportTestCase(
    ActivityExportSetUpMixin, InterestExportAssertionsMixin, APITestCase
):
    factory = ScheduleActivityFactory
    participant_factory = ScheduleParticipantFactory
    url_name = 'schedule-detail'

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
    }

    def setUp(self):
        super().setUp()
        self.setUpActivityExport()

    def test_export_includes_interested_members(self):
        interest = self.create_interest(user=BlueBottleUserFactory.create())

        workbook = self.download_export()

        self.assertEqual(len(workbook.worksheets), 2)
        self.assert_interest_sheet(workbook, [interest])


class PeriodicInterestExportTestCase(
    ActivityExportSetUpMixin, InterestExportAssertionsMixin, APITestCase
):
    factory = PeriodicActivityFactory
    participant_factory = PeriodicParticipantFactory
    url_name = 'periodic-detail'

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
        'duration': timedelta(hours=4),
    }

    def setUp(self):
        super().setUp()
        self.setUpActivityExport()

    def test_export_includes_interested_members(self):
        interest = self.create_interest(user=BlueBottleUserFactory.create())

        workbook = self.download_export()

        self.assertEqual(len(workbook.worksheets), 2)
        self.assert_interest_sheet(workbook, [interest])


class TeamScheduleInterestExportTestCase(
    ActivityExportSetUpMixin, InterestExportAssertionsMixin, APITestCase
):
    factory = ScheduleActivityFactory
    participant_factory = TeamFactory
    url_name = 'schedule-detail'

    activity_defaults = {
        'start': date.today() + timedelta(days=10),
        'deadline': date.today() + timedelta(days=20),
        'team_activity': 'teams',
    }

    def setUp(self):
        super().setUp()
        self.setUpActivityExport()

    def test_export_includes_interested_members(self):
        workbook_without_interests = self.download_export()
        self.assertEqual(len(get_interest_sheets(workbook_without_interests)), 0)

        interest = self.create_interest(user=BlueBottleUserFactory.create())
        workbook = self.download_export()

        self.assert_interest_sheet(workbook, [interest])


class DateActivityInterestExportTestCase(
    ActivityExportSetUpMixin, InterestExportAssertionsMixin, APITestCase
):
    factory = DateActivityFactory
    participant_factory = DateParticipantFactory
    url_name = 'date-detail'

    activity_defaults = {}

    def setUp(self):
        super().setUp()
        self.setUpActivityExport()

    def test_export_includes_slot_interested_members(self):
        first_slot = self.activity.slots.first()
        last_slot = self.activity.slots.last()
        first_interest = InterestFactory.create(
            activity=self.activity,
            slot=first_slot,
            user=BlueBottleUserFactory.create(),
        )
        last_interest = InterestFactory.create(
            activity=self.activity,
            slot=last_slot,
            user=BlueBottleUserFactory.create(),
        )

        workbook = self.download_export()

        self.assertEqual(len(workbook.worksheets), 7)
        self.assertEqual(len(get_interest_sheets(workbook)), 2)
        self.assert_interest_sheet_for_slot(workbook, first_slot, [first_interest])
        self.assert_interest_sheet_for_slot(workbook, last_slot, [last_interest])

    def test_export_skips_interested_tab_for_slots_without_interests(self):
        slot = self.activity.slots.first()
        interest = InterestFactory.create(
            activity=self.activity,
            slot=slot,
            user=BlueBottleUserFactory.create(),
        )

        workbook = self.download_export()

        self.assertEqual(len(get_interest_sheets(workbook)), 1)
        self.assert_interest_sheet_for_slot(workbook, slot, [interest])

    def test_export_interested_tab_title_includes_slot_info(self):
        slot = self.activity.slots.first()
        InterestFactory.create(
            activity=self.activity,
            slot=slot,
            user=BlueBottleUserFactory.create(),
        )

        workbook = self.download_export()

        expected_title = format_slot_worksheet_title(slot, prefix='Interested ')
        self.assertIsNotNone(get_sheet_by_title(workbook, expected_title))

    def test_export_orders_interested_members_per_slot(self):
        slot = self.activity.slots.first()
        older = InterestFactory.create(
            activity=self.activity,
            slot=slot,
            user=BlueBottleUserFactory.create(),
            created=now() - timedelta(days=2),
        )
        newer = InterestFactory.create(
            activity=self.activity,
            slot=slot,
            user=BlueBottleUserFactory.create(),
            created=now() - timedelta(days=1),
        )

        workbook = self.download_export()

        self.assert_interest_sheet_for_slot(workbook, slot, [older, newer])

    def test_export_excludes_interests_on_past_slots(self):
        past_slot = DateActivitySlotFactory.create(
            activity=self.activity,
            start=now() - timedelta(days=1),
            status='open',
        )
        future_slot = self.activity.slots.filter(start__gt=now()).first()
        if not future_slot:
            future_slot = self.activity.slots.first()
            future_slot.start = now() + timedelta(days=10)
            future_slot.save()

        InterestFactory.create(
            activity=self.activity,
            slot=past_slot,
            user=BlueBottleUserFactory.create(),
        )
        future_interest = InterestFactory.create(
            activity=self.activity,
            slot=future_slot,
            user=BlueBottleUserFactory.create(),
        )

        workbook = self.download_export()

        self.assertIsNone(get_interest_sheet_for_slot(workbook, past_slot))
        self.assert_interest_sheet_for_slot(workbook, future_slot, [future_interest])
        self.assertIsNone(get_sheet_by_title(
            workbook,
            format_slot_worksheet_title(past_slot),
        ))

    def test_export_includes_interests_on_past_slots_when_succeeded(self):
        self.activity.status = 'succeeded'
        self.activity.save()

        past_slot = DateActivitySlotFactory.create(
            activity=self.activity,
            start=now() - timedelta(days=1),
            status='finished',
        )
        interest = InterestFactory.create(
            activity=self.activity,
            slot=past_slot,
            user=BlueBottleUserFactory.create(),
        )

        workbook = self.download_export()

        self.assert_interest_sheet_for_slot(workbook, past_slot, [interest])


class SlotInterestExportTestCase(InterestExportAssertionsMixin, APITestCase):
    def setUp(self):
        super().setUp()
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_participant_exports = True
        initiative_settings.save()

        self.manager = BlueBottleUserFactory.create()
        self.activity = DateActivityFactory.create(
            initiative=InitiativeFactory.create(status='approved'),
            status='open',
            review=False,
            owner=self.manager,
        )
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
            start=now() + timedelta(days=10),
        )
        self.other_slot = DateActivitySlotFactory.create(
            activity=self.activity,
            start=now() + timedelta(days=20),
        )
        self.interest = InterestFactory.create(
            activity=self.activity,
            slot=self.slot,
            user=BlueBottleUserFactory.create(),
        )

        response = self.client.get(
            reverse('date-slot-detail', args=(self.slot.pk,)),
            HTTP_AUTHORIZATION="JWT {0}".format(self.manager.get_jwt_token())
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.url = response.json()['data']['attributes']['participants-export-url']['url']

    def test_export_includes_interested_members(self):
        workbook = self.download_export(user=self.manager)

        self.assertEqual(len(workbook.worksheets), 2)
        self.assert_interest_sheet(workbook, [self.interest])

    def test_export_excludes_interests_from_other_slots(self):
        InterestFactory.create(
            activity=self.activity,
            slot=self.other_slot,
            user=BlueBottleUserFactory.create(),
        )

        workbook = self.download_export(user=self.manager)

        self.assertEqual(len(workbook.worksheets), 2)
        self.assert_interest_sheet(workbook, [self.interest])

    def test_export_without_interests_on_this_slot(self):
        self.interest.delete()
        InterestFactory.create(
            activity=self.activity,
            slot=self.other_slot,
            user=BlueBottleUserFactory.create(),
        )

        workbook = self.download_export(user=self.manager)

        self.assertEqual(len(workbook.worksheets), 1)
        self.assert_no_interest_sheet(workbook)
