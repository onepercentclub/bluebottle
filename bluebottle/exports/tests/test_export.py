# -*- coding: utf-8 -*-
from datetime import timedelta

import xlrd
from django.db import connection
from django.test import override_settings
from django.utils.timezone import now

from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.exports.exporter import Exporter
from bluebottle.exports.tasks import plain_export
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.impact.models import ImpactType
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.initiatives.tests.factories import InitiativePlatformSettingsFactory
from bluebottle.segments.tests.factories import SegmentTypeFactory, SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    PeriodActivityFactory, PeriodParticipantFactory,
    DateActivityFactory, DeadlineActivityFactory, DeadlineParticipantFactory
)

TEST_EXPORT_SETTINGS = {
    'EXPORTDB_USE_CELERY': False
}


@override_settings(**TEST_EXPORT_SETTINGS)
class TestExportAdmin(BluebottleTestCase):
    def setUp(self):
        super(TestExportAdmin, self).setUp()

    def test_export(self):
        from_date = now() - timedelta(weeks=2)
        to_date = now() + timedelta(weeks=1)
        data = {
            'from_date': from_date,
            'to_date': to_date,
            '_save': 'Confirm'
        }
        tenant = connection.tenant
        initiatives = InitiativeFactory.create_batch(4)
        for initiative in initiatives:
            DateActivityFactory.create_batch(3, initiative=initiative)
            DeadlineActivityFactory.create_batch(2, initiative=initiative)
            FundingFactory.create_batch(1, initiative=initiative)
            DeedFactory.create_batch(1, initiative=initiative)

        result = plain_export(Exporter, tenant=tenant, **data)
        book = xlrd.open_workbook(result)
        self.assertEqual(
            book.sheet_by_name('Users').ncols,
            16
        )
        self.assertEqual(
            book.sheet_by_name('Users').nrows,
            41
        )
        self.assertEqual(
            book.sheet_by_name('Initiatives').nrows,
            5
        )
        self.assertEqual(
            book.sheet_by_name('Funding activities').nrows,
            5
        )
        self.assertEqual(
            book.sheet_by_name('Activities on a date').nrows,
            13
        )
        self.assertEqual(
            book.sheet_by_name('Activities on a date').cell(0, 8).value,
            'Status'
        )
        self.assertEqual(
            book.sheet_by_name('Activities on a date').cell(0, 9).value,
            'Office Location'
        )
        self.assertEqual(
            book.sheet_by_name('Activities on a date').cell(0, 10).value,
            'Skill'
        )

        print(book._sheet_names)
        self.assertEqual(
            book.sheet_by_name('Flexible activities').nrows,
            9
        )
        self.assertEqual(
            book.sheet_by_name('Flexible activities').cell(0, 16).value,
            'Preparation time'
        )
        self.assertEqual(
            book.sheet_by_name('Flexible activities').cell(0, 17).value,
            'Start'
        )
        self.assertEqual(
            book.sheet_by_name('Flexible activities').cell(0, 18).value,
            'Deadline'
        )

        self.assertEqual(
            book.sheet_by_name('Deed activities').nrows,
            5
        )
        self.assertEqual(
            book.sheet_by_name('Deed activities').cell(0, 8).value,
            'Status'
        )
        self.assertEqual(
            book.sheet_by_name('Deed activities').cell(0, 9).value,
            'Start'
        )
        self.assertEqual(
            book.sheet_by_name('Deed activities').cell(0, 10).value,
            'End'
        )
        self.assertEqual(
            book.sheet_by_name('Collection campaigns').cell(0, 8).value,
            'Status'
        )
        self.assertEqual(
            book.sheet_by_name('Collection campaigns').cell(0, 9).value,
            'Start'
        )
        self.assertEqual(
            book.sheet_by_name('Collection campaigns').cell(0, 10).value,
            'End'
        )

    def test_export_user_segments(self):
        from_date = now() - timedelta(weeks=2)
        to_date = now() + timedelta(weeks=1)
        users = BlueBottleUserFactory.create_batch(5)
        segment_type = SegmentTypeFactory.create(name='Department')
        engineering = SegmentFactory.create(segment_type=segment_type, name='Engineering')
        rubbish = SegmentFactory.create(segment_type=segment_type, name='Rubbish')
        users[0].segments.add(engineering)
        initiative = InitiativeFactory.create(owner=users[0])
        activity = DeadlineActivityFactory.create(
            owner=users[1],
            initiative=initiative
        )
        activity.segments.add(engineering)
        activity.segments.add(rubbish)
        DeadlineParticipantFactory.create(activity=activity, user=users[2])

        data = {
            'from_date': from_date,
            'to_date': to_date,
            '_save': 'Confirm'
        }
        tenant = connection.tenant
        result = plain_export(Exporter, tenant=tenant, **data)
        book = xlrd.open_workbook(result)

        self.assertEqual(
            book.sheet_by_name('Users').ncols,
            17
        )
        self.assertEqual(
            book.sheet_by_name('Users').cell(0, 16).value,
            'Department'
        )

        t = 0
        while t < book.sheet_by_name('Users').nrows:
            if book.sheet_by_name('Users').cell(t, 5).value == users[0].email:
                self.assertEqual(
                    book.sheet_by_name('Users').cell(t, 16).value,
                    'Engineering'
                )
            t += 1

        self.assertEqual(
            book.sheet_by_name('Flexible activities').cell(0, 21).value,
            'Department'
        )

        t = 0
        while t < book.sheet_by_name('Users').nrows:
            if book.sheet_by_name('Users').cell(t, 5).value == users[0].email:
                self.assertTrue(
                    book.sheet_by_name('Flexible activities').cell(t, 21).value in
                    ['Engineering, Rubbish', 'Rubbish, Engineering']
                )
            t += 1

    def test_export_impact(self):
        from_date = now() - timedelta(weeks=2)
        to_date = now() + timedelta(weeks=1)
        users = BlueBottleUserFactory.create_batch(5)

        co2 = ImpactType.objects.get(slug='co2')
        co2.active = True
        co2.save()
        water = ImpactType.objects.get(slug='water')
        water.active = True
        water.save()

        initiative = InitiativeFactory.create(owner=users[0])

        activity = DeadlineActivityFactory.create(
            owner=users[1],
            initiative=initiative
        )
        activity.goals.create(type=co2, realized=300)
        activity.goals.create(type=water, realized=750)

        data = {
            'from_date': from_date,
            'to_date': to_date,
            '_save': 'Confirm'
        }
        tenant = connection.tenant
        result = plain_export(Exporter, tenant=tenant, **data)
        book = xlrd.open_workbook(result)

        self.assertEqual(
            book.sheet_by_name('Flexible activities').cell(0, 21).value,
            u'Reduce CO\u2082 emissions'
        )
        self.assertEqual(
            book.sheet_by_name('Flexible activities').cell(1, 21).value,
            300
        )
        self.assertEqual(
            book.sheet_by_name('Flexible activities').cell(0, 22).value,
            u'Save water'
        )
        self.assertEqual(
            book.sheet_by_name('Flexible activities').cell(1, 22).value,
            750
        )

    def test_export_teams(self):
        self.settings = InitiativePlatformSettingsFactory.create(
            team_activities=False
        )
        from_date = now() - timedelta(weeks=2)
        to_date = now() + timedelta(weeks=1)

        initiative = InitiativeFactory.create()

        activity = PeriodActivityFactory.create(
            initiative=initiative
        )
        team_captain = PeriodParticipantFactory.create(activity=activity)
        PeriodParticipantFactory.create_batch(
            3, activity=activity, accepted_invite=team_captain.invite
        )
        data = {
            'from_date': from_date,
            'to_date': to_date,
            '_save': 'Confirm'
        }
        tenant = connection.tenant
        result = plain_export(Exporter, tenant=tenant, **data)
        book = xlrd.open_workbook(result)

        sheet = book.sheet_by_name('Participants to flexible activi')
        self.assertEqual(
            [field.value for field in tuple(sheet.get_rows())[0]],
            [
                'Participant ID', 'Activity Title', 'Initiative Title', 'Activity ID',
                'Activity status', 'User ID', 'Remote ID', 'Email', 'Status',
            ]
        )

        self.settings.team_activities = True
        self.settings.save()

        result = plain_export(Exporter, tenant=tenant, **data)
        book = xlrd.open_workbook(result)

        sheet = book.sheet_by_name('Participants to flexible activi')
        self.assertEqual(
            [field.value for field in tuple(sheet.get_rows())[0]],
            [
                'Participant ID', 'Activity Title', 'Initiative Title', 'Activity ID',
                'Activity status', 'User ID', 'Remote ID', 'Email', 'Status'
            ]
        )
