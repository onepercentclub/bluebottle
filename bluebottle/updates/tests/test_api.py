from django.core import mail
from django.urls import reverse
from rest_framework import status

from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase
from bluebottle.updates.models import Update
from bluebottle.updates.serializers import UpdateSerializer
from bluebottle.updates.tests.factories import UpdateFactory


class UpdateListTestCase(APITestCase):
    url = reverse('update-list')
    serializer = UpdateSerializer
    factory = UpdateFactory
    fields = ['activity', 'message', 'images', 'parent', 'notify', 'pinned', 'video_url']

    def setUp(self):
        super().setUp()

        self.defaults = {
            'activity': DeedFactory.create(),
            'parent': self.factory.create(),
            'video_url': '',
            'message': 'Some message',
            'notify': False,
            'pinned': False,
        }

    def test_create(self):
        mail.outbox = []
        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('author', self.user)
        self.assertRelationship('activity', [self.defaults['activity']])
        self.assertRelationship('parent', [self.defaults['parent']])

        self.assertAttribute('message', self.defaults['message'])
        self.assertAttribute('created')
        self.assertEqual(len(mail.outbox), 2)

    def test_create_without_message(self):

        mail.outbox = []
        self.defaults['message'] = ''
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_without_message_with_video(self):
        mail.outbox = []
        self.defaults['message'] = ''
        self.defaults['video_url'] = 'https://www.youtube.com/watch?v=9J68GxO02xE'
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)

    def test_patch_pinned(self):
        mail.outbox = []
        self.defaults['message'] = 'Yeah'
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)

        self.model = Update.objects.get(pk=self.response.json()['data']['id'])
        self.url = reverse('update-detail', args=(self.model.pk,))
        self.perform_update(to_change={'pinned': True}, user=self.user)
        self.assertStatus(status.HTTP_200_OK)

    def test_create_notify(self):
        DeedParticipantFactory.create(activity=self.defaults['activity'])
        mail.outbox = []
        self.defaults['notify'] = True

        self.perform_create(user=self.defaults['activity'].owner)

        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('author', self.defaults['activity'].owner)
        self.assertRelationship('activity', [self.defaults['activity']])
        self.assertRelationship('parent', [self.defaults['parent']])

        self.assertAttribute('message', self.defaults['message'])
        self.assertAttribute('created')
        self.assertEqual(len(mail.outbox), 2)
        title = self.defaults['activity'].title
        self.assertEqual(mail.outbox[0].subject, f"New update from '{title}'")

    def test_create_notify_not_owner(self):
        self.defaults['notify'] = True

        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_create_pinned_not_owner(self):
        self.defaults['pinned'] = True

        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_create_nested_reply(self):
        self.defaults['parent'].parent = UpdateFactory.create()
        self.defaults['parent'].save()

        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_images(self):
        file_path = './bluebottle/files/tests/files/test-image.png'
        with open(file_path, 'rb') as test_file:
            response = self.client.post(
                reverse('image-list'),
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="some_file.png"',
                user=self.user
            )

            file_data = response.json()['data']

        file_path2 = './bluebottle/files/tests/files/Test-Image2.PNG'
        with open(file_path2, 'rb') as test_file:
            response = self.client.post(
                reverse('image-list'),
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="test-image2.png"',
                user=self.user
            )

            file_data2 = response.json()['data']

        self.defaults['images'] = [file_data['id'], file_data2['id']]

        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_201_CREATED)
        self.assertIncluded('author', self.user)
        self.assertIncluded('images', self.defaults['images'])
        self.assertRelationship('activity', [self.defaults['activity']])
        self.assertAttribute('message', self.defaults['message'])

    def test_create_no_message_with_images(self):
        file_path = './bluebottle/files/tests/files/test-image.png'
        with open(file_path, 'rb') as test_file:
            response = self.client.post(
                reverse('image-list'),
                test_file.read(),
                content_type="image/png",
                HTTP_CONTENT_DISPOSITION='attachment; filename="some_file.png"',
                user=self.user
            )

            file_data = response.json()['data']

        self.defaults['images'] = [file_data['id']]
        self.defaults['message'] = ''
        self.perform_create(user=self.user)
        self.assertStatus(status.HTTP_201_CREATED)

    def test_create_incomplete(self):
        self.defaults['message'] = ''
        self.perform_create(user=self.user)

        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_create_anonymous(self):
        self.perform_create()
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_get(self):
        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_405_METHOD_NOT_ALLOWED)


