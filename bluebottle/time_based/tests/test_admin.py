import json
import datetime
from datetime import timedelta

from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils.timezone import now

from bluebottle.files.tests.factories import PrivateDocumentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.time_based.admin import SkillAdmin
from bluebottle.time_based.models import DateActivity, Skill
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, DateActivitySlotFactory,
    DateParticipantFactory, DateRegistrationFactory
)


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
        page = page.forms[1].submit().follow()
        self.assertTrue(
            "0 Activities on a date" in page.text
        )
        self.assertEqual(DateActivity.objects.count(), 0)


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
        form['description'] = json.dumps({'html': 'Lorem etc', 'delta': ''})
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

        self.admin_add_inline_form_entry(form, 'slots')

        form['slots-1-start_0'] = '2030-02-13'
        form['slots-1-start_1'] = '14:00'
        form['slots-1-duration_0'] = 2
        form['slots-1-duration_1'] = 0

        page = form.submit().follow()

        self.assertEqual(page.status, '200 OK', 'Slots added to the activity')
        activity = DateActivity.objects.get(title='Activity with multiple slots')
        self.assertEqual(activity.slots.count(), 2)

    def test_add_registration(self):
        activity = DateActivityFactory.create(initiative=self.initiative)
        DateActivitySlotFactory.create(activity=activity)

        self.assertEqual(activity.registrations.count(), 0)
        url = reverse('admin:time_based_dateactivity_change', args=(activity.pk,))
        page = self.app.get(url)
        form = page.forms['dateactivity_form']
        self.admin_add_inline_form_entry(form, 'registrations')
        form['registrations-0-user'] = BlueBottleUserFactory.create().pk
        form['registrations-0-activity'] = activity.pk
        page = form.submit()
        form = page.forms['confirm']
        form.submit()

        self.assertEqual(activity.registrations.count(), 1)

    def test_add_participant(self):
        activity = DateActivityFactory.create(initiative=self.initiative)
        slot = DateActivitySlotFactory.create(activity=activity)

        self.assertEqual(slot.participants.count(), 0)

        url = reverse('admin:time_based_dateactivityslot_change', args=(slot.pk,))
        page = self.app.get(url)
        form = page.forms['dateactivityslot_form']

        self.admin_add_inline_form_entry(form, 'participants')
        form['participants-0-user'] = BlueBottleUserFactory.create().pk
        form['participants-0-slot'] = slot.pk
        page = form.submit()
        form = page.forms['confirm']
        form.submit()

        self.assertEqual(slot.participants.count(), 1)


class DateParticipantAdminTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)
        self.supporter = BlueBottleUserFactory.create()
        self.registration = DateRegistrationFactory.create(status='accepted')
        slot = self.registration.activity.slots.first()
        self.participant = DateParticipantFactory.create(
            registration=self.registration,
            slot=slot
        )

    def test_adjusting_contribution(self):
        self.url = reverse('admin:time_based_dateparticipant_change', args=(self.participant.id,))
        page = self.app.get(self.url)
        self.assertEqual(page.status, '200 OK')
        form = page.forms[1]
        form['contributions-0-value_0'] = 0
        form['contributions-0-value_1'] = 0
        page = form.submit()
        self.assertEqual(page.status, '200 OK')
        self.assertTrue('This field is required.' in page.text)

    def test_document(self):
        self.registration.document = PrivateDocumentFactory.create()
        self.registration.save()

        self.url = reverse('admin:time_based_dateregistration_change', args=(self.registration.id,))
        page = self.app.get(self.url)
        self.assertEqual(page.status, '200 OK')

        link = page.html.find("a", {'class': 'private-document-link'})

        self.assertTrue(
            link.attrs['href'].startswith(
                reverse('registration-document', args=(self.registration.pk, ))
            )
        )


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

        page = page.click('Upcoming')
        self.assertTrue('3 slots' in page.text)


class DuplicateSlotAdminTestCase(BluebottleAdminTestCase):
    extra_environ = {}

    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.activity = DateActivityFactory.create(
            slots=[]
        )
        self.activity.initiative.states.submit()
        self.activity.initiative.states.approve(save=True)
        self.activity.refresh_from_db()
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
            start=now() - datetime.timedelta(days=1)
        )
        self.activity.states.publish(save=True)
        self.url = reverse('admin:time_based_dateactivityslot_change', args=(self.slot.id,))
        self.app.set_user(self.staff_member)

    def test_duplicate_daily(self):
        page = self.app.get(self.url)
        self.assertEqual(page.status, '200 OK')
        page = page.click('Repeat this slot')

        warning = page.html.find("div", {'class': 'warning'})
        self.assertEqual(
            warning.text.strip(),
            (
                'Ensure the time slot details are correct before repeating, as bulk changes won’t '
                'be possible later.'
            )
        )
        form = page.forms[1]
        form["interval"] = "day"
        form["end"] = str((now() + datetime.timedelta(days=4)).date())
        page = form.submit()
        self.assertEqual(
            page.location,
            f'/en/admin/time_based/dateactivity/{self.activity.id}/change/#/tab/inline_0/'
        )
        page = page.follow()
        self.assertContains(page, '6 Results')
        self.assertEqual(self.activity.slots.count(), 6)
        self.assertEqual(
            [s.start.date() for s in self.activity.slots.all()],
            [datetime.date.today() + timedelta(days=offset) for offset in range(-1, 5)]
        )

    def test_duplicate_reopen(self):
        self.assertEqual(self.activity.status, 'expired')
        page = self.app.get(self.url)
        page = page.click('Repeat this slot')
        form = page.forms[1]
        form["interval"] = "day"
        form["end"] = str((now() + datetime.timedelta(days=4)).date())
        page = form.submit()
        self.assertEqual(
            page.location,
            f'/en/admin/time_based/dateactivity/{self.activity.id}/change/#/tab/inline_0/'
        )
        page = page.follow()
        self.assertContains(page, '6 Results')
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.slots.count(), 6)
        self.assertEqual(self.activity.status, 'open')
