from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient
from bluebottle.time_based.tests.factories import DateActivityFactory
from bluebottle.time_based.tests.steps import api_user_joins_activity, assert_participant_status, \
    api_participant_transition, assert_status


class DateParticipantScenarioTestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        self.owner = BlueBottleUserFactory.create()
        self.supporter = BlueBottleUserFactory.create()
        self.activity = DateActivityFactory.create(status='open', owner=self.owner)
        self.client = JSONAPITestClient()

    def test_scenario_user_joins_activity(self):
        api_user_joins_activity(self, activity=self.activity, supporter=self.supporter)
        assert_participant_status(self, activity=self.activity, supporter=self.supporter, status='accepted')

    def test_scenario_user_joins_review_activity_accepted(self):
        self.activity.review = True
        self.activity.save()
        api_user_joins_activity(self, activity=self.activity, supporter=self.supporter)
        assert_participant_status(self, activity=self.activity, supporter=self.supporter, status='new')
        api_participant_transition(self, activity=self.activity, supporter=self.supporter,
                                   transition='accept', request_user=self.owner)
        assert_participant_status(self, activity=self.activity, supporter=self.supporter, status='accepted')

    def test_scenario_user_withdraws_from_activity(self):
        api_user_joins_activity(self, activity=self.activity, supporter=self.supporter)
        assert_participant_status(self, activity=self.activity, supporter=self.supporter, status='accepted')
        api_participant_transition(self, activity=self.activity, supporter=self.supporter, transition='withdraw')
        assert_participant_status(self, activity=self.activity, supporter=self.supporter, status='withdrawn')
        api_participant_transition(self, activity=self.activity, supporter=self.supporter, transition='reapply')
        assert_participant_status(self, activity=self.activity, supporter=self.supporter, status='accepted')

    def test_scenario_user_withdraws_from_review_activity(self):
        self.activity.review = True
        self.activity.save()
        api_user_joins_activity(self, activity=self.activity, supporter=self.supporter)
        assert_participant_status(self, activity=self.activity, supporter=self.supporter, status='new')
        api_participant_transition(self, activity=self.activity, supporter=self.supporter, transition='withdraw')
        assert_participant_status(self, activity=self.activity, supporter=self.supporter, status='withdrawn')
        api_participant_transition(self, activity=self.activity, supporter=self.supporter, transition='reapply')
        assert_participant_status(self, activity=self.activity, supporter=self.supporter, status='new')

    def test_scenario_user_fills_activity(self):
        self.activity.capacity = 1
        self.activity.save()
        api_user_joins_activity(self, activity=self.activity, supporter=self.supporter)
        assert_participant_status(self, activity=self.activity, supporter=self.supporter, status='accepted')
        assert_status(self, model=self.activity, status='full')
        api_participant_transition(self, activity=self.activity, supporter=self.supporter, transition='withdraw')
        assert_participant_status(self, activity=self.activity, supporter=self.supporter, status='withdrawn')
        assert_status(self, model=self.activity, status='open')
