from datetime import datetime, timedelta
from io import BytesIO
from urllib.parse import urlparse

import mock
from django.core.files import File
from django.db import connection
from django.test import Client as TestClient
from django.test.client import RequestFactory
from django.utils.timezone import get_current_timezone
from djmoney.money import Money
from pytz import UTC
from requests import Request, Response

from bluebottle.activity_links.models import LinkedActivity, LinkedFunding
from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.effects import get_platform_actor
from bluebottle.activity_pub.models import (
    AdoptionModeChoices, AdoptionTypeChoices, Announce, Follow, Accept, Event,
    Recipient
)
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.collect.tests.factories import CollectActivityFactory, CollectTypeFactory
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.files.tests.factories import ImageFactory
from bluebottle.funding.tests.factories import BudgetLineFactory, FundingFactory
from bluebottle.funding_stripe.tests.factories import ExternalAccountFactory, StripePayoutAccountFactory
from bluebottle.geo.models import Geolocation
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory, GeolocationFactory
from bluebottle.test.factory_models.projects import ThemeFactory
from bluebottle.test.utils import JSONAPITestClient, BluebottleTestCase
from bluebottle.time_based.models import RegisteredDateActivity
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DeadlineActivityFactory,
    RegisteredDateActivityFactory, RegisteredDateParticipantFactory,
)


