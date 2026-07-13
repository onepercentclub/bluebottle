from datetime import datetime, timedelta
from io import BytesIO
from urllib.parse import urlparse

import httmock
import mock
from django.core.files import File
from django.db import connection
from django.test import Client as TestClient
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.utils.timezone import get_current_timezone
from djmoney.money import Money
from pytz import UTC
from requests import Request, Response

from bluebottle.activity_links.models import LinkedActivity, LinkedFunding, LinkedGrantApplication
from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.effects import get_platform_actor
from bluebottle.activity_pub.models import (
    AdoptionTypeChoices, Follow, Accept, Event,
    Recipient, RepetitionModeChoices
)
from bluebottle.activity_pub.tasks import publish_to_recipient
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.collect.tests.factories import CollectActivityFactory, CollectTypeFactory, CollectContributorFactory
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.files.tests.factories import ImageFactory
from bluebottle.funding.tests.factories import BudgetLineFactory, FundingFactory
from bluebottle.funding_stripe.tests.base import FundingStripeMixin
from bluebottle.funding_stripe.tests.factories import ExternalAccountFactory, StripePayoutAccountFactory
from bluebottle.geo.models import Geolocation
from bluebottle.grant_management.tests.factories import GrantApplicationFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.tests.factories import SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory, GeolocationFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.factory_models.projects import ThemeFactory
from bluebottle.test.utils import JSONAPITestClient, BluebottleTestCase
from bluebottle.time_based.models import PeriodicParticipant, RegisteredDateActivity
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
    DateRegistrationFactory,
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
    DeadlineRegistrationFactory,
    PeriodicRegistrationFactory,
    RegisteredDateActivityFactory,
    RegisteredDateParticipantFactory,
    PeriodicActivityFactory,
    ScheduleActivityFactory,
    ScheduleParticipantFactory,
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


client_mock = mock.patch(
    "bluebottle.activity_pub.clients.JSONLDClient.execute", wraps=execute
)

webfinger_mock = mock.patch(
    "bluebottle.webfinger.client.WebFingerClient._do_request", wraps=do_request
)


def mock_image_response():
    with open('./bluebottle/cms/tests/test_images/upload.png', 'rb') as image_file:
        mock_response = Response()
        mock_response.raw = BytesIO(image_file.read())
        mock_response.status_code = 200

    return mock_response


@httmock.urlmatch(path=r'/(media|api/activities/.*/image)/.*')
def image_mock(url, request):
    return mock_image_response()


