from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.forms import SharePublishForm
from bluebottle.activity_pub.models import Accept, Follower, Recipient
from bluebottle.activity_pub.tests.factories import OrganizationFactory
from bluebottle.activity_pub.utils import get_platform_actor
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.test.utils import BluebottleTestCase


class SharePublishFormTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        site_settings = SitePlatformSettings.load()
        site_settings.share_activities = ['supplier', 'consumer']
        site_settings.save()

        self.activity = DeedFactory.create(status='open')

    def create_consumer(self, accepted=True):
        platform_actor = get_platform_actor()
        consumer = OrganizationFactory.create()
        follow = Follower.objects.create(actor=consumer, object=platform_actor)
        if accepted:
            Accept.objects.create(actor=platform_actor, object=follow)
        return follow

    def share_with(self, *follows):
        adapter.sync(self.activity)
        publish = self.activity.activity_pub_model.create_set.first()
        for follow in follows:
            Recipient.objects.create(actor=follow.actor, activity=publish)

    def test_not_shared(self):
        consumer = self.create_consumer()
        self.create_consumer(accepted=False)

        form = SharePublishForm(obj=self.activity)

        self.assertEqual(form.fields['old_recipients'].initial, [])
        self.assertEqual(
            list(form.fields['recipients'].queryset), [consumer.actor]
        )

    def test_already_shared(self):
        shared = self.create_consumer()
        other = self.create_consumer()
        self.share_with(shared)

        form = SharePublishForm(obj=self.activity)

        self.assertEqual(form.fields['old_recipients'].initial, [shared.actor])
        self.assertEqual(
            list(form.fields['recipients'].queryset), [other.actor]
        )

    def test_shared_with_all(self):
        first = self.create_consumer()
        second = self.create_consumer()
        self.share_with(first, second)

        form = SharePublishForm(obj=self.activity)

        self.assertEqual(
            set(form.fields['old_recipients'].initial),
            {first.actor, second.actor}
        )
        self.assertEqual(list(form.fields['recipients'].queryset), [])
        self.assertEqual(
            form.fields['recipients'].help_text,
            'No additional partners available to share with.'
        )
