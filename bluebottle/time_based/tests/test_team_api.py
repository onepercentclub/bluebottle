import json

from django.core import mail
from django.urls import reverse

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.notifications.models import ActivityMessageTemplate
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import APITestCase
from bluebottle.time_based.models import Team
from bluebottle.time_based.serializers.teams import TeamSerializer, TeamMemberSerializer
from bluebottle.time_based.tests.factories import (
    ScheduleActivityFactory, TeamFactory, TeamMemberFactory
)


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


class TeamListAPIViewTestCase(APITestCase):
    serializer = TeamSerializer
    model = Team

    def setUp(self):
        super().setUp()
        self.captain = BlueBottleUserFactory.create()
        initiative = InitiativeFactory.create(status='approved')
        self.activity = ScheduleActivityFactory.create(
            team_activity='teams',
            initiative=initiative,
            review=False,
        )
        self.activity.states.publish(save=True)
        ActivityMessageTemplate.objects.create(
            activity=self.activity,
            action='join',
            body_html=json.dumps({'html': '<p>Bring your own lunch</p>', 'delta': ''}),
            insert_method='append',
        )
        self.url = reverse('team-list')

    def register(self):
        data = {
            'data': {
                'type': 'contributors/time-based/team-schedule-registrations',
                'relationships': {
                    'activity': {
                        'data': {'id': str(self.activity.pk), 'type': 'activities/time-based/schedules'}
                    }
                }
            }
        }
        response = self.client.post(
            reverse('team-schedule-registration-list'),
            json.dumps(data),
            HTTP_AUTHORIZATION="JWT {0}".format(self.captain.get_jwt_token())
        )
        self.assertEqual(response.status_code, 201)

    def create_team(self, name):
        self.perform_create(
            user=self.captain,
            data={
                'data': {
                    'type': 'contributors/time-based/teams',
                    'attributes': {'name': name},
                    'relationships': {
                        'activity': {
                            'data': {'id': str(self.activity.pk), 'type': 'activities/time-based/schedules'}
                        }
                    }
                }
            }
        )
        self.assertStatus(201)

    def welcome_mails(self):
        return [
            message for message in mail.outbox
            if message.subject == 'You have registered your team on "Test"'
        ]

    def test_create_first_team(self):
        mail.outbox = []
        self.register()
        self.create_team('First team')

        welcome_mails = self.welcome_mails()
        self.assertEqual(len(welcome_mails), 1)
        self.assertEqual(welcome_mails[0].to, [self.captain.email])
        self.assertIn('Bring your own lunch', welcome_mails[0].body)

    def test_create_second_team(self):
        mail.outbox = []
        self.register()
        self.create_team('First team')
        first_team = self.model
        TeamMemberFactory.create(team=first_team)

        self.create_team('Second team')
        second_team = self.model
        TeamMemberFactory.create(team=second_team)

        self.assertEqual(second_team.registration, first_team.registration)
        welcome_mails = self.welcome_mails()
        self.assertEqual(len(welcome_mails), 2)
        for message in welcome_mails:
            self.assertEqual(message.to, [self.captain.email])
            self.assertIn('Bring your own lunch', message.body)

    def test_create_second_team_review(self):
        self.activity.review = True
        self.activity.save()

        self.register()
        self.create_team('First team')
        mail.outbox = []

        self.create_team('Second team')

        self.assertEqual(len(self.welcome_mails()), 0)


class TeamMemberListAPIViewTestCase(APITestCase):
    serializer = TeamMemberSerializer

    def setUp(self):
        super().setUp()
        self.manager = BlueBottleUserFactory.create()
        self.captain = BlueBottleUserFactory.create()
        self.existing_member = BlueBottleUserFactory.create(email='existing.member@example.com')
        self.activity = ScheduleActivityFactory.create(
            team_activity='teams',
            owner=self.manager
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

    def test_activity_owner_can_add_team_member(self):
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

        self.perform_create(user=self.manager, data=data)
        self.assertStatus(201)
        self.model.refresh_from_db()
        self.assertEqual(self.model.user, self.existing_member)
        self.assertEqual(self.model.team, self.team)
        self.assertIn(self.manager, self.activity.owners)
        self.assertNotEqual(self.manager, self.captain)
