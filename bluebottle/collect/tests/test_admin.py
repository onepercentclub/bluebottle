from django.urls import reverse

from bluebottle.collect.models import CollectActivity
from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class CollectActivityAdminTestCase(BluebottleAdminTestCase):

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)
        self.initiative = InitiativeFactory.create(status='approved')
        self.owner = BlueBottleUserFactory.create()

    def test_admin_collect_feature_flag(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.activity_types = ['dateactivity', 'periodactivity']
        initiative_settings.save()
        url = reverse('admin:index')
        page = self.app.get(url)
        self.assertFalse('Collect' in page.text)

        initiative_settings.activity_types = ['dateactivity', 'periodactivity', 'collect']
        initiative_settings.save()
        url = reverse('admin:index')
        page = self.app.get(url)
        self.assertTrue('Collect' in page.text)

    def test_admin_create_collect(self):
        url = reverse('admin:collect_collectactivity_changelist')
        page = self.app.get(url)
        page = page.click('Add Collect Campaign')
        form = page.forms['collectactivity_form']
        form['title'] = 'A small step'
        form['initiative'] = self.initiative.id
        form['owner'] = self.owner.id
        form.submit()
        self.assertEqual(CollectActivity.objects.count(), 1)

    def test_admin_contributors(self):
        activity = CollectActivityFactory.create(
            target=10,
            realized=5,
            status='open'
        )
        CollectContributorFactory.create_batch(
            3,
            activity=activity
        )

        url = reverse('admin:collect_collectactivity_change', args=(activity.id,))
        page = self.app.get(url)
        self.assertTrue("contributors-0" in page.text)
        self.assertTrue("contributors-1" in page.text)
        self.assertTrue("contributors-2" in page.text)
        self.assertFalse("contributors-3" in page.text, "Only real contributors shoudl show")
