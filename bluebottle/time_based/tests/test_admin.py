from datetime import timedelta

from django.urls import reverse

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.offices.tests.factories import LocationFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.time_based.models import DateActivity
from bluebottle.time_based.tests.factories import (
    PeriodActivityFactory, DateActivityFactory, DateActivitySlotFactory,
    DateParticipantFactory
)


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


class DateActivityAdminScenarioTestCase(BluebottleAdminTestCase):

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)
        self.owner = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory.create(owner=self.owner, status='approved')

    def test_staff_create_date_activity(self):
        self.activity_list_url = reverse('admin:time_based_dateactivity_changelist')
        page = self.app.get(self.activity_list_url)
        self.assertEqual(page.status, '200 OK')
        page = page.click('Add Activity on a date')
        self.assertEqual(page.status, '200 OK')
        form = page.forms['dateactivity_form']
        form['initiative'] = self.initiative.id
        form['title'] = 'Activity with multiple slots'
        form['description'] = 'Lorem etc'
        form['owner'] = self.owner.id
        form['review'] = 3
        page = form.submit().follow()
        self.assertEqual(page.status, '200 OK', 'Activity is added, now we can add a slot.')

        page = page.click('Activity with multiple slots', index=0)
        form = page.forms['dateactivity_form']

        self.admin_add_inline_form_entry(form, 'slots')

        form['slots-0-start_0'] = '2030-02-14'
        form['slots-0-start_1'] = '11:00'
        form['slots-0-duration_0'] = 1
        form['slots-0-duration_1'] = 30
        form['slots-0-is_online'] = True

        self.admin_add_inline_form_entry(form, 'slots')

        form['slots-1-start_0'] = '2030-02-13'
        form['slots-1-start_1'] = '14:00'
        form['slots-1-duration_0'] = 2
        form['slots-1-duration_1'] = 0
        form['slots-1-is_online'] = True

        page = form.submit().follow()
        self.assertEqual(page.status, '200 OK', 'Slots added to the activity')
        activity = DateActivity.objects.get(title='Activity with multiple slots')
        self.assertEqual(activity.slots.count(), 2)

    def test_add_slot_participants(self):
        activity = DateActivityFactory.create(initiative=self.initiative, slot_selection='free')
        DateActivitySlotFactory.create_batch(2, activity=activity)
        participant = DateParticipantFactory.create(activity=activity)
        self.assertEqual(len(participant.slot_participants.all()), 0)

        url = reverse('admin:time_based_dateparticipant_change', args=(participant.pk, ))

        page = self.app.get(url)
        form = page.forms['dateparticipant_form']

        form.fields['slot_participants-0-checked'][0].checked = True
        form.fields['slot_participants-1-checked'][0].checked = True
        form.fields['slot_participants-2-checked'][0].checked = True

        page = form.submit()
        page.forms['confirm'].submit().follow()

        self.assertEqual(len(participant.slot_participants.all()), 3)
