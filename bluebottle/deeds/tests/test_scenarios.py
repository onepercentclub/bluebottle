from datetime import date, timedelta

from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.deeds.tests.steps import api_create_deed, api_update_deed, api_deed_transition, api_read_deed
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.initiatives.tests.steps import api_read_initiative
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import JSONAPITestClient, BluebottleAdminTestCase
from bluebottle.time_based.tests.steps import assert_status


class DateActivityScenarioTestCase(BluebottleAdminTestCase):

    def setUp(self):
        super().setUp()
        self.owner = BlueBottleUserFactory.create()
        self.supporter = BlueBottleUserFactory.create()
        self.initiative = InitiativeFactory.create(owner=self.owner, status='approved')
        self.client = JSONAPITestClient()
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.activity_types = ['deed', 'funding', 'dateactivity', 'periodactivity']
        initiative_settings.save()

    def test_deeds_disabled(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.activity_types = ['funding', 'dateactivity', 'periodactivity']
        initiative_settings.save()
        activity_data = {
            'title': 'Movember',
            'end': str(date.today() + timedelta(days=10)),
        }
        api_create_deed(self, self.initiative, activity_data, status_code=403)

    def test_create_deed(self):
        activity_data = {
            'title': 'Movember',
            'end': str(date.today() + timedelta(days=10)),
        }
        activity = api_create_deed(self, self.initiative, activity_data)

        activity_data = {
            'title': 'Movember',
            'start': str(date.today()),
            'description': 'Show some stash!'
        }
        activity = api_update_deed(self, activity, activity_data)
        api_deed_transition(self, activity, 'publish')
        assert_status(self, activity, 'open')

    def test_view_intiative_with_draft_deed(self):
        DeedFactory.create(initiative=self.initiative, owner=self.owner, status='draft')
        api_read_initiative(self, self.initiative, request_user=self.owner)

    def test_view_deed(self):
        deed = DeedFactory.create(initiative=self.initiative, status='open')
        api_read_deed(self, deed, request_user=self.supporter)