class ActivityPubClient(TestClient):
    def _base_environ(self, **request):
        env = super()._base_environ(**request)

        env['SERVER_NAME'] = connection.tenant.domain_url
        env['HTTP_HOST'] = connection.tenant.domain_url
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

    if response.status_code in (200, 201, 204):
        return (
            BytesIO(response.content) if response.content else None, response.accepted_media_type
        )
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
        site_settings = SitePlatformSettings.load()
        with open('./bluebottle/utils/tests/test_images/upload.png', 'rb') as image:
            site_settings.favicon = File(BytesIO(image.read()), name='favion.png')
            site_settings.share_activities = ['supplier', 'consumer']
            site_settings.save()

        self.country = CountryFactory.create()

        with LocalTenant(self.other_tenant):
            CountryFactory.create(
                alpha2_code=self.country.alpha2_code
            )
            CountryFactory.create()

            site_settings = SitePlatformSettings.load()
            with open('./bluebottle/utils/tests/test_images/upload.png', 'rb') as image:
                site_settings.favicon = File(BytesIO(image.read()), name='favion.png')
            site_settings.share_activities = ['supplier', 'consumer']
            site_settings.save()

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

    def test_platform_organization(self):
        site_settings = SitePlatformSettings.load()
        self.assertEqual(site_settings.share_activities, ['supplier', 'consumer'])
        self.assertTrue(bool(site_settings.organization))
        self.assertTrue(bool(site_settings.organization.activity_pub_organization))

    def test_follow(self):
        platform_url = self.build_absolute_url('/')

        with LocalTenant(self.other_tenant):
            with mock.patch('requests.get', return_value=self.mock_response):
                adapter.follow(platform_url)

        self.follow = Follow.objects.get(object=get_platform_actor())

        self.assertTrue(self.follow)
        self.assertTrue(self.follow.actor.organization)
        self.assertTrue(self.follow.actor.organization.logo)

    def test_accept(self):
        self.test_follow()

        Accept.objects.create(
            object=self.follow
        )

        with LocalTenant(self.other_tenant):
            accept = Accept.objects.get(object=Follow.objects.get())
            self.assertTrue(accept)
            self.assertTrue(accept.actor.organization)
            self.assertTrue(accept.actor.organization.logo)

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
        adapter.create_event(self.model)

    def test_publish(self):
        self.test_accept()
        self.create()
        publish = self.model.event.publish_set.first()
        Recipient.objects.create(actor=self.follow.actor, activity=publish)

        with LocalTenant(self.other_tenant):
            self.event = Event.objects.get()
            self.assertEqual(self.event.name, self.model.title)

    def test_automatic_publish_on_approve(self):
        self.test_accept()

        self.follow.publish_mode = 'automatic'
        self.follow.save(update_fields=['publish_mode'])

        with LocalTenant(self.other_tenant):
            Event.objects.all().delete()

        activity = DeedFactory.create(status='submitted')
        activity.states.approve(save=True)

        publish = activity.event.publish_set.first()
        self.assertIsNotNone(publish)
        self.assertTrue(
            Recipient.objects.filter(activity=publish, actor=self.follow.actor).exists()
        )

        with LocalTenant(self.other_tenant):
            event = Event.objects.get()
            self.assertEqual(event.name, activity.title)

    def test_manual_follow_not_auto_published(self):
        self.test_accept()

        with LocalTenant(self.other_tenant):
            Event.objects.all().delete()

        activity = DeedFactory.create(status='submitted')
        activity.states.approve(save=True)

        event = getattr(activity, 'event', None)
        self.assertIsNone(event)

        with LocalTenant(self.other_tenant):
            self.assertEqual(Event.objects.count(), 0)

    def test_manual_publish_after_approve(self):
        self.test_accept()

        with LocalTenant(self.other_tenant):
            Event.objects.all().delete()

        activity = DeedFactory.create(status='submitted')
        activity.states.approve(save=True)

        adapter.create_event(activity)
        publish = activity.event.publish_set.first()
        Recipient.objects.create(actor=self.follow.actor, activity=publish)

        with LocalTenant(self.other_tenant):
            event = Event.objects.get()
            self.assertEqual(event.name, activity.title)

    def test_publish_to_closed_platform(self):
        with LocalTenant(self.other_tenant):
            MemberPlatformSettings.objects.create(closed=True)

        self.test_accept()
        self.create()

        publish = self.model.event.publish_set.first()
        Recipient.objects.create(actor=self.follow.actor, activity=publish)

        with LocalTenant(self.other_tenant):
            event = Event.objects.get()
            self.assertTrue(event.name, self.model.title)

    def test_publish_no_accept(self):
        self.test_follow()
        self.create()

        with LocalTenant(self.other_tenant):
            self.assertEqual(Event.objects.count(), 0)

    def approve(self, activity):
        activity.theme = ThemeFactory.create()
        activity.states.approve(save=True)

    @property
    def mock_response(self):
        with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as image_file:
            mock_response = Response()
            mock_response.raw = BytesIO(image_file.read())
            mock_response.status_code = 200

        return mock_response

    def test_adopt(self):
        self.test_publish()

        with LocalTenant(self.other_tenant):
            self.event = Event.objects.get()

            request = RequestFactory().get('/')
            request.user = BlueBottleUserFactory.create()

            with mock.patch('requests.get', return_value=self.mock_response):
                with mock.patch.object(Geolocation, 'update_location'):
                    self.adopted = adapter.adopt(self.event, request)
                    self.assertEqual(self.adopted.title, self.model.title)
                    self.assertEqual(self.adopted.origin, self.event)
                    self.assertEqual(self.adopted.image.origin, self.event.image)

                    self.approve(self.adopted)
                    announce = Announce.objects.last()
                    self.assertTrue(announce)

        announce = Announce.objects.first()
        self.assertTrue(announce)

    def test_adopt_default_owner(self):
        self.test_publish()

        with LocalTenant(self.other_tenant):
            follow = Follow.objects.get()
            follow.default_owner = BlueBottleUserFactory()
            follow.save()

        with LocalTenant(self.other_tenant):
            follow = Follow.objects.get()
            self.event = Event.objects.get()

            request = RequestFactory().get('/')
            request.user = BlueBottleUserFactory.create()

            with mock.patch('requests.get', return_value=self.mock_response):
                with mock.patch.object(Geolocation, 'update_location'):
                    self.adopted = adapter.adopt(self.event, request)
                    self.assertEqual(self.adopted.owner, follow.default_owner)


class LinkTestCase(ActivityPubTestCase):
    def test_follow(self):
        super().test_follow()
        with LocalTenant(self.other_tenant):
            follow = Follow.objects.get()
            follow.adoption_mode = AdoptionModeChoices.automatic
            follow.adoption_type = AdoptionTypeChoices.link
            follow.save()

    def test_link(self):
        self.test_publish()

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertEqual(link.title, self.model.title)

            announce = Announce.objects.get()
            self.assertEqual(announce.object, link.event)

    def test_update(self):
        title = 'Some new title'
        self.test_link()
        self.model.title = title
        self.model.save()

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertEqual(link.title, title)

    def test_cancel(self):
        self.test_link()
        self.model.states.cancel(save=True)

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertEqual(link.status, 'cancelled')

    def test_finish(self):
        self.test_link()
        self.model.states.succeed(save=True)

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertEqual(link.status, 'succeeded')

    def test_delete(self):
        self.test_link()
        self.model.delete()

        with LocalTenant(self.other_tenant):
            with self.assertRaises(LinkedActivity.DoesNotExist):
                LinkedActivity.objects.get()