class ActivityPubTestCase:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.delay_on_commit = publish_to_recipient.delay_on_commit
        publish_to_recipient.delay_on_commit = publish_to_recipient.delay

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        publish_to_recipient.delay_on_commit = cls.delay_on_commit

    def setUp(self):
        super().setUp()

        self.other_tenant = Client.objects.get(schema_name='test2')
        site_settings = SitePlatformSettings.load()
        with open('./bluebottle/utils/tests/test_images/upload.png', 'rb') as image:
            site_settings.logo = File(BytesIO(image.read()), name='favion.png')
            site_settings.share_activities = ['supplier', 'consumer']
            site_settings.save()

        self.country = CountryFactory.create()

        publish_to_recipient.delay_on_commit = publish_to_recipient.delay

        with LocalTenant(self.other_tenant):
            CountryFactory.create(
                alpha2_code=self.country.alpha2_code
            )
            CountryFactory.create()

            site_settings = SitePlatformSettings.load()
            with open('./bluebottle/utils/tests/test_images/upload.png', 'rb') as image:
                site_settings.logo = File(BytesIO(image.read()), name='favion.png')
            site_settings.share_activities = ['supplier', 'consumer']
            site_settings.save()

        self.client = ActivityPubClient()
        self.json_api_client = JSONAPITestClient()
        self.user = BlueBottleUserFactory.create()

        client_mock.start()
        webfinger_mock.start()

    def tearDown(self):
        super().tearDown()
        client_mock.stop()
        webfinger_mock.stop()

    def build_absolute_url(self, path):
        return connection.tenant.build_absolute_url(path)

    def test_platform_organization(self):
        site_settings = SitePlatformSettings.load()
        self.assertEqual(site_settings.share_activities, ['supplier', 'consumer'])
        self.assertTrue(bool(site_settings.organization))
        self.assertTrue(bool(site_settings.organization.activity_pub_model))

    def test_accept(self):
        self.test_follow()

        Accept.objects.create(
            object=self.follow
        )

        with LocalTenant(self.other_tenant):
            accept = Accept.objects.get(object=Follow.objects.get())
            self.assertTrue(accept)
            self.assertTrue(accept.actor.adopted)

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
        adapter.sync(self.model)

    def test_publish(self):
        self.test_accept()
        self.create()
        publish = self.model.activity_pub_model.create_set.get()

        with httmock.HTTMock(image_mock):
            Recipient.objects.create(actor=self.follow.actor, activity=publish)

        with LocalTenant(self.other_tenant):
            self.event = Event.objects.get()
            self.assertEqual(self.event.name, self.model.title)

    def test_automatic_publish_on_approve(self):
        self.test_accept()

        self.follow.publish_mode = 'automatic'
        self.follow.save()

        with LocalTenant(self.other_tenant):
            Event.objects.all().delete()

        activity = self.factory.create(status='submitted')
        activity.states.approve(save=True)

        publish = activity.activity_pub_model.create_set.first()
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

        adapter.sync(activity)
        publish = activity.activity_pub_model.create_set.get()
        Recipient.objects.create(actor=self.follow.actor, activity=publish)

        with LocalTenant(self.other_tenant):
            event = Event.objects.get()
            self.assertEqual(event.name, activity.title)

    def test_publish_to_closed_platform(self):
        with LocalTenant(self.other_tenant):
            MemberPlatformSettings.objects.create(closed=True)

        self.test_accept()
        self.create()

        publish = self.model.activity_pub_model.create_set.first()

        with httmock.HTTMock(image_mock):
            Recipient.objects.create(actor=self.follow.actor, activity=publish)

        with LocalTenant(self.other_tenant):
            event = Event.objects.get()
            self.assertTrue(event.name, self.model.title)

    def test_publish_no_accept(self):
        self.test_follow()
        self.create()

        with LocalTenant(self.other_tenant):
            self.assertEqual(Event.objects.count(), 0)

    def test_publish_closed_segment(self):
        self.test_follow()
        self.create()
        segment = SegmentFactory.create(closed=True)
        self.model.segments.add(segment)

        with LocalTenant(self.other_tenant):
            self.assertEqual(Event.objects.count(), 0)

    def approve(self, activity):
        activity.states.approve(save=True)

    def complete(self):
        self.adopted.theme = ThemeFactory.create()


class TemplateTestCase(ActivityPubTestCase):
    def test_follow(self):
        platform_url = self.build_absolute_url('/')

        with LocalTenant(self.other_tenant):
            with httmock.HTTMock(image_mock):

                follow = Follow(
                    adoption_type=AdoptionTypeChoices.clone
                )
                follow.follow(platform_url)
                follow.save()

        self.follow = Follow.objects.get(object=get_platform_actor())

        self.assertTrue(self.follow)
        self.assertTrue(self.follow.actor.adopted)

    def test_adopt(self):
        self.test_publish()

        with LocalTenant(self.other_tenant):
            self.event = Event.objects.get()

            request = RequestFactory().get('/')
            request.user = BlueBottleUserFactory.create()

            with httmock.HTTMock(image_mock):
                with mock.patch.object(Geolocation, 'update_location'):
                    self.adopted = adapter.adopt(self.event, owner=request.user)
                    self.assertEqual(self.adopted.title, self.model.title)
                    self.assertEqual(self.adopted.origin, self.event)
                    self.assertEqual(self.adopted.image.origin, self.event.image)

                    self.complete()
                    self.adopted.states.submit(save=True)

                    self.approve(self.adopted)
                    accept = Accept.objects.last()
                    self.assertTrue(accept)

        accept = Accept.objects.first()
        self.assertTrue(accept)

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

            with httmock.HTTMock(image_mock):
                with mock.patch.object(Geolocation, 'update_location'):
                    self.adopted = adapter.adopt(self.event, owner=request.user)
                    self.assertEqual(self.adopted.owner, follow.default_owner)


