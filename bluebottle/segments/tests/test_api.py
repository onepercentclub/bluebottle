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
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.segments.models import Segment, SegmentType
from bluebottle.segments.serializers import SegmentSerializer
from bluebottle.segments.tests.factories import SegmentFactory, SegmentTypeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient, APITestCase
from bluebottle.time_based.tests.factories import PeriodActivityFactory, \
    PeriodParticipantFactory, DateActivityFactory, \
    DateActivitySlotFactory, DateParticipantFactory


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
                type=segment_type
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
        self.assertEqual(
            set(relation['id'] for relation in result['relationships']['segments']['data']),
            set(str(segment.pk) for segment in segment_type.segments.all())
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
            type=self.segment_type
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
            str(segment.type_id),
            result['relationships']['type']['data']['id']
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
        SegmentFactory.create(type=inactive_type)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            len(response.json()['data']), 20
        )


class SegmentDetailAPITestCase(APITestCase):

    def setUp(self):
        super().setUp()

        self.serializer = SegmentSerializer
        self.factory = SegmentFactory

        self.segment_type = SegmentTypeFactory.create()
        self.model = SegmentFactory.create(type=self.segment_type)

        self.fields = []

        self.url = reverse('segment-detail', args=(self.model.pk, ))

    def test_retrieve(self):
        self.perform_get()

        self.assertStatus(status.HTTP_200_OK)
        self.assertIncluded('type', self.segment_type)
        self.assertAttribute('name', self.model.name)
        self.assertAttribute('slug', self.model.slug)
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

    def test_retrieve_closed(self):
        with self.closed_site():
            self.perform_get()

        self.assertStatus(status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_closed_user(self):
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
        period_activity = PeriodActivityFactory.create(
            status='succeeded',
            start=datetime.date.today() - datetime.timedelta(weeks=2),
            deadline=datetime.date.today() - datetime.timedelta(weeks=1),
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=3)
        )
        period_activity.segments.set([self.model])
        PeriodParticipantFactory.create_batch(3, activity=period_activity)

        date_activity = DateActivityFactory.create(
            status='succeeded',
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=2)
        )
        date_activity.segments.set([self.model])
        DateActivitySlotFactory.create(
            activity=date_activity,
            start=now() - datetime.timedelta(weeks=1),
        )
        DateParticipantFactory.create_batch(3, activity=date_activity)

        funding = FundingFactory.create(
            deadline=now() - datetime.timedelta(weeks=1),
            status='succeeded'
        )
        funding.segments.set([self.model])
        for donor in DonorFactory.create_batch(3, activity=funding, user=None, amount=Money(10, 'USD')):
            donor.contributions.get().states.succeed(save=True)
        for donor in DonorFactory.create_batch(3, activity=funding, user=None, amount=Money(10, 'EUR')):
            donor.contributions.get().states.succeed(save=True)

        deed_activity = DeedFactory.create(
            status='succeeded',
            start=datetime.date.today() - datetime.timedelta(days=10),
            end=datetime.date.today() - datetime.timedelta(days=5)
        )
        deed_activity.segments.set([self.model])

        DeedParticipantFactory.create_batch(3, activity=deed_activity)
        participants = DeedParticipantFactory.create_batch(3, activity=deed_activity)
        for participant in participants:
            participant.states.withdraw(save=True)

        collect_activity = CollectActivityFactory.create(
            status='succeeded',
            start=datetime.date.today() - datetime.timedelta(weeks=2),
        )
        collect_activity.segments.set([self.model])
        collect_activity.realized = 100
        collect_activity.save()
        CollectContributorFactory.create_batch(3, activity=collect_activity)

        unrelated_activity = PeriodActivityFactory.create(
            status='succeeded',
            start=datetime.date.today() - datetime.timedelta(weeks=2),
            deadline=datetime.date.today() - datetime.timedelta(weeks=1),
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=3)
        )
        PeriodParticipantFactory.create_batch(3, activity=unrelated_activity)

        response = self.client.get(
            self.url,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.json()['data']['meta']['stats']
        self.assertEqual(stats['hours'], 66.0)
        self.assertEqual(stats['activities'], 5)
        self.assertEqual(stats['amount'], {'amount': 75.0, 'currency': 'EUR'})
        self.assertEqual(stats['contributors'], 18)
        self.assertEqual(stats['effort'], 3)

        self.assertEqual(
            stats['collected'][str(collect_activity.collect_type_id)], collect_activity.realized
        )
