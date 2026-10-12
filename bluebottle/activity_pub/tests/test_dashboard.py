from io import BytesIO

from django.core.files import File
from django.test.client import RequestFactory
from django.urls import reverse

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.dashboard import ActivityPubConnections, AppIndexDashboard
from bluebottle.activity_pub.models import Accept, Follower, Following, Recipient
from bluebottle.activity_pub.tests.factories import OrganizationFactory
from bluebottle.activity_pub.utils import get_platform_actor
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class ActivityPubDashboardTestCase(BluebottleAdminTestCase):
    def setUp(self):
        super().setUp()
        site_settings = SitePlatformSettings.load()
        with open('./bluebottle/utils/tests/test_images/upload.svg', 'rb') as image:
            site_settings.logo = File(BytesIO(image.read()), name='upload.svg')
        site_settings.share_activities = ['supplier', 'consumer']
        site_settings.save()

        self.request = RequestFactory().get(reverse('admin:index'))
        self.request.user = self.superuser

    def create_supplier(self, accepted=True):
        platform_actor = get_platform_actor()
        supplier = OrganizationFactory.create()
        follow = Following.objects.create(actor=platform_actor, object=supplier)
        if accepted:
            Accept.objects.create(actor=supplier, object=follow)
        return follow

    def create_consumer(self, accepted=True):
        platform_actor = get_platform_actor()
        consumer = OrganizationFactory.create()
        follow = Follower.objects.create(actor=consumer, object=platform_actor)
        if accepted:
            Accept.objects.create(actor=platform_actor, object=follow)
        return follow

    def create_published_activity(self, follow, status='open'):
        activity = DeedFactory.create(status=status)
        adapter.sync(activity)
        publish = activity.activity_pub_model.create_set.first()
        Recipient.objects.create(actor=follow.actor, activity=publish, send=True)
        return activity

    def test_connections_widget_lists_suppliers_and_consumers(self):
        supplier = self.create_supplier(accepted=True)
        consumer = self.create_consumer(accepted=False)
        self.create_published_activity(consumer, status='open')

        widget = ActivityPubConnections()
        widget.init_with_context({'request': self.request})

        self.assertTrue(widget.show_suppliers)
        self.assertTrue(widget.show_consumers)
        self.assertEqual(len(widget.suppliers), 1)
        self.assertEqual(len(widget.consumers), 1)
        self.assertEqual(widget.suppliers[0]['name'], str(supplier.object))
        self.assertTrue(widget.suppliers[0]['accepted'])
        self.assertFalse(widget.consumers[0]['accepted'])
        self.assertEqual(widget.consumers[0]['shared_activities'], 1)

    def test_app_dashboard_includes_connections_widget(self):
        dashboard = AppIndexDashboard({'request': self.request}, app_label='activity_pub')
        self.assertTrue(
            any(isinstance(module, ActivityPubConnections) for module in dashboard.children)
        )
