from urllib.parse import urlparse
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key

from django.urls import reverse

from bluebottle.activity_pub.tests.factories import FollowFactory, PersonFactory, OrganizationFactory, PublicKeyFactory
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import (
    OrganizationFactory as BluebottleOrganizationFactory
)
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.activity_pub.models import ActivityPubModel, Person, Organization


class ActivityPubModelTestCase(BluebottleTestCase):
    def test_is_local(self):
        self.assertTrue(ActivityPubModel(iri=None).is_local)
        self.assertFalse(ActivityPubModel(iri='https://example.com').is_local)

    def test_pub_url(self):
        self.assertEqual(
            ActivityPubModel(iri='https://example.com').pub_url, 'https://example.com'
        )


class PersonTestCase(BluebottleTestCase):
    def setUp(self):
        self.model = PersonFactory.create()

    def test_pub_url(self):
        self.assertEqual(
            urlparse(self.model.pub_url).path, reverse('json-ld:person', args=(self.model.pk, ))
        )

    def test_from_object(self):
        member = BlueBottleUserFactory.create()

        model = Person.objects.from_model(member)
        self.assertTrue(model.inbox_id)
        self.assertTrue(model.outbox_id)
        self.assertTrue(model.public_key_id)
        self.assertTrue(model.name, member.full_name)
        self.assertTrue(model.member, member)


class OrganizationTestCase(BluebottleTestCase):
    def setUp(self):
        self.model = OrganizationFactory.create()

    def test_pub_url(self):
        self.assertEqual(
            urlparse(self.model.pub_url).path, reverse('json-ld:organization', args=(self.model.pk, ))
        )

    def test_from_object(self):
        organization = BluebottleOrganizationFactory.create()

        model = Organization.objects.from_model(organization)
        self.assertTrue(model.inbox_id)
        self.assertTrue(model.outbox_id)
        self.assertTrue(model.public_key_id)
        self.assertTrue(model.name, organization.name)
        self.assertTrue(model.organization, organization)


class PublicKeyTestCase(BluebottleTestCase):
    def setUp(self):
        self.model = PublicKeyFactory.create()

    def test_has_pem(self):
        self.assertTrue(self.model.public_key_pem)

    def test_has_private_key_pem(self):
        self.assertTrue(self.model.private_key)
        self.assertTrue(self.model.private_key.private_key_pem)

    def test_can_verify_signature(self):
        public_key = load_pem_public_key(
            bytes(self.model.public_key_pem, encoding='utf-8')
        )
        private_key = load_pem_private_key(
            bytes(self.model.private_key.private_key_pem, encoding='utf-8'), password=None
        )

        message = b'Some message'
        signature = private_key.sign(message)
        public_key.verify(signature=signature, data=message)


class FollowTestCase(BluebottleTestCase):
    def setUp(self):
        self.settings = SitePlatformSettings.objects.create(
            organization=BluebottleOrganizationFactory.create()
        )

        self.model = FollowFactory.create(actor=None)

    def test_actor(self):
        self.assertEqual(self.model.actor.organization, self.settings.organization)

    def test_recipients(self):
        self.assertEqual(
            [recipient.actor for recipient in self.model.recipients.all()],
            [self.model.object]
        )
