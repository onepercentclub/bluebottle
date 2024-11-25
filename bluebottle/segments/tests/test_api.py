# coding=utf-8
import datetime
from builtins import range
from builtins import str

from django.urls import reverse
from django.utils.timezone import now
from moneyed import Money
from rest_framework import status

from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.funding.tests.factories import FundingFactory, DonorFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.models import Segment, SegmentType
from bluebottle.segments.serializers import SegmentDetailSerializer, SegmentPublicDetailSerializer
from bluebottle.segments.tests.factories import SegmentFactory, SegmentTypeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient, APITestCase
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
    SlotParticipantFactory,
)


class SegmentTypeListAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(SegmentTypeListAPITestCase, self).setUp()

        self.client = JSONAPITestClient()

        self.url = reverse('segment-type-list')
        self.user = BlueBottleUserFactory()

        for i in range(5):
            segment_type = SegmentTypeFactory.create()
            SegmentFactory.create_batch(
                3,
                segment_type=segment_type
            )

    def test_list(self):
        response = self.client.get(self.url, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 5
        )
        result = response.json()['data'][0]

        segment_type = SegmentType.objects.get(pk=result['id'])

        self.assertEqual(segment_type.name, result['attributes']['name'])

        self.assertTrue(
            result['relationships']['segments']['links']['related'].endswith(
                reverse('related-segment-detail', args=(segment_type.pk, ))
            )
        )

    def test_list_anonymous(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 5
        )

    def test_list_closed(self):
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_inactive(self):
        SegmentTypeFactory.create(is_active=False)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 5
        )


class SegmentListAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(SegmentListAPITestCase, self).setUp()

        self.client = JSONAPITestClient()

        self.url = reverse('segment-list')
        self.user = BlueBottleUserFactory()
        self.segment_type = SegmentTypeFactory.create()
        self.segments = SegmentFactory.create_batch(
            20,
            segment_type=self.segment_type
        )

    def test_list(self):
        response = self.client.get(self.url, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 20
        )
        result = response.json()['data'][0]

        segment = Segment.objects.get(pk=result['id'])

        self.assertEqual(segment.name, result['attributes']['name'])
        self.assertEqual(
            str(segment.segment_type_id),
            result['relationships']['segment-type']['data']['id']
        )

    def test_list_anonymous(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 20
        )

    def test_list_closed(self):
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_inactive(self):
        inactive_type = SegmentTypeFactory(is_active=False)
        SegmentFactory.create(segment_type=inactive_type)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 20
        )


