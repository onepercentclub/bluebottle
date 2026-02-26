from django.urls import reverse

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase
from bluebottle.time_based.models import Team
from bluebottle.time_based.serializers.teams import TeamSerializer, TeamMemberSerializer
from bluebottle.time_based.tests.factories import ScheduleActivityFactory, TeamFactory


class TeamDetailAPIViewTestCase(APITestCase):

    serializer = TeamSerializer
    fields = [
        'id', 'name', 'status', 'user'
    ]
    defaults = {}
    model = Team

    def setUp(self):
        super().setUp()
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


class TeamMemberListAPIViewTestCase(APITestCase):
    serializer = TeamMemberSerializer

    def setUp(self):
        super().setUp()
        self.captain = BlueBottleUserFactory.create()
        self.existing_member = BlueBottleUserFactory.create(email='existing.member@example.com')
        self.activity = ScheduleActivityFactory.create(
            team_activity='teams',
            owner=self.captain
        )
        self.team = TeamFactory.create(
            user=self.captain,
            activity=self.activity
        )
        self.url = reverse('team-member-list')

    def test_add_team_member_by_existing_email(self):
        data = {
            'data': {
                'type': 'contributors/time-based/team-members',
                'attributes': {
                    'email': self.existing_member.email
                },
                'relationships': {
                    'team': {
                        'data': {
                            'id': str(self.team.pk),
                            'type': 'contributors/time-based/teams'
                        }
                    }
                }
            }
        }

        self.perform_create(user=self.captain, data=data)
        self.assertStatus(201)
        self.model.refresh_from_db()
        self.assertEqual(self.model.user, self.existing_member)
        self.assertEqual(self.model.team, self.team)
