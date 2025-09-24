import mock

from django.urls import reverse

from bluebottle.activity_pub.serializers.fields import RelatedActivityPubField
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.activity_pub.serializers.json_ld import ActorSerializer
from bluebottle.activity_pub.tests.factories import BluebottleOrganizationFactory, FollowFactory, OrganizationFactory


class RelatedActivityPubFieldTestCase(BluebottleTestCase):
    def setUp(self):
        self.settings = SitePlatformSettings.objects.create(
            organization=BluebottleOrganizationFactory.create()
        )
        self.field = RelatedActivityPubField(ActorSerializer)

    def test_to_representation(self):
        organization = OrganizationFactory.create()

        data = self.field.to_representation(
            organization
        )
        self.assertEqual(
            data,
            f'http://test.localhost{reverse("json-ld:organization", args=(organization.pk, ))}'
        )

    def test_to_internal_value(self):
        organization = OrganizationFactory.create()

        instance = self.field.to_internal_value(
            f'http://test.localhost{reverse("json-ld:organization", args=(organization.pk, ))}'
        )
        self.assertEqual(instance, organization)

    def test_to_internal_value_does_not_exist(self):
        instance = self.field.to_internal_value(
            f'http://test.localhost{reverse("json-ld:organization", args=("12345678", ))}'
        )
        self.assertIsNone(instance)

    def test_to_internal_value_wrong_type(self):
        follow = FollowFactory.create()

        instance = self.field.to_internal_value(
            f'http://test.localhost{reverse("json-ld:follow", args=(follow.pk, ))}'
        )
        self.assertIsNone(instance)

    def test_to_internal_value_wrong_url(self):
        FollowFactory.create()

        instance = self.field.to_internal_value(
            'http://test.localhost/does-not-exist'
        )
        self.assertIsNone(instance)

    def test_to_internal_external_url_already_sync(self):
        organization = OrganizationFactory.create(
            url='http://test2.localhost/api/activity-pub/organization/1'
        )
        instance = self.field.to_internal_value(organization.url)

        self.assertEqual(instance, organization)

    def test_to_internal_external_url(self):
        follow = FollowFactory.create()

        with mock.patch('bluebottle.activity_pub.adapters.JSONLDAdapter.sync', return_value=follow):
            instance = self.field.to_internal_value(
                'http://test2.localhost/api/activity-pub/organization/1'
            )

        self.assertEqual(instance, follow)
