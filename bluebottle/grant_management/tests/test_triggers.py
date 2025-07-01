from djmoney.money import Money

from bluebottle.activities.messages.activity_manager import (
    ActivityRejectedNotification, ActivitySubmittedNotification,
    ActivityApprovedNotification, ActivityNeedsWorkNotification
)
from bluebottle.activities.messages.reviewer import ActivitySubmittedReviewerNotification
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.files.tests.factories import ImageFactory
from bluebottle.grant_management.messages.activity_manager import GrantApplicationSubmittedMessage, \
    GrantApplicationApprovedMessage, GrantApplicationNeedsWorkMessage, GrantApplicationRejectedMessage, \
    GrantApplicationCancelledMessage
from bluebottle.grant_management.tests.factories import GrantApplicationFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import TriggerTestCase


class GrantApplicationTriggersTestCase(TriggerTestCase):
    factory = GrantApplicationFactory

    def setUp(self):
        self.owner = BlueBottleUserFactory.create()
        self.staff_user = BlueBottleUserFactory.create(
            is_staff=True,
            submitted_initiative_notifications=True
        )

        image = ImageFactory()

        self.defaults = {
            'initiative': InitiativeFactory.create(status='approved'),
            'owner': self.owner,
            'target': Money(1000, 'EUR'),
            'image': image,
        }
        super().setUp()

    def create(self):
        self.model = self.factory.create(**self.defaults)

    def test_submit(self):
        self.defaults['initiative'] = None
        self.create()
        self.model.states.submit()

        with self.execute():
            self.assertNotificationEffect(GrantApplicationSubmittedMessage)
            self.assertNoNotificationEffect(ActivitySubmittedReviewerNotification)
            self.assertNoNotificationEffect(ActivitySubmittedNotification)

    def test_approve(self):
        self.defaults['initiative'] = None
        self.create()
        self.model.states.submit(save=True)
        self.model.states.approve()

        with self.execute():
            self.assertNotificationEffect(GrantApplicationApprovedMessage)
            self.assertNoNotificationEffect(ActivityApprovedNotification)
            self.assertTransitionEffect(OrganizerStateMachine.succeed, self.model.organizer)

    def test_needs_work(self):
        self.defaults['initiative'] = None
        self.create()
        self.model.states.submit(save=True)
        self.model.states.request_changes()

        with self.execute():
            self.assertNotificationEffect(GrantApplicationNeedsWorkMessage)
            self.assertNoNotificationEffect(ActivityNeedsWorkNotification)

    def test_reject(self):
        self.create()
        self.model.states.submit(save=True)
        self.model.states.reject()

        with self.execute():
            self.assertNotificationEffect(GrantApplicationRejectedMessage)
            self.assertNoNotificationEffect(ActivityRejectedNotification)
            self.assertTransitionEffect(OrganizerStateMachine.fail, self.model.organizer)

    def test_cancel(self):
        self.create()
        self.model.states.submit(save=True)
        self.model.states.cancel()

        with self.execute():
            self.assertNotificationEffect(GrantApplicationCancelledMessage)
            self.assertNoNotificationEffect(ActivityRejectedNotification)
            self.assertTransitionEffect(OrganizerStateMachine.fail, self.model.organizer)