class SyncTestCase(ActivityPubTestCase):
    def test_follow(self):
        platform_url = self.build_absolute_url('/')
        with LocalTenant(self.other_tenant):
            with httmock.HTTMock(image_mock):

                follow = Follow(
                    adoption_type=AdoptionTypeChoices.sync
                )
                follow.follow(platform_url)
                follow.save()

        self.follow = Follow.objects.get(object=get_platform_actor())

        self.assertTrue(self.follow)
        self.assertTrue(self.follow.actor.adopted)

    def test_adopt(self):
        self.test_publish()

        with LocalTenant(self.other_tenant):
            self.event = Event.objects.get()

            request = RequestFactory().get('/')
            request.user = BlueBottleUserFactory.create()

            with httmock.HTTMock(image_mock):
                with mock.patch.object(Geolocation, 'update_location'):
                    self.adopted = adapter.adopt(self.event, owner=request.user)
                    self.assertEqual(self.adopted.title, self.model.title)
                    self.assertEqual(self.adopted.origin, self.event)
                    self.assertEqual(self.adopted.image.origin, self.event.image)

                    self.complete()
                    self.adopted.states.submit(save=True)

                    self.approve(self.adopted)
                    accept = Accept.objects.last()
                    self.assertTrue(accept)

        accept = Accept.objects.first()
        self.assertTrue(accept)

    def join(self):
        self.participant = self.participant_factory.create(activity=self.adopted)

    def test_join(self):
        self.test_adopt()

        with LocalTenant(self.other_tenant):
            self.join()
            self.email = self.participant.user.email
            self.adopted.origin.refresh_from_db()
            self.assertEqual(self.adopted.origin.contributor_count, 1)

        self.synced_participant = self.participant_factory._meta.model.objects.get()

        self.assertEqual(
            self.email, self.synced_participant.remote_user.email
        )

        self.assertEqual(
            self.synced_participant.status, self.expected_participant_status
        )

    def test_leave(self):
        self.test_join()

        with LocalTenant(self.other_tenant):
            self.participant.states.withdraw(save=True)
            self.adopted.origin.refresh_from_db()
            self.assertEqual(self.adopted.origin.contributor_count, 0)

        self.synced_participant.refresh_from_db()
        self.assertEqual(
            self.synced_participant.status, 'withdrawn'
        )

    def test_rejoin(self):
        self.test_leave()

        with LocalTenant(self.other_tenant):
            self.participant.states.reapply(save=True)

            self.adopted.origin.refresh_from_db()
            self.assertEqual(self.adopted.origin.contributor_count, 1)

        self.synced_participant.refresh_from_db()
        self.assertEqual(
            self.synced_participant.status, self.expected_participant_status
        )

    def test_update(self):
        self.test_adopt()

        with httmock.HTTMock(image_mock):
            self.model.title = 'Some new title'
            self.model.save()

        with LocalTenant(self.other_tenant):
            self.event.refresh_from_db()
            self.assertEqual(self.event.name, 'Some new title')
            self.adopted.refresh_from_db()
            self.assertEqual(self.adopted.title, 'Some new title')

    def test_update_image(self):
        self.test_adopt()

        with httmock.HTTMock(image_mock):
            self.model.image = ImageFactory.create()
            self.model.save()

        image_iri = self.model.image.activity_pub_model.pub_url

        with LocalTenant(self.other_tenant):
            self.event.refresh_from_db()
            self.assertEqual(self.event.image.iri, image_iri)
            self.adopted.refresh_from_db()
            self.assertEqual(
                self.adopted.image.origin.iri,
                image_iri
            )

    def test_succeed(self):
        self.test_adopt()

        with httmock.HTTMock(image_mock):
            self.model.states.succeed(save=True)

        with LocalTenant(self.other_tenant):
            self.adopted.refresh_from_db()
            self.assertEqual(self.model.status, 'succeeded')

    def test_cancel(self):
        self.test_adopt()

        with httmock.HTTMock(image_mock):
            self.model.states.cancel(save=True)

        with LocalTenant(self.other_tenant):
            self.adopted.refresh_from_db()
            self.assertEqual(self.model.status, 'cancelled')