class AdoptDeedTestCase(ActivityPubTestCase, BluebottleTestCase):
    factory = DeedFactory

    def create(self):
        super().create(
            start=(datetime.now() + timedelta(days=10)).date(),
            end=(datetime.now() + timedelta(days=20)).date(),
            organization=None
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


class LinkDeedTestCase(LinkTestCase, BluebottleTestCase):
    factory = DeedFactory

    def create(self):
        super().create(
            start=(datetime.now() + timedelta(days=10)).date(),
            end=(datetime.now() + timedelta(days=20)).date(),
            organization=None
        )
        self.submit()


class LinkFundingTestCase(LinkTestCase, BluebottleTestCase):
    factory = FundingFactory

    def create(self):
        super().create(
            impact_location=GeolocationFactory.create(country=self.country),
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

        BudgetLineFactory.create_batch(2, activity=self.model)
        self.submit()

    def approve(self, activity):
        BudgetLineFactory.create_batch(2, activity=activity)

        activity.bank_account = ExternalAccountFactory.create(
            account_id="some-external-account-id",
            status="verified",
            connect_account=StripePayoutAccountFactory.create(
                account_id="test-account-id",
                status="verified",
            )
        )
        activity.theme = ThemeFactory.create()
        activity.states.submit()
        activity.states.approve(save=True)

    def test_update_donated_amount(self):
        self.test_link()

        self.model.amount_donated = Money(12, 'EUR')
        self.model.save()

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertEqual(link.donated, Money(12, 'EUR'))

    def test_deadline_maps_to_end(self):
        self.test_link()

        with LocalTenant(self.other_tenant):
            link = LinkedFunding.objects.get()
            self.assertEqual(link.end, self.model.deadline)

    def test_image_maps_to_linked_funding_image(self):
        self.test_link()

        with LocalTenant(self.other_tenant):
            link = LinkedFunding.objects.get()
            self.assertIsNotNone(self.model.image, "Original Funding should have an image")
            self.assertIsNotNone(link.image, "LinkedFunding should have an image mapped from Funding")

    def test_impact_location_maps_to_linked_funding_location(self):
        self.test_link()

        with LocalTenant(self.other_tenant):
            link = LinkedFunding.objects.get()
            self.assertIsNotNone(self.model.impact_location)
            self.assertIsNotNone(link.location)
            self.assertEqual(link.location.locality, self.model.impact_location.locality)
            self.assertEqual(link.location.country, self.model.impact_location.country)


class FundingTestCase(ActivityPubTestCase, BluebottleTestCase):
    factory = FundingFactory

    def create(self):
        super().create(
            impact_location=GeolocationFactory.create(country=self.country),
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

        BudgetLineFactory.create_batch(2, activity=self.model)

        self.submit()

    def approve(self, activity):
        BudgetLineFactory.create_batch(2, activity=activity)

        activity.bank_account = ExternalAccountFactory.create(
            account_id="some-external-account-id",
            status="verified",
            connect_account=StripePayoutAccountFactory.create(
                account_id="test-account-id",
                status="verified",
            )
        )
        activity.theme = ThemeFactory.create()
        activity.states.submit()
        activity.states.approve(save=True)

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


class LinkDeadlineActivityTestCase(LinkTestCase, BluebottleTestCase):
    factory = DeadlineActivityFactory

    def create(self):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            start=(datetime.now() + timedelta(days=10)).date(),
            deadline=(datetime.now() + timedelta(days=20)).date()
        )
        self.submit()


class AdoptDeadlineActivityTestCase(ActivityPubTestCase, BluebottleTestCase):
    factory = DeadlineActivityFactory

    def create(self):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            start=(datetime.now() + timedelta(days=10)).date(),
            deadline=(datetime.now() + timedelta(days=20)).date()
        )
        self.submit()

    def test_publish(self):
        super().test_publish()

        self.assertEqual(self.event.start_time.date(), self.model.start)
        self.assertEqual(self.event.end_time.date(), self.model.deadline)

    def test_adopt(self):
        super().test_adopt()

        self.assertEqual(self.adopted.start, self.model.start)
        self.assertEqual(self.adopted.deadline, self.model.deadline)
        self.assertEqual(self.adopted.duration, self.model.duration)
        if self.model.location:
            self.assertEqual(
                self.adopted.location.position,
                self.model.location.position
            )


class LinkRegisteredDateActivityTestCase(LinkTestCase, BluebottleTestCase):
    factory = RegisteredDateActivityFactory

    def create(self):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            start=datetime.now(tz=UTC) - timedelta(days=10),
            organization=None
        )
        RegisteredDateParticipantFactory.create(activity=self.model)
        self.submit()

    def test_finish(self):
        pass


