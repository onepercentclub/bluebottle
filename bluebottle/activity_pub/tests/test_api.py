from django.db import connection
from django.urls import reverse

from bluebottle.activity_pub.models import Person

from bluebottle.cms.models import SitePlatformSettings
from bluebottle.clients.utils import LocalTenant
from bluebottle.clients.models import Client

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import JSONAPITestClient, BluebottleTestCase
from bluebottle.test.factory_models.organizations import OrganizationFactory


class ActivityPubTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()

        self.other_tenant = Client.objects.get(schema_name='test2')

        SitePlatformSettings.objects.create(
            organization=OrganizationFactory.create()
        )

        with LocalTenant(self.other_tenant):
            SitePlatformSettings.objects.create(
                organization=OrganizationFactory.create()
            )

        self.json_api_client = JSONAPITestClient()


class PersonAPITestCase(ActivityPubTestCase):
    def build_absolute_url(self, path):
        return connection.tenant.build_absolute_url(path)

    def setUp(self):
        super(PersonAPITestCase, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.person = Person.objects.from_model(self.user)
        self.person_url = self.build_absolute_url(reverse("json-ld:person", args=(self.person.pk, )))

    def test_get_inbox(self):
        inbox_url = self.build_absolute_url(reverse("json-ld:inbox", args=(self.person.inbox.pk, )))
        response = self.client.get(inbox_url)

        self.assertEqual(
            response.json(),
            {
                '@context': [
                    'https://www.w3.org/ns/activitystreams',
                    'https://w3id.org/security/v1',
                    'https://goodup.com/json-ld'
                ],
                'id': self.build_absolute_url(reverse('json-ld:inbox', args=(self.person.inbox.pk, ))),
                'type': 'Inbox'
            }
        )

    def test_get_person(self):
        response = self.client.get(self.person_url)

        self.assertEqual(
            response.json(),
            {
                '@context': [
                    'https://www.w3.org/ns/activitystreams',
                    'https://w3id.org/security/v1',
                    'https://goodup.com/json-ld'
                ],
                'id': self.build_absolute_url(reverse('json-ld:person', args=(self.person.pk, ))),
                'inbox': self.build_absolute_url(reverse('json-ld:inbox', args=(self.person.inbox.pk, ))),
                'outbox': self.build_absolute_url(reverse('json-ld:outbox', args=(self.person.outbox.pk, ))),
                'name': self.person.name,
                'publicKey': {
                    'id': self.build_absolute_url(reverse('json-ld:public-key', args=(self.person.public_key.pk, ))),
                    'publicKeyPem': self.person.public_key.public_key_pem
                },
                'type': 'Person'
            }
        )