class LinkTestCase(ActivityPubTestCase):
    expected_link_status = 'open'

    def test_follow(self):
        platform_url = self.build_absolute_url('/')

        with LocalTenant(self.other_tenant):
            with httmock.HTTMock(image_mock):
                follow = Follow(
                    automatic_adoption_activity_types=[
                        self.factory._meta.model._meta.model_name
                    ],
                    adoption_type=AdoptionTypeChoices.link
                )
                follow.follow(platform_url)
                follow.save()

        self.follow = Follow.objects.get(object=get_platform_actor())

        self.assertTrue(self.follow)
        self.assertTrue(self.follow.actor.organization)
        self.assertTrue(self.follow.actor.organization.icon)
        self.assertEqual(self.follow.adoption_type, AdoptionTypeChoices.link)

    def test_update_follow(self):
        self.test_follow()

        with LocalTenant(self.other_tenant):
            follow = Follow.objects.get()
            follow.adoption_type = AdoptionTypeChoices.clone
            follow.save()

        follow = Follow.objects.get(object=get_platform_actor())
        self.assertEqual(follow.adoption_type, AdoptionTypeChoices.clone)

    def test_link(self):
        with httmock.HTTMock(image_mock):
            self.test_publish()

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertEqual(link.status, self.expected_link_status)
            self.assertEqual(link.title, self.model.title)
            self.assertTrue(link.image)
            accept = Accept.objects.get(object=link.origin)
            self.assertEqual(accept.actor, Follow.objects.get().actor)

    def test_link_notifies_source_platform(self):
        self.test_link()

        accept = Accept.objects.get(object=self.model.activity_pub_model)
        self.assertEqual(accept.actor, self.follow.actor)

    def test_update(self):
        title = 'Some new title'
        self.test_link()
        self.model.title = title

        with httmock.HTTMock(image_mock):
            self.model.save()

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertEqual(link.title, title)

    def test_cancel(self):
        self.test_link()

        with httmock.HTTMock(image_mock):
            self.model.states.cancel(save=True)

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertEqual(link.status, 'cancelled')

    def test_finish(self):
        self.test_link()
        with httmock.HTTMock(image_mock):
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


class TemplateDeedTestCase(TemplateTestCase, BluebottleTestCase):
    factory = DeedFactory

    def create(self, **kwargs):
        super().create(
            start=(datetime.now() + timedelta(days=10)).date(),
            end=(datetime.now() + timedelta(days=20)).date(),
            organization=None,
            **kwargs
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


class SyncDeedTestCase(SyncTestCase, BluebottleTestCase):
    factory = DeedFactory
    participant_factory = DeedParticipantFactory
    expected_participant_status = 'accepted'

    def create(self, **kwargs):
        super().create(
            start=(datetime.now() + timedelta(days=10)).date(),
            end=(datetime.now() + timedelta(days=20)).date(),
            organization=None,
            **kwargs
        )
        if 'status' not in kwargs:
            self.submit()


class SyncDeadlineActivityTestCase(SyncTestCase, BluebottleTestCase):
    factory = DeadlineActivityFactory
    participant_factory = DeadlineParticipantFactory
    expected_participant_status = 'new'

    motivation = 'Some motivation'

    def create(self, **kwargs):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            start=(datetime.now() + timedelta(days=10)).date(),
            deadline=(datetime.now() + timedelta(days=20)).date(),
            **kwargs
        )
        self.submit()

    def join(self):
        registration = DeadlineRegistrationFactory.create(
            activity=self.adopted,
            answer=self.motivation,
        )
        self.participant = registration.participants.get()

    def test_join(self):
        super().test_join()

        self.assertEqual(self.synced_participant.registration.answer, self.motivation)

    def test_accept_participant(self):
        self.test_join()
        self.synced_participant.registration.states.accept(save=True)

        with LocalTenant(self.other_tenant):
            self.participant.refresh_from_db()
            self.assertStatus(self.participant, 'succeeded')

    def test_reject_participant(self):
        self.test_join()
        self.synced_participant.registration.states.reject(save=True)

        with LocalTenant(self.other_tenant):
            self.participant.refresh_from_db()
            self.assertStatus(self.participant, 'rejected')


