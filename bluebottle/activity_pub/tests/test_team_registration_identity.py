from rest_framework.exceptions import ValidationError

from bluebottle.activities.models import RemoteMember
from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import Team as ActivityPubTeam
from bluebottle.activity_pub.serializers.federated_activities import (
    TeamScheduleParticipantSerializer,
    TeamScheduleRegistrationSerializer,
)
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.effects.teams import CreateTeamRegistrationEffect
from bluebottle.time_based.models import Team, TeamScheduleRegistration
from bluebottle.time_based.tests.factories import (
    ScheduleActivityFactory,
    TeamFactory,
)


class CreateTeamRegistrationRemoteCaptainTestCase(BluebottleTestCase):
    def setUp(self):
        initiative = InitiativeFactory.create()
        self.activity = ScheduleActivityFactory.create(
            team_activity='teams',
            initiative=initiative,
        )
        initiative.states.submit()
        initiative.states.approve(save=True)
        self.activity.states.publish(save=True)

        self.remote_one = RemoteMember.objects.create(
            first_name='Remote',
            last_name='One',
            email='remote-one@example.com',
        )
        self.remote_two = RemoteMember.objects.create(
            first_name='Remote',
            last_name='Two',
            email='remote-two@example.com',
        )

    def test_second_remote_team_uses_own_registration(self):
        team_one = Team(
            activity=self.activity,
            user=None,
            remote_user=self.remote_one,
        )
        team_one.execute_triggers()
        team_one.save()

        team_two = Team(
            activity=self.activity,
            user=None,
            remote_user=self.remote_two,
        )
        team_two.execute_triggers()
        team_two.save()

        team_one.refresh_from_db()
        team_two.refresh_from_db()

        self.assertIsNotNone(team_one.registration_id)
        self.assertIsNotNone(team_two.registration_id)
        self.assertNotEqual(team_one.registration_id, team_two.registration_id)
        self.assertEqual(team_one.registration.remote_user_id, self.remote_one.id)
        self.assertEqual(team_two.registration.remote_user_id, self.remote_two.id)
        self.assertIsNone(team_one.registration.user_id)
        self.assertIsNone(team_two.registration.user_id)
        self.assertEqual(
            TeamScheduleRegistration.objects.filter(activity=self.activity).count(),
            2,
        )

    def test_missing_captain_identity_raises(self):
        team = Team(activity=self.activity, user=None, remote_user=None)
        effect = CreateTeamRegistrationEffect(team)
        with self.assertRaises(ValueError) as error:
            effect.post_save()
        self.assertIn('captain identity', str(error.exception))


class TeamScheduleParticipantSerializerValidationTestCase(BluebottleTestCase):
    def setUp(self):
        initiative = InitiativeFactory.create()
        self.activity = ScheduleActivityFactory.create(
            team_activity='teams',
            initiative=initiative,
        )
        initiative.states.submit()
        initiative.states.approve(save=True)
        self.activity.states.publish(save=True)
        self.team = TeamFactory.create(activity=self.activity)
        self.slot = self.team.slots.get()
        self.remote_user = RemoteMember.objects.create(
            first_name='Pat',
            last_name='Participant',
            email='pat@example.com',
        )
        self.serializer = TeamScheduleParticipantSerializer()

    def test_missing_registration_raises_validation_error(self):
        with self.assertRaises(ValidationError) as error:
            self.serializer.create({
                'activity': self.activity,
                'slot': self.slot,
                'remote_user': self.remote_user,
            })
        self.assertIn('TeamScheduleRegistration', str(error.exception.detail))

    def test_registration_without_team_raises_validation_error(self):
        registration = TeamScheduleRegistration(
            activity=self.activity,
            remote_user=self.remote_user,
            user=None,
        )
        registration.execute_triggers()
        registration.save()
        self.assertFalse(registration.teams.exists())

        with self.assertRaises(ValidationError) as error:
            self.serializer.create({
                'activity': self.activity,
                'slot': self.slot,
                'remote_user': self.remote_user,
            })
        self.assertIn('no team', str(error.exception.detail).lower())


class TeamScheduleRegistrationSerializerCreateTestCase(BluebottleTestCase):
    def setUp(self):
        site_settings = SitePlatformSettings.load()
        site_settings.share_activities = ['supplier', 'consumer']
        site_settings.save()

        initiative = InitiativeFactory.create()
        self.activity = ScheduleActivityFactory.create(
            team_activity='teams',
            initiative=initiative,
        )
        initiative.states.submit()
        initiative.states.approve(save=True)
        self.activity.states.publish(save=True)
        adapter.sync(self.activity)

        self.remote_user = RemoteMember.objects.create(
            first_name='Remote',
            last_name='Captain',
            email='captain@example.com',
        )
        self.serializer = TeamScheduleRegistrationSerializer()

    def test_create_uses_team_registration_effect(self):
        registration = self.serializer.create({
            'activity': self.activity,
            'remote_user': self.remote_user,
            'user': None,
            'answer': 'We want to help',
            'team': {
                'id': 'https://consumer.example/teams/1',
                'name': 'Harbor crew',
                'summary': 'Weekend shifts',
            },
        })

        self.assertEqual(registration.answer, 'We want to help')
        self.assertEqual(registration.remote_user_id, self.remote_user.id)
        team = registration.teams.get()
        self.assertEqual(team.name, 'Harbor crew')
        self.assertEqual(team.description, 'Weekend shifts')
        self.assertEqual(team.remote_user_id, self.remote_user.id)
        self.assertEqual(team.team_members.count(), 1)

    def test_create_adopts_existing_activity_pub_team(self):
        ap_team = ActivityPubTeam.objects.create(
            iri='https://consumer.example/teams/unadopted',
        )
        registration = self.serializer.create({
            'activity': self.activity,
            'remote_user': self.remote_user,
            'user': None,
            'team': ap_team.iri,
        })
        ap_team.refresh_from_db()
        self.assertEqual(ap_team.adopted_id, registration.teams.get().id)
        self.assertEqual(ap_team.attributed_to_id, self.activity.activity_pub_model.id)

    def test_create_rejoins_withdrawn_team(self):
        registration = self.serializer.create({
            'activity': self.activity,
            'remote_user': self.remote_user,
            'user': None,
        })
        team = registration.teams.get()
        team.states.withdraw(save=True)
        team.refresh_from_db()
        registration.refresh_from_db()
        self.assertEqual(team.status, 'withdrawn')
        self.assertEqual(registration.status, 'withdrawn')

        result = self.serializer.create({
            'activity': self.activity,
            'remote_user': self.remote_user,
            'user': None,
        })
        team.refresh_from_db()
        result.refresh_from_db()
        self.assertEqual(result.pk, registration.pk)
        self.assertEqual(team.status, 'accepted')
        self.assertEqual(result.status, 'accepted')
