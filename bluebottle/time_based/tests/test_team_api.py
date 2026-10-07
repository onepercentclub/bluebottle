from django.urls import reverse

from bluebottle.activities.models import RemoteMember
from bluebottle.initiatives.tests.factories import InitiativeFactory
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

    def test_manager_remote_captain_email(self):
        from bluebottle.activities.models import RemoteMember
        remote = RemoteMember.objects.create(
            email='remote-captain@example.com',
            first_name='Remote',
            last_name='Captain',
        )
        self.team.user = None
        self.team.remote_user = remote
        self.team.save()

        self.perform_get(self.manager)
        self.assertAttribute('captain-email', remote.email)


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


class RelatedTeamListSyncedTeamAPIViewTestCase(APITestCase):
    """
    BB-30309: a team synced from a consumer platform has no local captain
    (user is NULL, remote_user is set). The activity's `teams` links count it,
    so the sidebar says "1 team participating", but the list behind the
    link the public Teams tab loads (`active`) should then also return it.
    """
    serializer = TeamSerializer

    def setUp(self):
        super().setUp()
        self.manager = BlueBottleUserFactory.create()
        self.other_user = BlueBottleUserFactory.create()

        initiative = InitiativeFactory.create()
        self.activity = ScheduleActivityFactory.create(
            team_activity='teams',
            owner=self.manager,
            initiative=initiative,
            review=False,
        )
        initiative.states.submit()
        initiative.states.approve(save=True)
        self.activity.states.publish(save=True)

        remote_captain = RemoteMember.objects.create(
            email='cas@example.com',
            first_name='Cas',
            last_name='Consumer',
        )
        self.team = TeamFactory.create(
            activity=self.activity,
            user=None,
            remote_user=remote_captain,
        )

    def schedule_team(self):
        # Scheduling a synced team through its slot syncs back to the consumer,
        # which needs the federated Team actor. That flow is covered in
        # activity_pub's SyncTeamScheduleActivityTestCase; here we only care
        # about what the list returns, so set the status directly.
        Team.objects.filter(pk=self.team.pk).update(status='scheduled')

    def get_link(self, name, user=None):
        self.url = reverse('schedule-detail', args=(self.activity.pk,))
        self.perform_get(user=user)
        self.assertStatus(200)
        return self.response.json()['data']['relationships']['teams']['links'][name]

    def assertListMatchesLink(self, name, user=None):
        link = self.get_link(name, user=user)
        self.assertEqual(link['meta']['count'], 1)

        self.url = link['href']
        self.perform_get(user=user)
        self.assertStatus(200)
        self.assertObjectList(models=[self.team])

    def test_synced_team_has_no_local_captain(self):
        self.assertIsNone(self.team.user)
        self.assertIsNone(self.team.owner)
        self.assertEqual(self.team.status, 'accepted')

    def test_unscheduled_synced_team_manager(self):
        self.assertListMatchesLink('unscheduled', user=self.manager)

    def test_unscheduled_synced_team_other_user(self):
        self.assertListMatchesLink('unscheduled', user=self.other_user)

    def test_scheduled_synced_team_manager(self):
        self.schedule_team()
        self.assertListMatchesLink('active', user=self.manager)

    def test_scheduled_synced_team_other_user(self):
        self.schedule_team()
        self.assertListMatchesLink('active', user=self.other_user)

    def test_scheduled_synced_team_anonymous(self):
        self.schedule_team()
        self.assertListMatchesLink('active')