class SyncScheduleActivityTestCase(SyncTestCase, BluebottleTestCase):
    factory = ScheduleActivityFactory
    participant_factory = ScheduleParticipantFactory
    expected_participant_status = 'new'

    def create(self, **kwargs):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            organization=None
        )
        self.submit()

    def test_schedule(self):
        self.test_join()

        self.synced_participant.slot.start = (datetime.now(get_current_timezone()) + timedelta(days=10))
        self.synced_participant.slot.duration = timedelta(hours=10)
        self.synced_participant.slot.location = GeolocationFactory.create(country=self.country)
        self.synced_participant.slot.save()

        with LocalTenant(self.other_tenant):
            self.participant.refresh_from_db()
            self.assertEqual(
                self.participant.status, 'scheduled'
            )
            self.assertEqual(
                self.synced_participant.slot.start, self.participant.slot.start
            )

    def test_reschedule(self):
        self.test_schedule()

        self.synced_participant.slot.start = (datetime.now(get_current_timezone()) + timedelta(days=20))
        self.synced_participant.slot.duration = timedelta(hours=10)
        self.synced_participant.slot.location = GeolocationFactory.create(country=self.country)
        self.synced_participant.slot.save()

        with LocalTenant(self.other_tenant):
            self.participant.refresh_from_db()
            self.assertEqual(
                self.participant.status, 'scheduled'
            )
            self.assertEqual(
                self.synced_participant.slot.start, self.participant.slot.start
            )


class SyncPeriodicActivityTestCase(SyncTestCase, BluebottleTestCase):
    factory = PeriodicActivityFactory
    participant_factory = PeriodicRegistrationFactory
    expected_participant_status = 'new'

    def create(self, **kwargs):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            organization=None
        )
        self.submit()

    def join(self):
        super().join()
        self.participant = self.participant.participants.first()

    def test_join(self):
        super().test_join()
        self.synced_participant.states.accept(save=True)
        slot_url = self.model.slots.first().activity_pub_model.pub_url

        self.assertEqual(
            self.synced_participant.participants.get().slot, self.model.slots.first()
        )

        with LocalTenant(self.other_tenant):
            self.participant.refresh_from_db()
            self.assertEqual(
                self.participant.slot.origin.pub_url,
                slot_url
            )

    def test_next_slot(self):
        self.test_join()

        self.model.slots.first().states.finish(save=True)

        self.assertEqual(
            PeriodicParticipant.objects.count(), 2
        )

        with LocalTenant(self.other_tenant):
            self.assertEqual(
                PeriodicParticipant.objects.count(), 2
            )


class SyncCollectActivityTestCase(SyncTestCase, BluebottleTestCase):
    factory = CollectActivityFactory
    participant_factory = CollectContributorFactory
    expected_participant_status = 'accepted'

    def create(self, **kwargs):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            location_hint='ring rtop bell',
            start=(datetime.now() + timedelta(days=10)).date(),
            end=(datetime.now() + timedelta(days=20)).date(),
            collect_type=CollectTypeFactory.create(),
            organization=None
        )
        self.submit()


