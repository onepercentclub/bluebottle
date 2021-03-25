from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from bluebottle.initiatives.tests.factories import InitiativeFactory

from bluebottle.deeds.models import Deed
from bluebottle.initiatives.models import InitiativePlatformSettings
from django.urls import reverse

from bluebottle.test.utils import BluebottleAdminTestCase


class DeedAdminTestCase(BluebottleAdminTestCase):

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)
        self.initiative = InitiativeFactory.create(status='approved')
        self.owner = BlueBottleUserFactory.create()

    def test_admin_deeds_feature_flag(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.activity_types = ['funding', 'dateactivity', 'periodactivity']
        initiative_settings.save()
        url = reverse('admin:index')
        page = self.app.get(url)
        self.assertFalse('Deeds' in page.text)

        initiative_settings.activity_types = ['deed', 'funding', 'dateactivity', 'periodactivity']
        initiative_settings.save()
        url = reverse('admin:index')
        page = self.app.get(url)
        self.assertTrue('Deeds' in page.text)

    def test_admin_create_deed(self):
        url = reverse('admin:deeds_deed_changelist')
        page = self.app.get(url)
        page = page.click('Add Deed')
        form = page.forms['deed_form']
        form['title'] = 'A small step'
        form['initiative'] = self.initiative.id
        form['owner'] = self.owner.id
        form.submit()
        self.assertEqual(Deed.objects.count(), 1)
