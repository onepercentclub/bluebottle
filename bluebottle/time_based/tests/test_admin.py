from datetime import timedelta

from django.urls import reverse

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.offices.tests.factories import LocationFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.time_based.models import DateActivity
from bluebottle.time_based.tests.factories import PeriodActivityFactory, DateActivityFactory


class PeriodActivityAdminTestCase(BluebottleAdminTestCase):

    def test_list_shows_duration(self):
        PeriodActivityFactory.create(duration_period='weeks', duration=timedelta(hours=4))
        PeriodActivityFactory.create(duration_period='months', duration=timedelta(hours=8))
        PeriodActivityFactory.create(duration_period=None, duration=timedelta(hours=1))
        PeriodActivityFactory.create(duration_period='overall', duration=timedelta(hours=10))
        url = reverse('admin:time_based_periodactivity_changelist')
        response = self.app.get(url, user=self.staff_member)
        self.assertEqual(response.status, '200 OK')
        self.assertTrue('4 hours per week' in response.text)
        self.assertTrue('8 hours per month' in response.text)
        self.assertFalse('8 hours per months' in response.text)
        self.assertTrue('1 hour' in response.text)
        self.assertFalse('1 hours' in response.text)
        self.assertTrue('10 hours' in response.text)


class DateActivityAdminTestCase(BluebottleAdminTestCase):

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)

    def test_admin_can_delete_activity(self):
        activity = DateActivityFactory.create()
        self.assertEqual(DateActivity.objects.count(), 1)
        url = reverse('admin:time_based_dateactivity_change', args=(activity.id,))
        page = self.app.get(url)
        page = page.click('Delete')
        self.assertFalse(
            "your account doesn't have permission to delete the following types of objects" in page.text,
            "Deleting an activity should not result in an error."
        )
        self.assertTrue(
            "All of the following related items will be deleted" in page.text
        )
        page = page.forms[0].submit().follow()
        self.assertTrue(
            "0 Activities on a date" in page.text
        )
        self.assertEqual(DateActivity.objects.count(), 0)

    def test_list_activities_office(self):
        office = LocationFactory.create(name='Schin op Geul')
        initiative = InitiativeFactory.create(location=office)
        PeriodActivityFactory.create(initiative=initiative)
        url = reverse('admin:time_based_periodactivity_changelist')
        response = self.app.get(url)
        self.assertEqual(len(response.html.find_all("a", string="Schin op Geul")), 2)
        response = self.app.get(url)
        self.assertEqual(len(response.html.find_all("a", string="Schin op Geul")), 2)
