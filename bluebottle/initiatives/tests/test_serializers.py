from django.test import RequestFactory

from bluebottle.initiatives.serializers import MemberSerializer
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class MemberSerializerTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.request = RequestFactory().get('/')
        self.request.user = BlueBottleUserFactory.create()

    def get_serializer(self, member, display_member_names='first_name', owners=None):
        return MemberSerializer(
            member,
            context={
                'request': self.request,
                'display_member_names': display_member_names,
                'owners': owners or [],
            },
        )

    def test_empty_first_name_initials_when_hiding_last_name(self):
        member = BlueBottleUserFactory.create(first_name='', last_name='Doe')

        data = self.get_serializer(member).to_representation(member)

        self.assertIsNone(data['last_name'])
        self.assertEqual(data['initials'], '')
        self.assertEqual(data['full_name'], '')

    def test_first_name_initials_when_hiding_last_name(self):
        member = BlueBottleUserFactory.create(first_name='Jane', last_name='Doe')

        data = self.get_serializer(member).to_representation(member)

        self.assertIsNone(data['last_name'])
        self.assertEqual(data['initials'], 'J')
        self.assertEqual(data['full_name'], 'Jane')
