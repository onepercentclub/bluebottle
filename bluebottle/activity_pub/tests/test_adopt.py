import httmock

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.serializers import ActivityPubSerializer
from bluebottle.activity_pub.tests.factories import CreateFactory, FollowFactory
from bluebottle.activity_pub.tests.test_federated_serializers import (
    DeadlineSerializerTestCase, image_mock,
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class AdoptDoGoodEventTestCase(DeadlineSerializerTestCase):
    def test_event_title_aliases_name(self):
        self.create()
        self.assertEqual(self.activity_pub_instance.title, self.activity_pub_instance.name)

    def test_adapter_adopt_with_owner(self):
        follow = FollowFactory.create(default_owner=BlueBottleUserFactory.create())
        owner = BlueBottleUserFactory.create()
        self.create()
        CreateFactory.create(object=self.activity_pub_instance, actor=follow.object)

        with httmock.HTTMock(image_mock):
            activity = adapter.adopt(self.activity_pub_instance, owner=owner)

        self.assertEqual(activity.title, self.activity_pub_instance.name)
        self.assertEqual(activity.owner, owner)

    def test_activity_pub_data_uses_name_not_title(self):
        self.create()
        data = ActivityPubSerializer(instance=self.activity_pub_instance).data
        self.assertIn('name', data)
        self.assertNotIn('title', data)
