# -*- coding: utf-8 -*-
import xlrd
from datetime import timedelta
from django.db import connection
from django.test import override_settings
from django.utils.timezone import now

from bluebottle.assignments.tests.factories import AssignmentFactory, ApplicantFactory
from bluebottle.events.tests.factories import EventFactory
from bluebottle.exports.exporter import Exporter
from bluebottle.exports.tasks import plain_export
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.impact.models import ImpactType
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import CustomMemberField, CustomMemberFieldSettings
from bluebottle.segments.tests.factories import SegmentTypeFactory, SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase

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
            EventFactory.create_batch(3, initiative=initiative)
            AssignmentFactory.create_batch(2, initiative=initiative)
            FundingFactory.create_batch(1, initiative=initiative)

        result = plain_export(Exporter, tenant=tenant, **data)
        book = xlrd.open_workbook(result)
        self.assertEqual(
            book.sheet_by_name('Users').ncols,
            11
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
            book.sheet_by_name('Events').nrows,
            13
        )
        self.assertEqual(
            book.sheet_by_name('Events').cell(0, 13).value,
            'Start'
        )
        self.assertEqual(
            book.sheet_by_name('Events').cell(0, 14).value,
            'Time needed'
        )

        self.assertEqual(
            book.sheet_by_name('Tasks').nrows,
            9
        )
        self.assertEqual(
            book.sheet_by_name('Tasks').cell(0, 16).value,
            'Preparation time'
        )
        self.assertEqual(
            book.sheet_by_name('Tasks').cell(0, 17).value,
            'Start time'
        )
        self.assertEqual(
            book.sheet_by_name('Tasks').cell(0, 19).value,
            'End date'
        )

    def test_export_custom_user_fields(self):
        from_date = now() - timedelta(weeks=2)
        to_date = now() + timedelta(weeks=1)

        colour = CustomMemberFieldSettings.objects.create(
            name='colour',
            description='Favourite colour'
        )

        BlueBottleUserFactory.create_batch(2)
        user = BlueBottleUserFactory.create(email='markies@decanteclaer.nl')
        BlueBottleUserFactory.create_batch(2)

        CustomMemberField.objects.create(
            member=user,
            field=colour,
            value='Parblue Yellow'
        )
        initiative = InitiativeFactory.create(owner=user)
        assignment = AssignmentFactory.create(owner=user, initiative=initiative)
        ApplicantFactory.create(activity=assignment, user=user)

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
            12
        )
        t = 1
        while t < book.sheet_by_name('Users').nrows:
            if book.sheet_by_name('Users').cell(t, 5).value == 'markies@decanteclaer.nl':
                self.assertEqual(
                    book.sheet_by_name('Users').cell(t, 11).value,
                    'Parblue Yellow'
                )
            t += 1

        self.assertEqual(
            book.sheet_by_name('Task contributions').cell(0, 13).value,
            'Favourite colour'
        )
        self.assertEqual(
            book.sheet_by_name('Task contributions').cell(1, 13).value,
            'Parblue Yellow'
        )

    def test_export_user_segments(self):
        from_date = now() - timedelta(weeks=2)
        to_date = now() + timedelta(weeks=1)
        users = BlueBottleUserFactory.create_batch(5)
        segment_type = SegmentTypeFactory.create(name='Department')
        engineering = SegmentFactory.create(type=segment_type, name='Engineering')
        rubbish = SegmentFactory.create(type=segment_type, name='Rubbish')
        users[0].segments.add(engineering)
        initiative = InitiativeFactory.create(owner=users[0])
        assignment = AssignmentFactory.create(
            owner=users[1],
            initiative=initiative
        )
        assignment.segments.add(engineering)
        assignment.segments.add(rubbish)
        ApplicantFactory.create(activity=assignment, user=users[2])

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
            12
        )
        self.assertEqual(
            book.sheet_by_name('Users').cell(0, 11).value,
            'Department'
        )

        t = 0
        while t < book.sheet_by_name('Users').nrows:
            if book.sheet_by_name('Users').cell(t, 5).value == users[0].email:
                self.assertEqual(
                    book.sheet_by_name('Users').cell(t, 11).value,
                    'Engineering'
                )
            t += 1

        self.assertEqual(
            book.sheet_by_name('Tasks').cell(0, 23).value,
            'Department'
        )

        t = 0
        while t < book.sheet_by_name('Users').nrows:
            if book.sheet_by_name('Users').cell(t, 5).value == users[0].email:
                self.assertTrue(
                    book.sheet_by_name('Tasks').cell(t, 23).value in
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

        assignment = AssignmentFactory.create(
            owner=users[1],
            initiative=initiative
        )
        assignment.goals.create(type=co2, realized=300)
        assignment.goals.create(type=water, realized=750)

        data = {
            'from_date': from_date,
            'to_date': to_date,
            '_save': 'Confirm'
        }
        tenant = connection.tenant
        result = plain_export(Exporter, tenant=tenant, **data)
        book = xlrd.open_workbook(result)

        self.assertEqual(
            book.sheet_by_name('Tasks').cell(0, 23).value,
            u'Reduce CO\u2082 emissions'
        )
        self.assertEqual(
            book.sheet_by_name('Tasks').cell(1, 23).value,
            300
        )
        self.assertEqual(
            book.sheet_by_name('Tasks').cell(0, 24).value,
            u'Save water'
        )
        self.assertEqual(
            book.sheet_by_name('Tasks').cell(1, 24).value,
            750
        )