class AdoptRegisteredDateActivityTestCase(ActivityPubTestCase, BluebottleTestCase):
    factory = RegisteredDateActivityFactory

    def create(self):
        activity = super().create(
            location=GeolocationFactory.create(country=self.country),
            start=datetime.now(tz=UTC) - timedelta(days=10),
            organization=None
        )
        RegisteredDateParticipantFactory.create(activity=self.model)
        self.submit()

    def test_publish(self):
        super().test_publish()

        with LocalTenant(self.other_tenant):
            self.assertEqual(self.event.start_time.date(), self.model.start.date())
            if self.model.end:
                self.assertEqual(self.event.end_time.date(), self.model.end.date())
            self.assertEqual(self.event.duration, self.model.duration)

    def test_adopt(self):
        super().test_adopt()

        self.assertIsInstance(self.adopted, RegisteredDateActivity)
        self.assertEqual(self.adopted.start.date(), self.model.start.date())
        self.assertEqual(self.adopted.duration, self.model.duration)
        if self.model.location:
            self.assertEqual(
                self.adopted.location.position,
                self.model.location.position
            )


class LinkedDateActivityTestCase(LinkTestCase, BluebottleTestCase):
    factory = DateActivityFactory

    def create(self):
        super().create(slots=[], organization=None)

        DateActivitySlotFactory.create_batch(
            3,
            activity=self.model,
            location=None,
            is_online=True
        )

        self.submit()


class AdoptDateActivityTestCase(ActivityPubTestCase, BluebottleTestCase):
    factory = DateActivityFactory

    def create(self):
        super().create(slots=[], organization=None)

        DateActivitySlotFactory.create_batch(
            3,
            activity=self.model,
            location=None,
            is_online=True
        )

        self.submit()

    def test_publish(self):
        super().test_publish()
        with LocalTenant(self.other_tenant):
            self.assertEqual(self.event.sub_event.count(), 3)

    def test_adopt(self):
        super().test_adopt()

        with LocalTenant(self.other_tenant):
            self.assertEqual(self.adopted.slots.count(), 3)


class LinkedSingleSlotDateActivityTestCase(LinkTestCase, BluebottleTestCase):
    factory = DateActivityFactory

    def create(self):
        super().create(slots=[])

        DateActivitySlotFactory.create_batch(
            1,
            activity=self.model,
            location=GeolocationFactory.create(country=self.country),
        )

        self.submit()


class AdoptSingleSlotDateActivityTestCase(ActivityPubTestCase, BluebottleTestCase):
    factory = DateActivityFactory

    def create(self):
        super().create(slots=[])

        DateActivitySlotFactory.create_batch(
            1,
            activity=self.model,
            location=GeolocationFactory.create(country=self.country),
        )

        self.submit()

    def test_publish(self):
        super().test_publish()
        with LocalTenant(self.other_tenant):
            self.assertEqual(self.event.sub_event.count(), 1)

    def test_adopt(self):
        super().test_adopt()

        with LocalTenant(self.other_tenant):
            self.assertEqual(self.adopted.slots.count(), 1)


class LinkCollectActivityTestCase(LinkTestCase, BluebottleTestCase):
    factory = CollectActivityFactory

    def create(self):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            location_hint='ring rtop bell',
            start=(datetime.now() + timedelta(days=10)).date(),
            end=(datetime.now() + timedelta(days=20)).date(),
            collect_type=CollectTypeFactory.create(),
            organization=None
        )
        self.submit()

    def test_update_collect_type(self):
        self.test_link()

        new_collect_type = CollectTypeFactory.create()
        self.model.collect_type = new_collect_type
        self.model.save()

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertIsNotNone(link)


class AdoptCollectActivityTestCase(ActivityPubTestCase, BluebottleTestCase):
    factory = CollectActivityFactory

    def create(self):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            start=(datetime.now() + timedelta(days=10)).date(),
            end=(datetime.now() + timedelta(days=20)).date(),
            collect_type=CollectTypeFactory.create(),
            organization=None
        )
        self.submit()

    def test_publish(self):
        super().test_publish()

        with LocalTenant(self.other_tenant):
            self.assertEqual(self.event.start_time.date(), self.model.start)
            self.assertEqual(self.event.end_time.date(), self.model.end)

    def test_adopt(self):
        super().test_adopt()

        self.assertEqual(self.adopted.start, self.model.start)
        self.assertEqual(self.adopted.end, self.model.end)
        self.assertEqual(self.adopted.collect_type, self.model.collect_type)
        if self.model.location:
            self.assertEqual(
                self.adopted.location.position,
                self.model.location.position
            )
