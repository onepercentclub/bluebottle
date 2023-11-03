
import datetime
from builtins import str

from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now
from rest_framework import status

from bluebottle.activities.models import Contribution, Contributor, Activity
from bluebottle.funding.tests.factories import DonorFactory
from bluebottle.impact.tests.factories import (
    ImpactTypeFactory, ImpactGoalFactory
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.statistics.tests.factories import (
    DatabaseStatisticFactory, ManualStatisticFactory, ImpactStatisticFactory
)
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient
from bluebottle.time_based.tests.factories import DateActivityFactory, DateParticipantFactory


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
)
class StatisticListListAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(StatisticListListAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.url = reverse('statistics')
        self.user = BlueBottleUserFactory()

        initiative = InitiativeFactory.create()
        activity = DateActivityFactory.create(
            initiative=initiative,
            owner=initiative.owner,
        )
        initiative.states.submit(save=True)
        initiative.states.approve(save=True)
        activity.states.submit(save=True)

        slot = activity.slots.get()
        slot.start = timezone.now() - datetime.timedelta(hours=1)
        slot.duration = datetime.timedelta(minutes=6)
        slot.save()

        DateParticipantFactory.create_batch(5, activity=activity)

        self.impact_type = ImpactTypeFactory.create()

        self.impact_goal = ImpactGoalFactory.create(
            type=self.impact_type,
            target=100,
            realized=50
        )

        self.manual = ManualStatisticFactory.create()
        self.impact = ImpactStatisticFactory(impact_type=self.impact_type)
        self.database = DatabaseStatisticFactory(query='people_involved')

    def test_get(self):
        response = self.client.get(self.url, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json()['data']), 3)

        for resource in response.json()['data']:
            if resource['id'] == str(self.manual.pk):
                self.assertEqual(resource['type'], 'statistics')
                self.assertEqual(resource['attributes']['value'], self.manual.value)
                self.assertEqual(resource['attributes']['name'], self.manual.name)

            if resource['id'] == str(self.impact.pk):
                self.assertEqual(resource['type'], 'statistics')
                self.assertEqual(resource['attributes']['value'], self.impact_goal.realized)
                self.assertEqual(resource['attributes']['name'], self.impact_type.text_passed)
                self.assertEqual(resource['attributes']['icon'], self.impact_type.icon)

            if resource['id'] == str(self.database.pk):
                self.assertEqual(resource['type'], 'statistics')
                self.assertEqual(resource['attributes']['value'], 7)
                self.assertEqual(resource['attributes']['name'], self.database.name)

    def test_get_anonymous(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)

    def test_get_only_active(self):
        self.manual.active = False
        self.manual.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

    def test_get_closed(self):
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_closed_anonymous(self):
        MemberPlatformSettings.objects.update(closed=True)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post(self):
        response = self.client.post(self.url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_filter_by_year(self):
        response = self.client.get(self.url + '?year=' + str(now().year))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
)
class OldStatisticListListAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(OldStatisticListListAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.url = reverse('statistic-list')
        self.user = BlueBottleUserFactory()

        initiative = InitiativeFactory.create()
        activity = DateActivityFactory.create(
            initiative=initiative,
            owner=initiative.owner,
        )
        initiative.states.submit(save=True)
        initiative.states.approve(save=True)
        activity.states.submit(save=True)

        slot = activity.slots.get()
        slot.start = timezone.now() - datetime.timedelta(hours=1)
        slot.duration = datetime.timedelta(minutes=6)
        slot.save()

        DateParticipantFactory.create_batch(5, activity=activity)

        self.impact_type = ImpactTypeFactory.create()

        self.impact_goal = ImpactGoalFactory.create(
            type=self.impact_type,
            target=100,
            realized=50
        )

        self.manual = ManualStatisticFactory.create()
        self.impact = ImpactStatisticFactory(impact_type=self.impact_type)
        self.database = DatabaseStatisticFactory(query='people_involved')

    def test_get(self):
        response = self.client.get(self.url, user=self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.json()['data']), 3)

        for resource in response.json()['data']:
            if resource['id'] == str(self.manual.pk):
                self.assertEqual(resource['type'], 'statistics/manual-statistics')
                self.assertEqual(resource['attributes']['value'], self.manual.value)
                self.assertEqual(resource['attributes']['name'], self.manual.name)

            if resource['id'] == str(self.impact.pk):
                self.assertEqual(resource['type'], 'statistics/impact-statistics')
                self.assertEqual(resource['attributes']['value'], self.impact_goal.realized)
                self.assertEqual(resource['relationships']['impact-type']['data']['id'], str(self.impact_type.pk))

            if resource['id'] == str(self.database.pk):
                self.assertEqual(resource['type'], 'statistics/database-statistics')
                self.assertEqual(resource['attributes']['value'], 7)
                self.assertEqual(resource['attributes']['name'], self.database.name)

        self.assertEqual(response.json()['included'][0]['id'], str(self.impact_type.pk))
        self.assertEqual(response.json()['included'][0]['type'], 'activities/impact-types')


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
)
class StatisticYearFilterListAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(StatisticYearFilterListAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.url = reverse('statistic-list')
        self.user = BlueBottleUserFactory()

        activity1 = DateActivityFactory.create()
        activity1.created = now().replace(year=2020, month=6, day=12)
        activity1.save()
        activity2 = DateActivityFactory.create()
        activity2.created = now().replace(year=2021, month=10, day=12)
        activity2.save()

        slot1 = activity1.slots.first()
        slot1.start = now().replace(year=2020, month=6, day=12)
        slot1.duration = datetime.timedelta(hours=4)
        slot1.save()

        slot2 = activity2.slots.first()
        slot2.start = now().replace(year=2021, month=1, day=12)
        slot2.duration = datetime.timedelta(hours=8)
        slot2.save()

        DateParticipantFactory.create_batch(3, activity=activity1)
        DateParticipantFactory.create_batch(2, activity=activity2)

        self.impact_type = ImpactTypeFactory.create()

        ImpactGoalFactory.create(
            activity=activity1,
            type=self.impact_type,
            realized=50
        )
        ImpactGoalFactory.create(
            activity=activity2,
            type=self.impact_type,
            realized=100
        )

        donations = DonorFactory.create_batch(2)
        for don in donations:
            don.created = now().replace(year=2020, month=8)
            don.save()

        donations = DonorFactory.create_batch(3)
        for don in donations:
            don.created = now().replace(year=2021, month=2, day=12)
            don.save()

        Contribution.objects.update(status='succeeded')
        Contributor.objects.update(status='succeeded')
        Activity.objects.update(status='succeeded')

        self.manual = ManualStatisticFactory.create(value=35)
        self.impact = ImpactStatisticFactory(impact_type=self.impact_type)
        self.database = DatabaseStatisticFactory(query='participants')
        self.money = DatabaseStatisticFactory(query='donated_total')
        self.manual.sequence = 0
        self.manual.save()
        self.impact.sequence = 1
        self.impact.save()
        self.database.sequence = 2
        self.database.save()
        self.money.sequence = 3
        self.money.save()

    def test_filter_by_year_2020(self):
        response = self.client.get(self.url + '?year=2020')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]['attributes']['value'], 35)
        self.assertEqual(data[1]['attributes']['value'], 50.0)
        self.assertEqual(data[2]['attributes']['value'], 3)
        self.assertEqual(data[3]['attributes']['value'], {'amount': 70.0, 'currency': 'EUR'})

    def test_filter_by_year_2021(self):
        response = self.client.get(self.url + '?year=2021')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]['attributes']['value'], 35)
        self.assertEqual(data[1]['attributes']['value'], 100.0)
        self.assertEqual(data[2]['attributes']['value'], 2)
        self.assertEqual(data[3]['attributes']['value'], {'amount': 105.0, 'currency': 'EUR'})

    def test_filter_by_fiscal_year_2020(self):
        settings = MemberPlatformSettings.load()
        settings.fiscal_month_offset = 4
        settings.save()
        response = self.client.get(self.url + '?year=2020')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]['attributes']['value'], 35)
        self.assertEqual(data[1]['attributes']['value'], 50.0)
        self.assertEqual(data[2]['attributes']['value'], 5)
        self.assertEqual(data[3]['attributes']['value'], {'amount': 175.0, 'currency': 'EUR'})

    def test_filter_by_fiscal_year_2021(self):
        settings = MemberPlatformSettings.load()
        settings.fiscal_month_offset = -4
        settings.save()
        response = self.client.get(self.url + '?year=2021')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]['attributes']['value'], 35)
        self.assertEqual(data[1]['attributes']['value'], 0.0)
        self.assertEqual(data[2]['attributes']['value'], 2)
        self.assertEqual(data[3]['attributes']['value'], {'amount': 105.0, 'currency': 'EUR'})

    def test_no_filter(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]['attributes']['value'], 35)
        self.assertEqual(data[1]['attributes']['value'], 150.0)
        self.assertEqual(data[2]['attributes']['value'], 5)
        self.assertEqual(data[3]['attributes']['value'], {'amount': 175.0, 'currency': 'EUR'})
