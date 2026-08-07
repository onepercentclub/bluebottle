from django.test import RequestFactory
from rest_framework.exceptions import ValidationError

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import (
    Create, Recipient, Team as ActivityPubTeam,
)
from bluebottle.activity_pub.serializers.federated_activities import (
    TeamMemberAddSerializer, TeamScheduleSlotsSerializer,
)
from bluebottle.activity_pub.tests.factories import OrganizationFactory, PersonFactory
from bluebottle.cms.models import SitePlatformSettings
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import ScheduleActivityFactory, TeamFactory


class TeamMemberAddAuthorizationTestCase(BluebottleTestCase):
    def setUp(self):
        site_settings = SitePlatformSettings.load()
        site_settings.share_activities = ['supplier', 'consumer']
        site_settings.save()

        self.platform = OrganizationFactory.create()
        self.other_platform = OrganizationFactory.create()
        self.activity = ScheduleActivityFactory.create(team_activity='teams')
        adapter.sync(self.activity)
        self.team = TeamFactory.create(activity=self.activity)
        self.event = self.activity.activity_pub_model
        self.ap_team = ActivityPubTeam.objects.create(
            iri=f'https://consumer.example/teams/{self.team.pk}',
            attributed_to=self.event,
            adopted=self.team,
        )
        create = self.event.create_set.first()
        if create is None:
            create = Create.objects.create(
                object=self.event,
                actor=OrganizationFactory.create(),
            )
        Recipient.objects.get_or_create(activity=create, actor=self.platform)

        self.person = PersonFactory.create(
            iri='https://consumer.example/people/1',
            given_name='Ada',
            family_name='Lovelace',
            email='ada@example.com',
            source=self.platform,
        )
        self.other_person = PersonFactory.create(
            iri='https://consumer.example/people/2',
            given_name='Grace',
            family_name='Hopper',
            email='grace@example.com',
            source=self.platform,
        )

    def _person_data(self, person):
        return {
            'id': person.iri,
            'type': 'Person',
            'given_name': person.given_name,
            'family_name': person.family_name,
            'email': person.email,
        }

    def _serializer(self, data, platform=None):
        request = RequestFactory().post('/')
        request.auth = platform or self.platform
        serializer = TeamMemberAddSerializer(context={'request': request})
        serializer.initial_data = data
        return serializer

    def test_object_must_match_actor(self):
        serializer = self._serializer({
            'type': 'Add',
            'actor': self._person_data(self.person),
            'object': self._person_data(self.other_person),
            'target': {'id': self.ap_team.iri},
        })
        with self.assertRaises(ValidationError) as error:
            serializer.create({})
        self.assertIn('object', error.exception.detail)

    def test_unauthorized_platform_rejected(self):
        serializer = self._serializer(
            {
                'type': 'Add',
                'actor': self._person_data(self.person),
                'object': self._person_data(self.person),
                'target': {'id': self.ap_team.iri},
            },
            platform=self.other_platform,
        )
        with self.assertRaises(ValidationError) as error:
            serializer.create({})
        self.assertIn('target', error.exception.detail)

    def test_authorized_add_succeeds(self):
        serializer = self._serializer({
            'type': 'Add',
            'actor': self._person_data(self.person),
            'object': self._person_data(self.person),
            'target': {'id': self.ap_team.iri},
        })
        member = serializer.create({})
        self.assertEqual(member.team, self.team)
        self.assertEqual(member.remote_user.origin.iri, self.person.iri)


class TeamScheduleSlotReuseTestCase(BluebottleTestCase):
    def setUp(self):
        self.activity = ScheduleActivityFactory.create(team_activity='teams')
        self.team_one = TeamFactory.create(activity=self.activity)
        self.team_two = TeamFactory.create(activity=self.activity)
        self.slot_one = self.team_one.slots.order_by('pk').first()
        self.slot_two = self.team_two.slots.order_by('pk').first()

    def test_missing_team_raises(self):
        serializer = TeamScheduleSlotsSerializer()
        with self.assertRaises(ValidationError) as error:
            serializer._team_slot_to_reuse({'activity': self.activity})
        self.assertIn('team', error.exception.detail)

    def test_reuses_only_requested_team_slot(self):
        self.assertIsNotNone(self.slot_one)
        self.assertIsNotNone(self.slot_two)
        self.assertNotEqual(self.slot_one.pk, self.slot_two.pk)

        serializer = TeamScheduleSlotsSerializer()
        validated = {'activity': self.activity, 'team': self.team_two}
        existing = serializer._team_slot_to_reuse(validated)
        self.assertEqual(existing, self.slot_two)
        self.assertEqual(validated['team'], self.team_two)

    def test_unknown_team_field_raises(self):
        serializer = TeamScheduleSlotsSerializer()
        field = serializer.fields['team']
        with self.assertRaises(ValidationError):
            field.to_internal_value('https://example.com/teams/missing')
