from django.urls import reverse

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase
from bluebottle.time_based.models import Team
from bluebottle.time_based.serializers.teams import TeamSerializer
from bluebottle.time_based.tests.factories import ScheduleActivityFactory, TeamFactory


class TeamDetailAPIViewTestCase(APITestCase):

    serializer = TeamSerializer
    fields = [
        'id', 'name', 'status', 'user'
    ]
    defaults = {}
    model = Team

    def setUp(self):
        self.captain = BlueBottleUserFactory.create()
        self.manager = BlueBottleUserFactory.create()
        self.user = BlueBottleUserFactory.create()

        self.activity = ScheduleActivityFactory.create(
            team_activity='teams',
            owner=self.manager
        )
        self.team = TeamFactory.create(
            user=self.captain,
            activity=self.activity
        )
        self.url = reverse('team-detail', args=(self.team.pk,))

    def test_manager_captain_email(self):
        self.perform_get(self.manager)
        self.assertAttribute('captain-email', self.captain.email)

    def test_user_captain_email(self):
        self.perform_get(self.user)
        self.assertAttribute('captain-email', None)