class SegmentDetailAPITestCase(APITestCase):

    def setUp(self):
        super().setUp()

        self.serializer = SegmentDetailSerializer
        self.factory = SegmentFactory

        self.segment_type = SegmentTypeFactory.create()
        self.model = SegmentFactory.create(segment_type=self.segment_type)

        self.fields = []

        self.url = reverse('segment-detail', args=(self.model.pk, ))

    def test_retrieve(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertIncluded('segment-type', self.segment_type)
        self.assertAttribute('name', self.model.name)
        self.assertAttribute('slug', self.model.slug)
        self.assertAttribute('email-domains', self.model.email_domains)
        self.assertAttribute('tag-line', self.model.tag_line)
        self.assertAttribute('story', self.model.story)
        self.assertAttribute('background-color', self.model.background_color)
        self.assertAttribute('text-color', self.model.text_color)
        self.assertAttribute('logo')
        self.assertAttribute('cover-image')

    def test_story_escaped(self):
        self.model.story = '<script>test</script><b>test</b>'
        self.model.save()

        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('story', '&lt;script&gt;test&lt;/script&gt;<b>test</b>')

    def test_retrieve_closed_site(self):
        with self.closed_site():
            self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_closed_site_user(self):
        with self.closed_site():
            self.perform_get(user=BlueBottleUserFactory.create())

        self.assertStatus(status.HTTP_200_OK)

    def test_update(self):
        self.perform_update({'name': 'test'})

        self.assertStatus(status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete(self):
        self.perform_delete()

        self.assertStatus(status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_stats(self):
        initiative = InitiativeFactory.create(status='approved')

        period_activity = DeadlineActivityFactory.create(
            initiative=initiative,
            status='succeeded',
            start=datetime.date.today() - datetime.timedelta(weeks=2),
            deadline=datetime.date.today() - datetime.timedelta(weeks=1),
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=3)
        )
        period_activity.segments.set([self.model])
        DeadlineParticipantFactory.create_batch(3, activity=period_activity)

        date_activity = DateActivityFactory.create(
            initiative=initiative,
            status='succeeded',
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=2)
        )
        date_activity.segments.set([self.model])
        slot = DateActivitySlotFactory.create(
            activity=date_activity,
            start=now() - datetime.timedelta(weeks=1),
        )

        participants = DateParticipantFactory.create_batch(3, activity=date_activity)
        for participant in participants:
            SlotParticipantFactory.create(slot=slot, participant=participant)

        funding = FundingFactory.create(
            initiative=initiative,
            deadline=now() + datetime.timedelta(weeks=1),
            status='open'
        )
        funding.segments.set([self.model])
        for donor in DonorFactory.create_batch(3, activity=funding, user=None, amount=Money(10, 'USD')):
            donor.contributions.get().states.succeed(save=True)
        for donor in DonorFactory.create_batch(3, activity=funding, user=None, amount=Money(10, 'EUR')):
            donor.contributions.get().states.succeed(save=True)

        deed_activity = DeedFactory.create(
            initiative=initiative,
            status='open',
            start=datetime.date.today() - datetime.timedelta(days=10),
            end=datetime.date.today() + datetime.timedelta(days=5)
        )
        deed_activity.segments.set([self.model])

        DeedParticipantFactory.create_batch(3, activity=deed_activity)
        participants = DeedParticipantFactory.create_batch(3, activity=deed_activity)
        for participant in participants:
            participant.states.withdraw(save=True)

        collect_activity = CollectActivityFactory.create(
            initiative=initiative,
            status='open',
            start=datetime.date.today() + datetime.timedelta(weeks=2),
        )
        collect_activity.segments.set([self.model])
        collect_activity.realized = 100
        collect_activity.save()
        CollectContributorFactory.create_batch(3, activity=collect_activity)

        unrelated_activity = DeadlineActivityFactory.create(
            initiative=initiative,
            status='open',
            start=datetime.date.today() - datetime.timedelta(weeks=2),
            deadline=datetime.date.today() + datetime.timedelta(weeks=1),
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=3)
        )
        DeadlineParticipantFactory.create_batch(3, activity=unrelated_activity)

        response = self.client.get(
            self.url,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json()['data']['meta']['activities-count'], 4)
        self.assertEqual(response.json()['data']['meta']['initiatives-count'], 1)

        stats = response.json()["data"]["meta"]["stats"]
        self.assertEqual(stats["hours"], 18.0)
        self.assertEqual(stats["amount"], {"amount": 75.0, "currency": "EUR"})
        self.assertEqual(stats["contributors"], 18)
        self.assertEqual(stats["effort"], 3)

    def test_retrieve_closed_segment(self):
        closed_segment = SegmentFactory.create(
            segment_type=self.segment_type,
            closed=True
        )
        self.url = reverse('segment-detail', args=(closed_segment.id,))
        user = BlueBottleUserFactory()
        self.perform_get(user=user)
        self.assertStatus(status.HTTP_403_FORBIDDEN)

    def test_retrieve_closed_segment_user(self):
        closed_segment = SegmentFactory.create(
            segment_type=self.segment_type,
            closed=True
        )
        self.url = reverse('segment-detail', args=(closed_segment.id,))
        user = BlueBottleUserFactory()
        user.segments.add(closed_segment)
        self.perform_get(user=user)
        self.assertStatus(status.HTTP_200_OK)

    def test_retrieve_closed_segment_staff(self):
        closed_segment = SegmentFactory.create(
            segment_type=self.segment_type,
            closed=True
        )
        self.url = reverse('segment-detail', args=(closed_segment.id,))
        user = BlueBottleUserFactory(is_staff=True)
        self.perform_get(user=user)
        self.assertStatus(status.HTTP_200_OK)


class SegmentPublicDetailAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.serializer = SegmentPublicDetailSerializer
        self.factory = SegmentFactory
        self.model = self.factory()

        self.url = reverse('segment-public-detail', args=(self.model.pk,))

    def test_get(self):
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)
        self.assertAttribute('name', self.model.name)
        self.assertAttribute('logo')
        self.assertNoAttribute('story')
        self.assertNotIncluded('segment-types')

        self.assertTrue(self.response.json()['data']['attributes']['logo'].startswith('/media/cache'))

    def test_get_closed_segment(self):
        self.model.closed = True
        self.model.save()

        self.test_get()

    def test_get_closed_platform(self):
        with self.closed_site():
            self.perform_get()
            self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_get_closed_platform_logged_in(self):
        with self.closed_site():
            self.perform_get(user=self.user)
            self.assertStatus(status.HTTP_200_OK)


class SegmentActivityDetailAPITestCase(APITestCase):

    def setUp(self):
        super().setUp()

        self.serializer = SegmentDetailSerializer
        self.factory = SegmentFactory

        self.segment_type = SegmentTypeFactory.create()
        self.closed_segment = SegmentFactory.create(segment_type=self.segment_type, closed=True)
        self.model = DeedFactory.create(status='open')
        self.model.segments.add(self.closed_segment)
        self.url = reverse('deed-detail', args=(self.model.pk, ))

    def test_retrieve_anonymous(self):
        self.perform_get()
        self.assertStatus(status.HTTP_401_UNAUTHORIZED)
        data = self.response.json()
        self.assertEqual(data['errors'][0]['detail'], str(self.closed_segment.id))
        self.assertEqual(data['errors'][0]['code'], 'closed_segment')

    def test_retrieve_user(self):
        user = BlueBottleUserFactory.create()
        self.perform_get(user=user)
        self.assertStatus(status.HTTP_403_FORBIDDEN)
        data = self.response.json()
        self.assertEqual(data['errors'][0]['detail'], str(self.closed_segment.id))
        self.assertEqual(data['errors'][0]['code'], 'closed_segment')

    def test_retrieve_staff(self):
        user = BlueBottleUserFactory.create(is_staff=True)
        self.perform_get(user=user)
        self.assertStatus(status.HTTP_200_OK)

    def test_retrieve_user_with_segment(self):
        user = BlueBottleUserFactory.create()
        user.segments.add(self.closed_segment)
        self.perform_get(user=user)
        self.assertStatus(status.HTTP_200_OK)

        self.assertStatus(status.HTTP_200_OK)

    def test_retrieve_activity_with_segment(self):
        self.model = DeedFactory.create()
        segment = SegmentFactory.create(segment_type=self.segment_type)
        self.model.segments.add(segment)
        self.url = reverse('deed-detail', args=(self.model.pk,))
        user = BlueBottleUserFactory.create()
        self.perform_get(user=user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertEqual(
            len(self.response.data["segments"]),
            1
        )

    def test_retrieve_activity_with_invisible_segment(self):
        self.model = DeedFactory.create()
        segment = SegmentFactory.create(segment_type=self.segment_type)
        self.model.segments.add(segment)
        self.url = reverse('deed-detail', args=(self.model.pk,))
        user = BlueBottleUserFactory.create()
        self.segment_type.visibility = False
        self.segment_type.save()
        self.perform_get(user=user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertEqual(
            len(self.response.data["segments"]),
            0
        )


class RelatedSegmentListAPITestCase(APITestCase):

    def setUp(self):
        super().setUp()

        self.serializer = SegmentDetailSerializer

        self.segment_type = SegmentTypeFactory.create()
        self.segments = SegmentFactory.create_batch(10, segment_type=self.segment_type)

        self.url = reverse('related-segment-detail', args=(self.segment_type.pk, ))

    def test_get(self):
        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)
        self.assertSize(10)

        self.assertAttribute('name')
        self.assertAttribute('logo')
        self.assertAttribute('story')

    def test_get_closed_segment(self):
        self.segments[0].closed = True
        self.segments[0].save()

        self.perform_get()
        self.assertStatus(status.HTTP_200_OK)
        self.assertSize(9)

    def test_get_closed_segments_user(self):
        self.segments[0].closed = True
        self.segments[0].save()
        self.user.segments.add(self.segments[0])
        self.user.save()

        self.perform_get(user=self.user)
        self.assertStatus(status.HTTP_200_OK)
        self.assertSize(10)

    def test_get_closed_platform(self):
        with self.closed_site():
            self.perform_get()
            self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_get_closed_platform_logged_in(self):
        with self.closed_site():
            self.perform_get(user=self.user)
            self.assertStatus(status.HTTP_200_OK)
