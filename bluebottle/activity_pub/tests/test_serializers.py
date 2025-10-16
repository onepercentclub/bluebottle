from django.urls import reverse

from rest_framework import exceptions

from bluebottle.cms.models import SitePlatformSettings
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.activity_pub.serializers.json_ld import ActivitySerializer
from bluebottle.activity_pub.tests.factories import BluebottleOrganizationFactory, FollowFactory, OrganizationFactory


class PolymorphicSerializerTestCase(BluebottleTestCase):
    serializer_class = ActivitySerializer

    def setUp(self):
        self.settings = SitePlatformSettings.objects.create(
            organization=BluebottleOrganizationFactory.create()
        )

        self.follow = FollowFactory.create()

    def test_to_representation(self):
        data = self.serializer_class().to_representation(
            self.follow
        )

        self.assertEqual(
            data,
            {
                'id': f'http://test.localhost{reverse("json-ld:follow", args=(self.follow.pk, ))}',
                'type': 'Follow',
                'actor': f'http://test.localhost{reverse("json-ld:organization", args=(self.follow.actor.pk, ))}',
                'object': f'http://test.localhost{reverse("json-ld:organization", args=(self.follow.object.pk, ))}'
            }
        )

    def test_to_representation_no_matching_serializer(self):
        with self.assertRaises(TypeError):
            self.serializer_class().to_representation(
                self.follow.object
            )

    def test_to_internal_value(self):
        data = {
            'id': f'http://test.localhost{reverse("json-ld:follow", args=(self.follow.pk, ))}',
            'type': 'Follow',
            'actor': f'http://test.localhost{reverse("json-ld:organization", args=(self.follow.actor.pk, ))}',
            'object': f'http://test.localhost{reverse("json-ld:organization", args=(self.follow.object.pk, ))}'
        }
        internal_value = self.serializer_class().to_internal_value(data)

        self.assertEqual(internal_value['id'], str(self.follow.pub_url))
        self.assertEqual(internal_value['object']['id'], self.follow.object.pub_url)
        self.assertEqual(internal_value['actor']['id'], self.follow.actor.pub_url)

    def test_to_internal_value_no_matching_serializer(self):
        data = {
            'id': f'http://test.localhost{reverse("json-ld:follow", args=(self.follow.pk, ))}',
            'type': 'Organization',
            'actor': f'http://test.localhost{reverse("json-ld:organization", args=(self.follow.actor.pk, ))}',
            'object': f'http://test.localhost{reverse("json-ld:organization", args=(self.follow.object.pk, ))}'
        }

        with self.assertRaises(exceptions.ValidationError):
            self.serializer_class().to_internal_value(data)

    def test_to_internal_value_invalid(self):
        data = {
            'id': f'http://test.localhost{reverse("json-ld:follow", args=(self.follow.pk, ))}',
            'type': 'Follow',
            'object': f'http://test.localhost{reverse("json-ld:organization", args=(self.follow.object.pk, ))}'
        }
        with self.assertRaises(exceptions.ValidationError):
            self.serializer_class().to_internal_value(data)

    def test_create(self):
        actor = OrganizationFactory.create()
        object = OrganizationFactory()

        serializer = self.serializer_class(data={
            'type': 'Follow',
            'actor': f'http://test.localhost{reverse("json-ld:organization", args=(actor.pk, ))}',
            'object': f'http://test.localhost{reverse("json-ld:organization", args=(object.pk, ))}'
        })
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()

        self.assertEqual(instance.object, object)
        self.assertEqual(instance.actor, actor)

        self.assertTrue(instance.pk)

    def test_create_no_matching_serializer(self):
        actor = OrganizationFactory.create()
        object = OrganizationFactory()

        serializer = self.serializer_class(data={
            'type': 'Organization',
            'actor': f'http://test.localhost{reverse("json-ld:organization", args=(actor.pk, ))}',
            'object': f'http://test.localhost{reverse("json-ld:organization", args=(object.pk, ))}'
        })

        with self.assertRaises(exceptions.ValidationError):
            serializer.is_valid()

    def test_create_invalid(self):
        actor = OrganizationFactory.create()

        serializer = self.serializer_class(data={
            'type': 'Follow',
            'actor': f'http://test.localhost{reverse("json-ld:organization", args=(actor.pk, ))}',
        })

        self.assertFalse(serializer.is_valid())

    def test_update(self):
        actor = OrganizationFactory.create()

        serializer = self.serializer_class(
            instance=self.follow,
            data={
                'type': 'Follow',
                'actor': f'http://test.localhost{reverse("json-ld:organization", args=(actor.pk, ))}',
                'object': f'http://test.localhost{reverse("json-ld:organization", args=(self.follow.object.pk, ))}',
            }
        )
        self.assertTrue(serializer.is_valid())

        serializer.save()

        self.follow.refresh_from_db()
        self.assertEqual(self.follow.actor, actor)

    def test_update_wrong_instance(self):
        actor = OrganizationFactory.create()

        serializer = self.serializer_class(
            instance=self.follow.actor,
            data={
                'type': 'Follow',
                'actor': f'http://test.localhost{reverse("json-ld:organization", args=(actor.pk, ))}',
                'object': f'http://test.localhost{reverse("json-ld:organization", args=(self.follow.object.pk, ))}',
            }
        )
        with self.assertRaises(TypeError):
            serializer.is_valid()
