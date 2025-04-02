import json
from django.urls import reverse

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
        page = form.submit()
        form = page.forms[1]
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
        page = form.submit()
        form = page.forms[1]
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
