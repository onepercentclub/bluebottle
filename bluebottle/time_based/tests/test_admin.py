from datetime import timedelta

from django.urls import reverse

from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.time_based.tests.factories import PeriodActivityFactory


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
