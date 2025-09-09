import json

from rest_framework import status

from django.db import connection, connections
from django.urls import reverse
from django.test import Client as TestClient, LiveServerTestCase
from django.core.management import call_command


from bluebottle.activity_pub.models import Person, Follow
from bluebottle.clients.utils import LocalTenant
from bluebottle.clients.models import Client
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import JSONAPITestClient


class ActivityPubClient(TestClient):
    def __init__(self, port):
        self.port = port
        super().__init__()

    def generic(self, *args, **kwargs):
        return super().generic(*args, **kwargs)

    def _base_environ(self, **request):
        env = super()._base_environ(**request)

        env['SERVER_NAME'] = connection.tenant.domain_url
        env['SERVER_PORT'] = self.port

        return env


class ActivityPubTestCase(LiveServerTestCase):
    def setUp(self):
        self.client = ActivityPubClient(self.server_thread.port)
        self.json_api_client = JSONAPITestClient()
        super().setUp()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        tenant = Client.objects.get(schema_name='test')
        cls.tenant = tenant
        connection.set_tenant(tenant)

        cls.other_tenant = Client.objects.get(schema_name='test2')

    def _fixture_teardown(self):
        # Allow TRUNCATE ... CASCADE and don't emit the post_migrate signal
        # when flushing only a subset of the apps
        for db_name in self._databases_names(include_mirrors=False):
            # Flush the database
            inhibit_post_migrate = (
                self.available_apps is not None
                or (  # Inhibit the post_migrate signal when using serialized
                    # rollback to avoid trying to recreate the serialized data.
                    self.serialized_rollback
                    and hasattr(connections[db_name], "_test_serialized_contents")
                )
            )
            call_command(
                "flush",
                verbosity=0,
                interactive=False,
                database=db_name,
                reset_sequences=False,
                allow_cascade=True,
                inhibit_post_migrate=inhibit_post_migrate,
            )


class PersonAPITestCase(ActivityPubTestCase):

    def build_absolute_url(self, path):
        return f'http://{connection.tenant.domain_url}:{self.server_thread.port}{path}'

    def setUp(self):
        super(PersonAPITestCase, self).setUp()

        user = BlueBottleUserFactory.create()
        self.person = Person.objects.from_model(user)

        self.person_url = self.build_absolute_url(reverse("Person", args=(self.person.pk, )))

    def test_get_person(self):
        response = self.client.get(self.person_url)

        self.assertEqual(
            response.json(),
            {
                '@context': ['https://www.w3.org/ns/activitystreams', 'https://w3id.org/security/v1'],
                'id': self.build_absolute_url(reverse('Person', args=(self.person.pk, ))),
                'inbox': self.build_absolute_url(reverse('Inbox', args=(self.person.inbox.pk, ))),
                'outbox': self.build_absolute_url(reverse('Outbox', args=(self.person.outbox.pk, ))),
                'name': self.person.name,
                'publicKey': {
                    'id': self.build_absolute_url(reverse('PublicKey', args=(self.person.public_key.pk, ))),
                    'publicKeyPem': self.person.public_key.public_key_pem
                },
                'type': 'Person'
            }
        )

    def test_follow(self):
        with LocalTenant(self.other_tenant):
            user = BlueBottleUserFactory.create()

            response = self.json_api_client.post(
                reverse('activity-pub-follow-list'),
                json.dumps({
                    'data': {
                        'type': 'activity-pub-follows',
                        'attributes': {
                            'url': self.person_url
                        }
                    }
                }),
                user=user,
                SERVER_PORT=self.client.port
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Follow.objects.get()
        )
