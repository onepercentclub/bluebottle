from datetime import timedelta

import mock
from django.db import connection
from django.utils import timezone
from django.utils.timezone import now

from bluebottle.clients.utils import LocalTenant
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tasks import time_contribution_tasks
from bluebottle.time_based.tests.factories import (
    ScheduleActivityFactory,
    ScheduleRegistrationFactory,
    TeamFactory,
    TeamMemberFactory,
)


class UnscheduledContributionsTestCase(BluebottleTestCase):
    """
    BB-30016: contributions of participants that have not been scheduled yet
    must not be succeeded by the contribution-finished periodic task.
    """

    def setUp(self):
        super().setUp()
        self.initiative = InitiativeFactory.create(status="approved")

    def run_task(self, when):
        with mock.patch.object(timezone, "now", return_value=when):
            time_contribution_tasks()
        with LocalTenant(connection.tenant, clear_tenant=True):
            pass

    def create_activity(self, team_activity):
        activity = ScheduleActivityFactory.create(
            initiative=self.initiative,
            team_activity=team_activity,
            review=False,
            registration_deadline=None,
            duration=timedelta(hours=4),
            deadline=(now() + timedelta(days=30)).date(),
        )
        activity.states.publish(save=True)
        return activity

    def test_unscheduled_team_member_stays_new(self):
        activity = self.create_activity("teams")
        team = TeamFactory.create(activity=activity)
        self.assertIsNone(team.slots.first().start)

        participant = TeamMemberFactory.create(team=team).participants.first()
        contribution = participant.contributions.filter(
            timecontribution__contribution_type="period"
        ).first()

        self.assertEqual(participant.status, "accepted")
        self.assertEqual(contribution.status, "new")

        self.run_task(now() + timedelta(days=1))

        participant.refresh_from_db()
        contribution.refresh_from_db()
        self.assertEqual(participant.status, "accepted")
        self.assertEqual(contribution.status, "new")

    def test_unscheduled_individual_stays_new(self):
        activity = self.create_activity("individuals")
        user = BlueBottleUserFactory.create()
        registration = ScheduleRegistrationFactory.create(
            activity=activity, user=user, as_user=user
        )
        participant = registration.participants.first()
        participant.save()
        participant.refresh_from_db()

        contribution = participant.contributions.filter(
            timecontribution__contribution_type="period"
        ).first()

        self.assertEqual(participant.status, "accepted")
        self.assertEqual(contribution.status, "new")

        self.run_task(now() + timedelta(days=1))

        participant.refresh_from_db()
        contribution.refresh_from_db()
        self.assertEqual(participant.status, "accepted")
        self.assertEqual(contribution.status, "new")

    def test_team_scheduled_in_future_stays_new(self):
        activity = self.create_activity("teams")
        team = TeamFactory.create(activity=activity)

        participant = TeamMemberFactory.create(team=team).participants.first()

        slot = team.slots.first()
        slot.start = now() + timedelta(days=10)
        slot.duration = timedelta(hours=4)
        slot.save()

        participant.refresh_from_db()
        contribution = participant.contributions.filter(
            timecontribution__contribution_type="period"
        ).first()
        contribution.refresh_from_db()

        self.assertEqual(participant.status, "scheduled")
        self.assertGreater(contribution.end, now())

        self.run_task(now() + timedelta(days=1))

        contribution.refresh_from_db()
        self.assertEqual(contribution.status, "new")

    def test_scheduled_slot_in_the_past_still_succeeds(self):
        """The fix must not stop genuinely finished participants succeeding."""
        activity = self.create_activity("teams")
        team = TeamFactory.create(activity=activity)
        participant = TeamMemberFactory.create(team=team).participants.first()

        slot = team.slots.first()
        slot.start = now() - timedelta(days=2)
        slot.duration = timedelta(hours=4)
        slot.save()

        participant.refresh_from_db()
        contribution = participant.contributions.filter(
            timecontribution__contribution_type="period"
        ).first()
        contribution.refresh_from_db()

        self.assertEqual(participant.status, "succeeded")
        self.assertEqual(contribution.status, "succeeded")
