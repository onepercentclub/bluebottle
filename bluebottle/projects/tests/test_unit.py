from datetime import timedelta, time
from decimal import Decimal
from django.utils import timezone

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.utils.model_dispatcher import get_project_model

from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.utils.utils import StatusDefinition
from bluebottle.donations.models import Donation
from bluebottle.orders.models import Order
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.suggestions import SuggestionFactory
from bluebottle.suggestions.models import Suggestion

PROJECT_MODEL = get_project_model()


class TestProjectStatusUpdate(BluebottleTestCase):
    """
        save() automatically updates some fields, specifically
        the status field. Make sure it picks the right one
    """
    def setUp(self):
        super(TestProjectStatusUpdate, self).setUp()

        self.init_projects()

        now = timezone.now()

        self.incomplete = ProjectPhase.objects.get(slug="done-incomplete")
        self.complete = ProjectPhase.objects.get(slug="done-complete")
        self.campaign = ProjectPhase.objects.get(slug="campaign")

        self.expired_project = ProjectFactory.create(amount_asked=5000,
                                                     campaign_started=now -
                                                     timezone.
                                                     timedelta(days=15),
                                                     status=self.campaign)

        self.expired_project.deadline = timezone.now() - timedelta(days=1)

    def test_deadline_end_of_day(self):
        self.expired_project.save()

        self.assertTrue(
            self.expired_project.deadline.time() == time(23, 59, 59),
            'Project deadlines are always at the end of the day'
        )

    def test_expired_too_little(self):
        """ Not enough donated - status done incomplete """
        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=self.expired_project,
            order=order,
            amount=4999
        )
        donation.save()

        order.locked()
        order.succeeded()
        order.save()

        self.expired_project.save()
        self.failUnless(self.expired_project.status == self.incomplete)

    def test_expired_exact(self):
        """ Exactly the amount requested - status done complete """
        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=self.expired_project,
            order=order,
            amount=5000
        )
        donation.save()

        order.locked()
        order.succeeded()
        order.save()

        self.expired_project.save()
        self.failUnless(self.expired_project.status == self.complete)

    def test_expired_more_than_enough(self):
        """ More donated than requested - status done complete """
        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=self.expired_project,
            order=order,
            amount=5001
        )
        donation.save()

        order.locked()
        order.succeeded()
        order.save()
        self.expired_project.save()
        self.failUnless(self.expired_project.status == self.complete)


class CalculateProjectMoneyDonatedTest(BluebottleTestCase):

    def setUp(self):
        super(CalculateProjectMoneyDonatedTest, self).setUp()

        # Required by Project model save method
        self.init_projects()

        self.some_project = ProjectFactory.create(amount_asked=5000)
        self.another_project = ProjectFactory.create(amount_asked=5000)

        self.some_user = BlueBottleUserFactory.create()
        self.another_user = BlueBottleUserFactory.create()

    # def test_donated_amount(self):
    #     # Some project have amount_asked of 5000000 (cents that is)
    #     self.assertEqual(self.some_project.amount_asked, 5000)
    #
    #     # A project without donations should have amount_donated of 0
    #     self.assertEqual(self.some_project.amount_donated, 0)
    #
    #     # Create a new donation of 15 in status 'new'. project money donated should be 0
    #     first_donation = self._create_donation(user=self.some_user, project=self.some_project, amount=1500,
    #                                            status=DonationStatuses.new)
    #     self.assertEqual(self.some_project.amount_donated, 0)
    #
    #
    #     # Create a new donation of 25 in status 'in_progress'. project money donated should be 0.
    #     second_donation = self._create_donation(user=self.some_user, project=self.some_project, amount=2500,
    #                                             status=DonationStatuses.in_progress)
    #     self.assertEqual(self.some_project.amount_donated, 0)
    #
    #     # Setting the first donation to status 'paid' money donated should be 1500
    #     first_donation.order.status = StatusDefinition.PENDING
    #     first_donation.order.save()
    #     self.assertEqual(self.some_project.amount_donated, 15)
    #
    #     # Setting the second donation to status 'pending' money donated should be 40
    #     second_donation.order.status = StatusDefinition.PENDING
    #     second_donation.order.save()
    #     self.assertEqual(self.some_project.amount_donated, 40)

    def _create_donation(self, user=None, amount=None, project=None,
                         status=StatusDefinition.NEW):
        """ Helper method for creating donations."""
        if not project:
            project = ProjectFactory.create()
            project.save()

        if not user:
            user = BlueBottleUserFactory.create()

        if not amount:
            amount = Decimal('10.00')

        order = Order.objects.create(status=status)
        donation = Donation.objects.create(user=user, amount=amount,
                                           project=project, order=order)

        return donation


class TestProjectStatusChangeSuggestionUpdate(BluebottleTestCase):

    def setUp(self):
        super(TestProjectStatusChangeSuggestionUpdate, self).setUp()

        self.init_projects()

        self.new = ProjectPhase.objects.get(slug="plan-new")
        self.needs_work = ProjectPhase.objects.get(slug="plan-needs-work")
        self.submitted = ProjectPhase.objects.get(slug="plan-submitted")

    def test_project_submitted_suggestion_submitted(self):
        """
        Test that suggestion has status submitted if a project status
        changes to submitted
        """
        project = ProjectFactory.create(status=self.new)
        suggestion = SuggestionFactory.create(project=project,
                                              token='xxx',
                                              status='in_progress')

        project.status = self.submitted
        project.save()

        suggestion = Suggestion.objects.get(project=project)

        self.assertEquals(suggestion.status, 'submitted')

    def test_project_needs_work_suggestion_in_progress(self):
        """
        Test that suggestion has status in-progress if a project status
        changes to needs-work
        """
        project = ProjectFactory.create(status=self.submitted)
        suggestion = SuggestionFactory.create(project=project,
                                              token='xxx',
                                              status='submitted')

        project.status = self.needs_work
        project.save()

        suggestion = Suggestion.objects.get(project=project)

        self.assertEquals(suggestion.status, 'in_progress')
