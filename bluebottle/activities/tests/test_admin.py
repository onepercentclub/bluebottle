import json
from django.urls import reverse

from bluebottle.activity_pub.tests.factories import CreateFactory, DoGoodEventFactory, OrganizationFactory
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.offices.tests.factories import LocationFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.time_based.tests.factories import DateActivityFactory


class DateActivityAdminTestCase(BluebottleAdminTestCase):

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)

    def test_admin_submit_when_complete(self):
        activity = DateActivityFactory.create(title='')
        url = reverse('admin:time_based_dateactivity_change', args=(activity.id,))

        page = self.app.get(url)

        form = page.forms['dateactivity_form']
        form['title'] = 'Complete activity'
        form['description'] = json.dumps({'html': 'Description', 'delta': ''})
        form.submit()

        activity.refresh_from_db()

        self.assertEqual(activity.status, 'submitted')

    def test_admin_approve_when_complete(self):
        activity = DateActivityFactory.create(title='')

        activity.initiative.states.submit()
        activity.initiative.states.approve(save=True)

        url = reverse('admin:time_based_dateactivity_change', args=(activity.id,))

        page = self.app.get(url)

        form = page.forms['dateactivity_form']
        form['title'] = 'Complete activity'
        form['description'] = json.dumps({'html': 'Description', 'delta': ''})
        form.submit()

        activity.refresh_from_db()

        self.assertEqual(activity.status, 'open')

    def test_admin_not_submit_when_incomplete(self):
        activity = DateActivityFactory.create(title='', description='')
        url = reverse('admin:time_based_dateactivity_change', args=(activity.id,))

        page = self.app.get(url)

        form = page.forms['dateactivity_form']
        form['title'] = 'Complete activity'
        page = form.submit()

        activity.refresh_from_db()

        self.assertEqual(activity.status, 'draft')

    def test_admin_office_location(self):
        LocationFactory.create()
        activity = DateActivityFactory.create()
        url = reverse('admin:time_based_dateactivity_change', args=(activity.id,))

        page = self.app.get(url)
        form = page.forms['dateactivity_form']
        self.assertTrue('office_location' in form.fields)


class ActivityAdminPartnerTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.superuser)
        self.url = reverse('admin:activities_activity_changelist')

    def test_partner_filter_and_column_when_consumer(self):
        site_settings = SitePlatformSettings.load()
        site_settings.share_activities = ['consumer']
        site_settings.save()

        partner = OrganizationFactory.create(name='DLL Partner')
        activity = DateActivityFactory.create()
        event = DoGoodEventFactory.create(adopted=activity)
        CreateFactory.create(actor=partner, object=event)

        page = self.app.get(self.url)
        self.assertIn('Partner', page.text)
        self.assertIn('DLL Partner', page.text)

        filtered = self.app.get(f'{self.url}?partner={partner.pk}')
        self.assertIn(activity.title, filtered.text)

    def test_partner_filter_hidden_when_not_consumer(self):
        site_settings = SitePlatformSettings.load()
        site_settings.share_activities = ['supplier']
        site_settings.save()

        page = self.app.get(self.url)
        self.assertNotIn('?partner=', page.text)
        filters = page.html.find(id='changelist-filter')
        if filters:
            self.assertNotIn('Partner', filters.text)
