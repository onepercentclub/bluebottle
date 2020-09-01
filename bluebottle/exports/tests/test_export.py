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
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import CustomMemberField, CustomMemberFieldSettings
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
        initiatives = InitiativeFactory.create_batch(10)
        for initiative in initiatives:
            EventFactory.create_batch(10, initiative=initiative)
            AssignmentFactory.create_batch(7, initiative=initiative)
            FundingFactory.create_batch(1, initiative=initiative)

        result = plain_export(Exporter, tenant=tenant, **data)
        book = xlrd.open_workbook(result)
        self.assertEqual(
            book.sheet_by_name('Users').ncols,
            11
        )
        self.assertEqual(
            book.sheet_by_name('Users').nrows,
            221
        )
        self.assertEqual(
            book.sheet_by_name('Initiatives').nrows,
            11
        )
        self.assertEqual(
            book.sheet_by_name('Funding activities').nrows,
            11
        )
        self.assertEqual(
            book.sheet_by_name('Events').nrows,
            101
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
            71
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
        users = BlueBottleUserFactory.create_batch(5)
        colour = CustomMemberFieldSettings.objects.create(
            name='colour',
            description='Favourite colour'
        )
        for user in users:
            CustomMemberField.objects.create(
                member=user,
                field=colour,
                value='Parblue Yellow'
            )
        initiative = InitiativeFactory.create(owner=users[0])
        assignment = AssignmentFactory.create(
            owner=users[1], initiative=initiative)
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
            'Favourite colour'
        )
        self.assertEqual(
            book.sheet_by_name('Users').cell(1, 11).value,
            'Parblue Yellow'
        )
        self.assertEqual(
            book.sheet_by_name('Task contributions').cell(0, 13).value,
            'Favourite colour'
        )
        self.assertEqual(
            book.sheet_by_name('Task contributions').cell(1, 13).value,
            'Parblue Yellow'
        )
