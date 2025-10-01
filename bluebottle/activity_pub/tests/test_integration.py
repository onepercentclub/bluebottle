from requests import Request, Response
import mock
from urllib.parse import urlparse
from io import BytesIO
from datetime import datetime, timedelta

from django.db import connection
from django.test import Client as TestClient
from django.test.client import RequestFactory
from django.utils.timezone import get_current_timezone

from bluebottle.activity_pub.effects import get_platform_actor
from bluebottle.activity_pub.models import Announce, Follow, Accept, Event
from bluebottle.activity_pub.adapters import adapter

from bluebottle.cms.models import SitePlatformSettings
from bluebottle.clients.utils import LocalTenant
from bluebottle.clients.models import Client
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.geo.models import Geolocation

from bluebottle.funding.tests.factories import BudgetLineFactory, FundingFactory
from bluebottle.funding_stripe.tests.factories import ExternalAccountFactory, StripePayoutAccountFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.projects import ThemeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import JSONAPITestClient, BluebottleTestCase
from bluebottle.files.tests.factories import ImageFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.factory_models.geo import CountryFactory, GeolocationFactory


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
        raise Exception(f'Failed request: {method.upper()}: {url}, {response.json()} status={response.status_code}')


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


class ActivityPubTestCase:
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
        self.user = BlueBottleUserFactory.create()

        adapter_mock.start()
        webfinger_mock.start()

    def tearDown(self):
        super().tearDown()
        adapter_mock.stop()
        webfinger_mock.stop()

    def build_absolute_url(self, path):
        return connection.tenant.build_absolute_url(path)

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

    def create(self, **kwargs):
        self.model = self.factory.create(
            owner=self.user,
            initiative=None,
            image=ImageFactory.create(),
            **kwargs
        )

    def submit(self):
        self.model.states.submit()
        self.model.states.approve(save=True)

    def test_publish(self):
        self.test_accept()

        self.create()

        with LocalTenant(self.other_tenant):
            self.event = Event.objects.get()

            self.assertEqual(self.event.name, self.model.title)

    def test_publish_to_closed_platform(self):
        with LocalTenant(self.other_tenant):
            MemberPlatformSettings.objects.create(closed=True)

        self.test_accept()
        self.create()

        with LocalTenant(self.other_tenant):
            event = Event.objects.get()

            self.assertTrue(event.name, self.model.title)

    def test_publish_no_accept(self):
        self.test_follow()
        self.create()

        with LocalTenant(self.other_tenant):
            self.assertEqual(Event.objects.count(), 0)

    def test_adopt(self):
        self.test_publish()

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as image_file:
            mock_response = Response()
            mock_response.raw = BytesIO(image_file.read())
            mock_response.status_code = 200

        with LocalTenant(self.other_tenant):
            self.event = Event.objects.get()

            request = RequestFactory().get('/')
            request.user = BlueBottleUserFactory.create()

            with mock.patch('requests.get', return_value=mock_response):
                with mock.patch.object(Geolocation, 'update_location'):
                    self.adopted = adapter.adopt(self.event, request)
                    self.assertEqual(self.adopted.title, self.model.title)
                    self.assertEqual(self.adopted.origin, self.event)
                    self.assertEqual(self.adopted.image.origin, self.event.image)

    def test_adopt_default_owner(self):
        self.test_publish()

        with LocalTenant(self.other_tenant):
            follow = Follow.objects.get()
            follow.default_owner = BlueBottleUserFactory()
            follow.save()

        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as image_file:
            mock_response = Response()
            mock_response.raw = BytesIO(image_file.read())
            mock_response.status_code = 200

        with LocalTenant(self.other_tenant):
            follow = Follow.objects.get()
            self.event = Event.objects.get()

            request = RequestFactory().get('/')
            request.user = BlueBottleUserFactory.create()

            with mock.patch('requests.get', return_value=mock_response):
                with mock.patch.object(Geolocation, 'update_location'):
                    self.adopted = adapter.adopt(self.event, request)
                    self.assertEqual(self.adopted.owner, follow.default_owner)


class AdoptDeedTestCase(ActivityPubTestCase, BluebottleTestCase):
    factory = DeedFactory

    def create(self):
        super().create(
            start=(datetime.now() + timedelta(days=10)).date(),
            end=(datetime.now() + timedelta(days=20)).date()
        )
        self.submit()

    def test_publish(self):
        super().test_publish()

        self.assertEqual(self.event.start_time.date(), self.model.start)
        self.assertEqual(self.event.end_time.date(), self.model.end)

    def test_adopt(self):
        super().test_adopt()

        self.assertEqual(self.adopted.start, self.model.start)
        self.assertEqual(self.adopted.end, self.model.end)

        with LocalTenant(self.other_tenant):
            self.adopted.theme = ThemeFactory.create()
            self.adopted.states.submit()
            self.adopted.states.approve(save=True)

        announce = Announce.objects.get()
        self.assertEqual(announce.object, self.model.event)


class FundingTestCase(ActivityPubTestCase, BluebottleTestCase):
    factory = FundingFactory

    def create(self):
        super().create(
            impact_location=GeolocationFactory.create(),
            deadline=(datetime.now(get_current_timezone()) + timedelta(days=10)),
            bank_account=ExternalAccountFactory.create(
                account_id="some-external-account-id",
                status="verified",
                connect_account=StripePayoutAccountFactory.create(
                    account_id="test-account-id",
                    status="verified",
                ),
            )
        )
        with LocalTenant(self.other_tenant):
            CountryFactory.create(
                alpha2_code=self.model.impact_location.country.alpha2_code
            )

        BudgetLineFactory.create_batch(2, activity=self.model)

        self.submit()

    def test_publish(self):
        super().test_publish()

        with LocalTenant(self.other_tenant):
            self.assertEqual(self.event.target, self.model.target.amount)
            self.assertEqual(self.event.target_currency, str(self.model.target.currency))
            self.assertEqual(self.event.end_time, self.model.deadline)
            self.assertEqual(self.event.location.latitude, self.model.impact_location.position.x)
            self.assertEqual(self.event.location.longitude, self.model.impact_location.position.y)
            self.assertEqual(self.event.location.name, self.model.impact_location.formatted_address)
            self.assertEqual(
                self.event.location.address.address_country, self.model.impact_location.country.code
            )
            self.assertEqual(
                self.event.location.address.address_locality, self.model.impact_location.locality
            )

    def test_adopt(self):
        super().test_adopt()

        self.assertEqual(self.adopted.target, self.model.target)
        self.assertEqual(self.adopted.impact_location.position, self.model.impact_location.position)
        self.assertEqual(
            self.adopted.impact_location.country.alpha2_code,
            self.model.impact_location.country.alpha2_code
        )
