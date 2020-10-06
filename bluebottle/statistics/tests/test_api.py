
from builtins import str
import datetime

from django.urls import reverse
from django.utils import timezone
from django.test.utils import override_settings

from rest_framework import status

from bluebottle.statistics.tests.factories import (
    DatabaseStatisticFactory, ManualStatisticFactory, ImpactStatisticFactory
)
from bluebottle.impact.tests.factories import (
    ImpactTypeFactory, ImpactGoalFactory
)
from bluebottle.events.tests.factories import EventFactory, ParticipantFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
)
class ImpactTypeListAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(ImpactTypeListAPITestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.url = reverse('statistic-list')
        self.user = BlueBottleUserFactory()

        initiative = InitiativeFactory.create()
        event = EventFactory.create(
            initiative=initiative,
            owner=initiative.owner,
            start=timezone.now() - datetime.timedelta(hours=1),
            duration=0.1

        )

        initiative.states.submit(save=True)
        initiative.states.approve(save=True)

        event.refresh_from_db()

        ParticipantFactory.create_batch(5, activity=event)

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
