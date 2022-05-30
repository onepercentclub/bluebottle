import datetime
from datetime import timedelta

from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils.timezone import now
from pytz import UTC

from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.offices.tests.factories import LocationFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.time_based.admin import SkillAdmin
from bluebottle.time_based.models import DateActivity, Skill
from bluebottle.time_based.tests.factories import (
    PeriodActivityFactory, DateActivityFactory, DateActivitySlotFactory,
    DateParticipantFactory, SlotParticipantFactory
)


class PeriodActivityAdminTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)

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

    def test_team_activity_disabled(self):
        activity = PeriodActivityFactory.create()
        url = reverse('admin:time_based_periodactivity_change', args=(activity.id,))
        page = self.app.get(url, user=self.staff_member)
        form = page.forms[0]
        self.assertFalse('team_activity' in form.fields)
        self.assertEqual(activity.team_activity, 'individuals')

    def test_team_activity_enabled(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.team_activities = True
        initiative_settings.save()
        activity = PeriodActivityFactory.create()
        self.assertEqual(activity.team_activity, 'individuals')
        url = reverse('admin:time_based_periodactivity_change', args=(activity.id,))
        page = self.app.get(url, user=self.staff_member)
        form = page.forms[0]
        self.assertTrue('team_activity' in form.fields)
        form['team_activity'] = 'teams'
        form.submit()
        activity.refresh_from_db()
        self.assertEqual(activity.team_activity, 'teams')


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
        form['review'] = 'true'
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

        url = reverse('admin:time_based_dateparticipant_change', args=(participant.pk,))

        page = self.app.get(url)
        form = page.forms['dateparticipant_form']

        form.fields['slot_participants-0-checked'][0].checked = True
        form.fields['slot_participants-1-checked'][0].checked = True
        form.fields['slot_participants-2-checked'][0].checked = True

        page = form.submit()
        page.forms['confirm'].submit().follow()

        self.assertEqual(len(participant.slot_participants.all()), 3)

    def test_add_participants(self):
        activity = DateActivityFactory.create(initiative=self.initiative, status='open')
        DateParticipantFactory.create(activity=activity)
        url = reverse('admin:time_based_dateactivity_change', args=(activity.pk,))
        page = self.app.get(url)
        self.assertFalse(
            'First complete and submit the activity before managing participants.' in
            page.text
        )
        self.assertTrue(
            'Add another Participant' in
            page.text
        )
        activity.status = 'rejected'
        activity.save()
        page = self.app.get(url)
        self.assertTrue(
            'First complete and submit the activity before managing participants.' in
            page.text
        )


class DateParticipantAdminTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)
        self.supporter = BlueBottleUserFactory.create()
        self.participant = DateParticipantFactory.create(status='participant')
        slot = self.participant.activity.slots.first()
        SlotParticipantFactory.create(
            participant=self.participant,
            slot=slot
        )

    def test_adjusting_contribution(self):
        self.url = reverse('admin:time_based_dateparticipant_change', args=(self.participant.id,))
        page = self.app.get(self.url)
        self.assertEqual(page.status, '200 OK')
        form = page.forms[0]
        form['contributions-0-value_0'] = 0
        form['contributions-0-value_1'] = 0
        page = form.submit()
        self.assertEqual(page.status, '200 OK')
        self.assertTrue('This field is required.' in page.text)


class TestSkillAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestSkillAdmin, self).setUp()
        self.site = AdminSite()
        self.skill_admin = SkillAdmin(Skill, self.site)
        self.client.force_login(self.superuser)
        InitiativeFactory.create()

    def test_theme_admin_staf(self):
        url = reverse('admin:time_based_skill_changelist')
        response = self.app.get(url, user=self.staff_member)
        self.assertEqual(response.status, '200 OK')


class DateActivitySlotAdminTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.activity1 = DateActivityFactory.create(
            slot_selection='free',
            capacity=None,
            slots=[]
        )
        DateActivitySlotFactory.create(
            activity=self.activity1,
            start=now() + timedelta(days=4),
            capacity=2
        )
        DateActivitySlotFactory.create(
            activity=self.activity1,
            start=now() + timedelta(days=4),
            capacity=3
        )
        DateActivitySlotFactory.create(
            activity=self.activity1,
            start=now() - timedelta(days=3),
            capacity=None
        )
        self.activity2 = DateActivityFactory.create(
            slot_selection='all',
            capacity=5,
            slots=[]
        )
        DateActivitySlotFactory.create(
            activity=self.activity2,
            start=now() + timedelta(days=5),
            capacity=None
        )
        DateActivitySlotFactory.create(
            activity=self.activity2,
            start=now() - timedelta(days=1),
            capacity=None
        )
        self.app.set_user(self.staff_member)

    def test_adjusting_contribution(self):
        self.url = reverse('admin:time_based_dateactivityslot_changelist')
        page = self.app.get(self.url)
        self.assertEqual(page.status, '200 OK')
        self.assertTrue('5 slots' in page.text)
        self.assertTrue('<td class="field-attendee_limit">3</td>' in page.text)
        self.assertTrue('<td class="field-attendee_limit">-</td>' in page.text)
        self.assertTrue('<td class="field-attendee_limit">5</td>' in page.text)

        self.assertTrue('<td class="field-required">Required</td>' in page.text)
        self.assertTrue('<td class="field-required">Optional</td>' in page.text)
        page = page.click('Upcoming')
        self.assertTrue('3 slots' in page.text)
        page = page.click('Required')
        self.assertTrue('1 slot' in page.text)


class DuplicateSlotAdminTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.activity = DateActivityFactory.create(
            slots=[]
        )
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
            start=datetime.datetime(2022, 5, 15, tzinfo=UTC)
        )
        self.url = reverse('admin:time_based_dateactivityslot_change', args=(self.slot.id,))
        self.app.set_user(self.staff_member)

    def test_duplicate_daily(self):
        page = self.app.get(self.url)
        self.assertEqual(page.status, '200 OK')
        page = page.click('Repeat this slot')
        h3 = page.html.find('h3')
        self.assertEqual(h3.text.strip(), 'Warning')
        form = page.forms[0]
        form["interval"] = "day"
        form["end"] = '2022-05-20'
        page = form.submit()
        self.assertEqual(
            page.location,
            f'/en/admin/time_based/dateactivity/{self.activity.id}/change/#/tab/inline_0/'
        )
        page = page.follow()
        self.assertContains(page, '6 Results')
        self.assertEqual(self.activity.slots.count(), 6)
        self.assertEqual(
            [str(s.start.date()) for s in self.activity.slots.all()],
            [
                '2022-05-15', '2022-05-16', '2022-05-17',
                '2022-05-18', '2022-05-19', '2022-05-20',
            ]
        )
