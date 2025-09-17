from requests import Request
import mock
from urllib.parse import urlparse
from io import BytesIO

from django.db import connection
from django.urls import reverse
from django.test import Client as TestClient


from bluebottle.activity_pub.admin import OrganizationSerializer
from bluebottle.activity_pub.effects import get_platform_actor
from bluebottle.activity_pub.models import Person, Follow, Accept, Event
from bluebottle.activity_pub.adapters import adapter

from bluebottle.cms.models import SitePlatformSettings
from bluebottle.clients.utils import LocalTenant
from bluebottle.clients.models import Client
from bluebottle.deeds.tests.factories import DeedFactory

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import JSONAPITestClient, BluebottleTestCase
from bluebottle.files.tests.factories import ImageFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory


class ActivityPubClient(TestClient):
    def _base_environ(self, **request):
        env = super()._base_environ(**request)

        env['SERVER_NAME'] = connection.tenant.domain_url
        env['content_type'] = 'application/ld+json'

        return env

    def post(self, *args, **kwargs):
        kwargs['content_type'] = 'application/ld+json'
        return super().post(*args, **kwargs)


def execute(method, url, data=None, auth=None):
    client = ActivityPubClient()

    headers = {'content_type': 'application/ld+json'}

    if auth:
        request = Request(
            method.upper(), url, data=data, headers={'content-type': 'application/ld+json'}
        ).prepare()

        signed = auth(request)
        headers.update(signed.headers)

    tenant = Client.objects.get(domain_url=urlparse(url).hostname)

    with LocalTenant(tenant):
        response = getattr(client, method)(url, data=data, headers=headers)

    if response.status_code in (200, 201):
        return (BytesIO(response.content), response.accepted_media_type)
    else:
        raise Exception(url, response.json())


adapter_mock = mock.patch(
    "bluebottle.activity_pub.adapters.JSONLDAdapter.execute", wraps=execute
)


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

        self.client = ActivityPubClient()
        self.json_api_client = JSONAPITestClient()

        adapter_mock.start()

    def tearDown(self):
        super().tearDown()
        adapter_mock.stop()


class PersonAPITestCase(ActivityPubTestCase):
    def build_absolute_url(self, path):
        return connection.tenant.build_absolute_url(path)

    def setUp(self):
        super(PersonAPITestCase, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.person = Person.objects.from_model(self.user)

    def test_get_inbox(self):
        inbox_url = self.build_absolute_url(reverse("json-ld:inbox", args=(self.person.inbox.pk, )))
        response = self.client.get(inbox_url)

        self.assertEqual(
            response.json(),
            {
                '@context': ['https://www.w3.org/ns/activitystreams', 'https://w3id.org/security/v1'],
                'id': self.build_absolute_url(reverse('json-ld:inbox', args=(self.person.inbox.pk, ))),
                'type': 'Person'
            }
        )

    def test_get_person(self):
        response = self.client.get(self.person_url)

        self.assertEqual(
            response.json(),
            {
                '@context': ['https://www.w3.org/ns/activitystreams', 'https://w3id.org/security/v1'],
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

    def test_follow(self):
        organization = get_platform_actor()
        organization_url = self.build_absolute_url(
            reverse("json-ld:organization", args=(organization.pk, ))
        )

        with LocalTenant(self.other_tenant):
            object = adapter.sync(
                organization_url, serializer=OrganizationSerializer
            )

            follow = Follow.objects.create(
                actor=get_platform_actor(),
                object=object
            )

            adapter.publish(follow)

        self.follow = Follow.objects.get(object=organization)
        self.assertTrue(self.follow)

    def test_accept(self):
        self.test_follow()

        accept = Accept.objects.create(
            actor=get_platform_actor(),
            object=self.follow
        )

        adapter.publish(accept)

        with LocalTenant(self.other_tenant):
            accept = Accept.objects.get(object=Follow.objects.get())

            self.assertTrue(accept)

    def test_publish_deed(self):
        self.test_accept()

        deed = DeedFactory.create(owner=self.user, image=ImageFactory.create())

        deed.initiative.states.submit()
        deed.initiative.states.approve(save=True)

        deed.states.publish(save=True)

        with LocalTenant(self.other_tenant):
            event = Event.objects.get()

            self.assertTrue(event.name, deed.title)
