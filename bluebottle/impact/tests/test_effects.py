from bluebottle.test.utils import BluebottleTestCase
from bluebottle.deeds.tests.factories import EffortContributionFactory
from bluebottle.impact.tests.factories import ImpactGoalFactory


class CreateEffortContributionTestCase(BluebottleTestCase):
    def setUp(self):
        self.contribution = EffortContributionFactory.create()
        self.contribution.contributor.activity.initiative.states.submit(save=True)
        self.contribution.contributor.activity.states.submit(save=True)
        self.contribution.contributor.activity.initiative.states.approve(save=True)

        self.impact_goal = ImpactGoalFactory.create(
            activity=self.contribution.contributor.activity,
            target=100,
            realized=0,
            coupled_with_contributions=True
        )

    def test_status_new(self):
        self.assertEqual(self.impact_goal.realized, 0)

    def test_status_succeed(self):
        self.contribution.states.succeed(save=True)
        self.impact_goal.refresh_from_db()

        self.assertEqual(self.impact_goal.realized, 1)

    def test_status_succeed_not_coupled(self):
        self.impact_goal.coupled_with_contributions = False
        self.impact_goal.save()

        self.contribution.states.succeed(save=True)
        self.impact_goal.refresh_from_db()

        self.assertEqual(self.impact_goal.realized, 0)

    def test_status_fail(self):
        self.test_status_succeed()
        self.contribution.states.fail(save=True)
        self.impact_goal.refresh_from_db()

        self.assertEqual(self.impact_goal.realized, 0)