class UpdateDetailView(APITestCase):
    serializer = UpdateSerializer
    factory = UpdateFactory

    fields = ['activity', 'author', 'messsage', 'images', 'parent']

    def setUp(self):
        super().setUp()

        self.defaults = {
            'activity': DeedFactory.create(),
            'author': self.user,
            'message': 'some message'
        }
        self.model = self.factory.create(**self.defaults)
        self.url = reverse('update-detail', args=(self.model.pk,))

    def test_get(self):
        self.perform_get(user=self.user)

        self.assertStatus(status.HTTP_200_OK)

        self.assertIncluded('author')
        self.assertAttribute('message')
        self.assertRelationship('activity')

    def test_get_other_user(self):

        self.perform_get(user=BlueBottleUserFactory.create())
        self.assertStatus(status.HTTP_200_OK)

    def test_get_anonymous(self):
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)

    def test_put(self):
        new_message = 'New message'
        self.perform_update({'message': new_message}, user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('message', new_message)

    def test_put_anonymous(self):
        new_message = 'New message'
        self.perform_update({'message': new_message})
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_put_other_user(self):
        new_message = 'New message'
        self.perform_update({'message': new_message}, user=BlueBottleUserFactory.create())
        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_put_staff(self):
        new_message = 'New message'
        self.perform_update({'message': new_message}, user=BlueBottleUserFactory.create(is_staff=True))
        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('message', new_message)

    def test_put_change_author(self):
        self.perform_update({'author': BlueBottleUserFactory.create()}, user=self.user)

        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_put_change_activity(self):
        self.perform_update({'author': DeedFactory.create()}, user=self.user)

        self.assertStatus(status.HTTP_400_BAD_REQUEST)

    def test_delete(self):
        self.perform_delete(user=self.user)

        self.assertStatus(status.HTTP_204_NO_CONTENT)

        self.assertRaises(self.model.__class__.DoesNotExist, self.model.refresh_from_db)

    def test_delete_other_user(self):
        self.perform_delete(user=BlueBottleUserFactory.create())

        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_delete_anonymous(self):
        self.perform_delete()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)


class ActivityUpdateListTestCase(APITestCase):
    factory = DeedFactory
    serializer = UpdateSerializer

    def setUp(self):
        self.activity = DeedFactory.create()

        self.models = UpdateFactory.create_batch(5, activity=self.activity)
        for model in self.models:
            UpdateFactory.create_batch(3, parent=model)

        self.url = reverse('activity-update-list', args=(self.activity.pk,))
        UpdateFactory.create_batch(3)

    def test_get(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(len(self.models))
        self.assertObjectList(self.models)

        self.assertAttribute('message')
        self.assertAttribute('created')
        self.assertAttribute('pinned')
        self.assertRelationship('activity')
        self.assertIncluded('author')

        for update in self.models:
            for reply in update.replies.all():
                self.assertIncluded('replies', reply)

    def test_get_pinned(self):
        pinned_models = UpdateFactory.create_batch(2, activity=self.activity, pinned=True)
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)
        self.assertObjectList(pinned_models + self.models)

    def test_get_logged_in(self):
        self.perform_get(user=BlueBottleUserFactory.create())

        self.assertStatus(status.HTTP_200_OK)
        self.assertTotal(len(self.models))

    def test_closed_platform(self):
        with self.closed_site():
            self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_closed_platform_logged_in(self):
        with self.closed_site():
            self.perform_get(user=BlueBottleUserFactory.create())

        self.assertStatus(status.HTTP_200_OK)