class LinkDeedTestCase(LinkTestCase, BluebottleTestCase):
    factory = DeedFactory

    def create(self, **kwargs):
        super().create(
            start=(datetime.now() + timedelta(days=10)).date(),
            end=(datetime.now() + timedelta(days=20)).date(),
            organization=None,
            **kwargs
        )
        if 'status' not in kwargs:
            self.submit()

    def test_link_succeeded(self):
        self.test_accept()
        self.follow.publish_mode = 'automatic'
        self.follow.save(update_fields=['publish_mode'])

        with httmock.HTTMock(image_mock):
            self.create(status='succeeded')
            adapter.sync(self.model)

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertEqual(link.status, 'succeeded')

    def test_link_cancelled(self):
        self.test_accept()
        self.follow.publish_mode = 'automatic'
        self.follow.save(update_fields=['publish_mode'])

        with httmock.HTTMock(image_mock):
            self.create(status='cancelled')
            adapter.sync(self.model)

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertEqual(link.status, 'cancelled')

    def test_link_manual_succeeded(self):
        self.test_accept()

        with httmock.HTTMock(image_mock):
            self.create(status='succeeded')

            adapter.sync(self.model)
            publish = self.model.activity_pub_model.create_set.first()
            Recipient.objects.create(actor=self.follow.actor, activity=publish)

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertEqual(link.status, 'succeeded')


@override_settings(
    MAPBOX_API_KEY=None
)
class LinkFundingTestCase(FundingStripeMixin, LinkTestCase, BluebottleTestCase):
    factory = FundingFactory

    def create(self, **kwargs):
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
            ),
            **kwargs
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

        with httmock.HTTMock(image_mock):
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
            self.assertEqual(
                link.location.country.alpha2_code,
                self.model.impact_location.country.alpha2_code
            )


class TemplateFundingTestCase(FundingStripeMixin, TemplateTestCase, BluebottleTestCase):
    factory = FundingFactory

    def create(self, **kwargs):
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
            ),
            **kwargs
        )

        BudgetLineFactory.create_batch(2, activity=self.model)

        self.submit()

    def complete(self):
        BudgetLineFactory.create_batch(2, activity=self.adopted)

        self.adopted.bank_account = ExternalAccountFactory.create(
            account_id="some-external-account-id",
            status="verified",
            connect_account=StripePayoutAccountFactory.create(
                account_id="test-account-id",
                status="verified",
            )
        )
        super().complete()

    def approve(self, activity):
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
                self.event.location.address.country, self.model.impact_location.country.code
            )
            self.assertEqual(
                self.event.location.address.locality, self.model.impact_location.locality
            )

    def test_adopt(self):
        super().test_adopt()

        self.assertEqual(self.adopted.target, self.model.target)
        self.assertEqual(self.adopted.impact_location.position, self.model.impact_location.position)
        self.assertEqual(
            self.adopted.impact_location.country.alpha2_code,
            self.model.impact_location.country.alpha2_code
        )


@override_settings(
    MAPBOX_API_KEY=None
)
class LinkGrantApplicationTestCase(LinkTestCase, BluebottleTestCase):
    factory = GrantApplicationFactory

    def create(self, **kwargs):
        super().create(
            impact_location=GeolocationFactory.create(country=self.country),
            started=datetime.now(get_current_timezone()),
            **kwargs
        )
        self.submit()

    def test_finish(self):
        self.test_link()

        with httmock.HTTMock(image_mock):
            self.model.states.succeed(save=True)

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertEqual(link.status, 'succeeded')

    def test_target_maps_to_linked_grant_application(self):
        self.test_link()

        with LocalTenant(self.other_tenant):
            link = LinkedGrantApplication.objects.get()
            self.assertEqual(link.target, self.model.target)

    def test_start_maps_to_linked_grant_application(self):
        self.test_link()

        with LocalTenant(self.other_tenant):
            link = LinkedGrantApplication.objects.get()
            self.assertEqual(link.start, self.model.started)

    def test_impact_location_maps_to_linked_grant_application_location(self):
        self.test_link()

        with LocalTenant(self.other_tenant):
            link = LinkedGrantApplication.objects.get()
            self.assertIsNotNone(self.model.impact_location)
            self.assertIsNotNone(link.location)
            self.assertEqual(link.location.locality, self.model.impact_location.locality)
            self.assertEqual(
                link.location.country.alpha2_code,
                self.model.impact_location.country.alpha2_code
            )


