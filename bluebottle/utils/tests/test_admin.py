import csv

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.db import models
from django.test.client import RequestFactory

from bluebottle.utils.admin import export_as_csv_action
from bluebottle.test.utils import BluebottleTestCase


class TestModel(models.Model):
    title = models.CharField(max_length=100)
    text = models.CharField(max_length=100)


class TestModelAdmin(admin.ModelAdmin):
    export_fields = (
        ('title', 'Just a title'),
        ('text', 'Some text'),
    )

    actions = (export_as_csv_action(fields=export_fields),)


class TestModelQuerySet(list):
    model = TestModel


class ExportAsCSVActionTest(BluebottleTestCase):
    """
    Integration tests for the User API.
    """

    def setUp(self):
        self.admin = TestModelAdmin(TestModel, AdminSite())
        self.request = RequestFactory().get('')

        super(ExportAsCSVActionTest, self).setUp()

    def test_export(self):
        response = self.admin.actions[0](
            self.admin,
            self.request,
            TestModelQuerySet([TestModel(title='bla', text='bli bloe')])
        )

        data = list(csv.reader(response.content.split('\n')))

        self.assertEqual(data[0], ['Just a title', 'Some text'])
        self.assertEqual(data[1], ['bla', 'bli bloe'])

    def test_export_escaped(self):
        response = self.admin.actions[0](
            self.admin,
            self.request,
            TestModelQuerySet([TestModel(title='@bla', text='+bli bloe')])
        )

        data = list(csv.reader(response.content.split('\n')))

        self.assertEqual(data[0], ['Just a title', 'Some text'])
        self.assertEqual(data[1], ['\'@bla', '\'+bli bloe'])
