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

        self.other_team = TeamFactory.create(
            user=self.captain,
            activity=self.activity
        )
        self.url = reverse('team-member-list')

    def test_sign_up(self):
        data = {
            'data': {
                'attributes': {
                    'invite-code': self.team.invite_code,
                },
                'type': 'contributors/time-based/team-members',
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

        self.perform_create(user=self.existing_member, data=data)
        self.assertStatus(201)

        self.assertEqual(self.model.user, self.existing_member)
        self.assertEqual(self.model.team, self.team)

    def test_sign_up_same_team_twice(self):
        self.test_sign_up()

        data = {
            'data': {
                'attributes': {
                    'invite-code': self.team.invite_code,
                },
                'type': 'contributors/time-based/team-members',
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

        self.perform_create(user=self.existing_member, data=data)
        self.assertStatus(400)

    def test_sign_up_other_team(self):
        self.test_sign_up()
        data = {
            'data': {
                'attributes': {
                    'invite-code': self.other_team.invite_code,
                },
                'type': 'contributors/time-based/team-members',
                'relationships': {
                    'team': {
                        'data': {
                            'id': str(self.other_team.pk),
                            'type': 'contributors/time-based/teams'
                        }
                    }
                }
            }
        }

        self.perform_create(user=self.existing_member, data=data)
        self.assertStatus(201)
        self.assertEqual(
            len(self.activity.registrations.all()), 1
        )
        self.assertEqual(
            len(self.activity.participants.all()), 4
        )
        self.assertEqual(self.model.user, self.existing_member)
        self.assertEqual(self.model.team, self.other_team)

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