class TemplateGrantApplicationTestCase(TemplateTestCase, BluebottleTestCase):
    factory = GrantApplicationFactory

    def create(self, **kwargs):
        super().create(
            impact_location=GeolocationFactory.create(country=self.country),
            started=datetime.now(get_current_timezone()),
            **kwargs
        )
        self.model.states.submit(save=True)
        self.model.states.approve(save=True)
        adapter.sync(self.model)

    def test_publish(self):
        super().test_publish()

        with LocalTenant(self.other_tenant):
            self.assertEqual(self.event.target, self.model.target.amount)
            self.assertEqual(self.event.target_currency, str(self.model.target.currency))
            self.assertEqual(self.event.start_time, self.model.started)
            self.assertEqual(self.event.location.latitude, self.model.impact_location.position.x)
            self.assertEqual(self.event.location.longitude, self.model.impact_location.position.y)
            self.assertEqual(self.event.location.name, self.model.impact_location.formatted_address)
            self.assertEqual(
                self.event.location.address.country, self.model.impact_location.country.code
            )
            self.assertEqual(
                self.event.location.address.locality, self.model.impact_location.locality
            )

    def test_adopt(self):
        super().test_adopt()

        self.assertEqual(self.adopted.target, self.model.target)
        self.assertEqual(self.adopted.impact_location.position, self.model.impact_location.position)
        self.assertEqual(
            self.adopted.impact_location.country.alpha2_code,
            self.model.impact_location.country.alpha2_code
        )


@override_settings(
    MAPBOX_API_KEY=None
)
class LinkDeadlineActivityTestCase(LinkTestCase, BluebottleTestCase):
    factory = DeadlineActivityFactory

    def create(self, **kwargs):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            start=(datetime.now() + timedelta(days=10)).date(),
            deadline=(datetime.now() + timedelta(days=20)).date(),
            **kwargs
        )
        self.submit()


class TemplateDeadlineActivityTestCase(TemplateTestCase, BluebottleTestCase):
    factory = DeadlineActivityFactory

    def create(self, **kwargs):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            start=(datetime.now() + timedelta(days=10)).date(),
            deadline=(datetime.now() + timedelta(days=20)).date(),
            **kwargs
        )
        self.submit()

    def test_publish_with_organization(self):
        self.test_accept()
        organization = OrganizationFactory.create()
        ActivityPubTestCase.create(
            self,
            location=GeolocationFactory.create(country=self.country),
            start=(datetime.now() + timedelta(days=10)).date(),
            deadline=(datetime.now() + timedelta(days=20)).date(),
            organization=organization
        )
        self.submit()

        publish = self.model.activity_pub_model.create_set.get()
        Recipient.objects.create(actor=self.follow.actor, activity=publish)

        with LocalTenant(self.other_tenant):
            event = Event.objects.filter(name=self.model.title).first()
            self.assertTrue(event)
            self.assertTrue(event.organization)
            self.assertEqual(event.organization.name, organization.name)

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


@override_settings(
    MAPBOX_API_KEY=None
)
class LinkScheduleActivityTestCase(LinkTestCase, BluebottleTestCase):
    factory = ScheduleActivityFactory

    def create(self):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            organization=None
        )
        self.submit()

    def test_link(self):
        super().test_link()


class TemplateScheduleActivityTestCase(TemplateTestCase, BluebottleTestCase):
    factory = ScheduleActivityFactory

    def create(self):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            organization=None
        )
        self.submit()

    def test_publish(self):
        super().test_publish()

        with LocalTenant(self.other_tenant):
            self.assertEqual(self.event.start_time.date(), self.model.start)
            self.assertEqual(self.event.end_time.date(), self.model.deadline)
            self.assertEqual(self.event.duration, self.model.duration)

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


@override_settings(
    MAPBOX_API_KEY=None
)
class LinkPeriodicActivityTestCase(LinkTestCase, BluebottleTestCase):
    factory = PeriodicActivityFactory

    def create(self):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            organization=None
        )
        self.submit()


