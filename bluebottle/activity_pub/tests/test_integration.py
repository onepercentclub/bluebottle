from requests import Request, Response
import mock
from urllib.parse import urlparse
from io import BytesIO
from datetime import datetime, timedelta

from django.db import connection
from django.test import Client as TestClient, override_settings
from django.test.client import RequestFactory

from bluebottle.activity_pub.effects import get_platform_actor
from bluebottle.activity_pub.models import Announce, GoodDeed, Follow, Accept, Event
from bluebottle.activity_pub.adapters import adapter

from bluebottle.cms.models import SitePlatformSettings
from bluebottle.clients.utils import LocalTenant
from bluebottle.clients.models import Client
from bluebottle.deeds.tests.factories import DeedFactory

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.projects import ThemeFactory
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


def do_request(url):
    client = ActivityPubClient()
    tenant = Client.objects.get(domain_url=urlparse(url).hostname)

    with LocalTenant(tenant):
        response = client.get(url, content_type='application.jrd+json')

    if response.status_code in (200, 201):
        return response.json()
    else:
        raise Exception(url, response.json())


adapter_mock = mock.patch(
    "bluebottle.activity_pub.adapters.JSONLDAdapter.execute", wraps=execute
)

webfinger_mock = mock.patch(
    "bluebottle.webfinger.client.WebFingerClient._do_request", wraps=do_request
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
        webfinger_mock.start()

    def tearDown(self):
        super().tearDown()
        adapter_mock.stop()
        webfinger_mock.stop()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class AdoptDeedTestCase(ActivityPubTestCase):
    def build_absolute_url(self, path):
        return connection.tenant.build_absolute_url(path)

    def setUp(self):
        super(AdoptDeedTestCase, self).setUp()

        self.user = BlueBottleUserFactory.create()

    def test_follow(self):
        platform_url = self.build_absolute_url('/')
        with LocalTenant(self.other_tenant):
            adapter.follow(platform_url)

        self.follow = Follow.objects.get(object=get_platform_actor())
        self.assertTrue(self.follow)

    def test_accept(self):
        self.test_follow()

        Accept.objects.create(
            object=self.follow
        )

        with LocalTenant(self.other_tenant):
            accept = Accept.objects.get(object=Follow.objects.get())
            self.assertTrue(accept)

    def test_publish_deed(self):
        self.test_accept()

        self.deed = DeedFactory.create(
            owner=self.user,
            image=ImageFactory.create(),
            start=(datetime.now() + timedelta(days=10)).date(),
            end=(datetime.now() + timedelta(days=20)).date()
        )

        self.deed.initiative.states.submit()
        self.deed.initiative.states.approve(save=True)

        self.deed.states.publish(save=True)

        with LocalTenant(self.other_tenant):
            event = Event.objects.get()

            self.assertEqual(event.name, self.deed.title)
            self.assertEqual(event.start_time.date(), self.deed.start)
            self.assertEqual(event.end_time.date(), self.deed.end)

    def test_publish_deed_to_closed_platform(self):
        with LocalTenant(self.other_tenant):
            MemberPlatformSettings.objects.create(closed=True)

        self.test_accept()

        deed = DeedFactory.create(owner=self.user, image=ImageFactory.create())

        deed.initiative.states.submit()
        deed.initiative.states.approve(save=True)

        deed.states.publish(save=True)

        with LocalTenant(self.other_tenant):
            event = Event.objects.get()

            self.assertTrue(event.name, deed.title)

    def test_publish_deed_no_accept(self):
        self.test_follow()

        deed = DeedFactory.create(owner=self.user, image=ImageFactory.create())

        deed.initiative.states.submit()
        deed.initiative.states.approve(save=True)

        deed.states.publish(save=True)

        with LocalTenant(self.other_tenant):
            self.assertEqual(Event.objects.count(), 0)

    def test_adopt_deed(self):
        self.test_publish_deed()

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as image_file:
            mock_response = Response()
            mock_response.raw = BytesIO(image_file.read())
            mock_response.status_code = 200

        with LocalTenant(self.other_tenant):
            event = GoodDeed.objects.get()

            request = RequestFactory().get('/')
            request.user = BlueBottleUserFactory.create()

            with mock.patch('requests.get', return_value=mock_response):
                deed = adapter.adopt(event, request)
                self.assertEqual(deed.title, self.deed.title)
                self.assertEqual(deed.start, self.deed.start)
                self.assertEqual(deed.end, self.deed.end)
                self.assertEqual(deed.origin, event)
                self.assertEqual(deed.image.origin, event.image)

                deed.theme = ThemeFactory.create()
                deed.states.submit()
                deed.states.approve(save=True)

        announce = Announce.objects.get()
        self.assertEqual(announce.object, self.deed.event)