class TemplatePeriodicActivityTestCase(TemplateTestCase, BluebottleTestCase):
    factory = PeriodicActivityFactory

    def create(self):
        super().create(
            location=GeolocationFactory.create(country=self.country),
            organization=None
        )
        self.submit()

    def test_publish(self):
        super().test_publish()

        with LocalTenant(self.other_tenant):
            self.assertEqual(self.event.start_time.date(), self.model.start)
            self.assertEqual(self.event.duration, self.model.duration)
            self.assertEqual(self.event.repetition_mode, RepetitionModeChoices.weekly)

    def test_adopt(self):
        super().test_adopt()

        self.assertEqual(self.adopted.start, self.model.start)
        self.assertEqual(self.adopted.duration, self.model.duration)
        self.assertEqual(self.adopted.period, self.model.period)

        if self.model.location:
            self.assertEqual(
                self.adopted.location.position,
                self.model.location.position
            )


@override_settings(
    MAPBOX_API_KEY=None
)
class LinkRegisteredDateActivityTestCase(LinkTestCase, BluebottleTestCase):
    factory = RegisteredDateActivityFactory
    expected_link_status = 'succeeded'

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

    def test_cancel(self):
        pass


class TemplateRegisteredDateActivityTestCase(TemplateTestCase, BluebottleTestCase):
    factory = RegisteredDateActivityFactory

    def create(self):
        super().create(
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

    def complete(self):
        RegisteredDateParticipantFactory.create(activity=self.adopted)
        super().complete()

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


@override_settings(
    MAPBOX_API_KEY=None
)
class LinkedDateActivityTestCase(LinkTestCase, BluebottleTestCase):
    factory = DateActivityFactory

    def create(self, **kwargs):
        super().create(slots=[], organization=None)

        DateActivitySlotFactory.create_batch(
            3,
            activity=self.model,
            location=None,
            is_online=True,
            **kwargs
        )

        self.submit()


class TemplateDateActivityTestCase(TemplateTestCase, BluebottleTestCase):
    factory = DateActivityFactory

    def create(self, **kwargs):
        super().create(slots=[], organization=None, **kwargs)

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


class SyncDateActivityTestCase(SyncTestCase, BluebottleTestCase):
    factory = DateActivityFactory
    motivation = 'I would really like to join'
    participant_factory = DateParticipantFactory
    expected_participant_status = 'accepted'

    def create(self, **kwargs):
        super().create(slots=[], organization=None, **kwargs)

        DateActivitySlotFactory.create_batch(
            3,
            activity=self.model,
            location=None,
            is_online=True
        )

        self.submit()

    def join(self):
        registration = DateRegistrationFactory.create(
            activity=self.adopted,
            answer=self.motivation
        )
        self.participant = DateParticipantFactory.create(
            activity=self.adopted,
            slot=self.adopted.slots.first(),
            registration=registration
        )

    def test_join(self):
        super().test_join()
        self.assertEqual(self.synced_participant.registration.answer, self.motivation)


@override_settings(
    MAPBOX_API_KEY=None
)
class LinkedSingleSlotDateActivityTestCase(LinkTestCase, BluebottleTestCase):
    factory = DateActivityFactory

    def create(self, **kwargs):
        super().create(slots=[], **kwargs)

        DateActivitySlotFactory.create_batch(
            1,
            activity=self.model,
            location=GeolocationFactory.create(country=self.country),
        )

        self.submit()


class TemplateSingleSlotDateActivityTestCase(TemplateTestCase, BluebottleTestCase):
    factory = DateActivityFactory

    def create(self, **kwargs):
        super().create(slots=[], **kwargs)

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


@override_settings(
    MAPBOX_API_KEY=None
)
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

        with httmock.HTTMock(image_mock):
            new_collect_type = CollectTypeFactory.create()
            self.model.collect_type = new_collect_type
            self.model.save()

        with LocalTenant(self.other_tenant):
            link = LinkedActivity.objects.get()
            self.assertIsNotNone(link)


class TemplateCollectActivityTestCase(TemplateTestCase, BluebottleTestCase):
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
        self.assertEqual(self.adopted.collect_type.name, self.model.collect_type.name)
        if self.model.location:
            self.assertEqual(
                self.adopted.location.position,
                self.model.location.position
            )
