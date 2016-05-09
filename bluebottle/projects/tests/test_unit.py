from datetime import timedelta, time
from django.utils import timezone

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.utils.model_dispatcher import get_project_model
from bluebottle.test.factory_models.projects import (ProjectFactory, ProjectPhaseFactory)
from bluebottle.utils.utils import StatusDefinition
from bluebottle.projects.models import (Project, ProjectPhaseLog)
from bluebottle.donations.models import Donation
from bluebottle.orders.models import Order
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.votes import VoteFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
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

        some_days_ago = now - timezone.timedelta(days=15)
        self.expired_project = ProjectFactory.create(
            amount_asked=5000, campaign_started=some_days_ago,
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


class TestProjectPhaseLog(BluebottleTestCase):
    def setUp(self):
        super(TestProjectPhaseLog, self).setUp()
        self.init_projects()

    def test_create_phase_log(self):
        phase1 = ProjectPhaseFactory.create()
        phase2 = ProjectPhaseFactory.create()

        project = ProjectFactory.create(status=phase1)

        phase_logs = ProjectPhaseLog.objects.all()
        self.assertEquals(len(phase_logs), 1)
        self.assertEquals(phase_logs[0].status, project.status)

        project.status = phase2
        project.save()

        phase_logs = ProjectPhaseLog.objects.all().order_by("-start")
        self.assertEquals(len(phase_logs), 2)
        self.assertEquals(phase_logs[0].status, project.status)


class SupporterCountTest(BluebottleTestCase):
    def setUp(self):
        super(SupporterCountTest, self).setUp()

        # Required by Project model save method
        self.init_projects()

        self.some_project = ProjectFactory.create(amount_asked=5000)
        self.another_project = ProjectFactory.create(amount_asked=5000)

        self.some_user = BlueBottleUserFactory.create()
        self.another_user = BlueBottleUserFactory.create()

    def test_supporter_count_new(self):
        self.assertEqual(self.some_project.supporter_count(), 0)

        self._create_donation(user=self.some_user, status=StatusDefinition.NEW)

        self.assertEqual(self.some_project.supporter_count(), 0)

    def test_supporter_count_success(self):
        self._create_donation(user=self.some_user,
                              status=StatusDefinition.SUCCESS)

        self.assertEqual(self.some_project.supporter_count(), 1)

    def test_supporter_count_pending(self):
        self._create_donation(user=self.some_user,
                              status=StatusDefinition.PENDING)

        self.assertEqual(self.some_project.supporter_count(), 1)

    def test_supporter_count_unique(self):
        self._create_donation(user=self.some_user,
                              status=StatusDefinition.SUCCESS)
        self._create_donation(user=self.some_user,
                              status=StatusDefinition.SUCCESS)

        self.assertEqual(self.some_project.supporter_count(), 1)

        self._create_donation(user=self.another_user,
                              status=StatusDefinition.SUCCESS)

        self.assertEqual(self.some_project.supporter_count(), 2)

    def test_supporter_count_anonymous(self):
        self._create_donation(status=StatusDefinition.SUCCESS)
        self.assertEqual(self.some_project.supporter_count(), 1)

    def test_supporter_count_anonymous_not_unique(self):
        self._create_donation(status=StatusDefinition.SUCCESS)
        self._create_donation(status=StatusDefinition.SUCCESS)
        self.assertEqual(self.some_project.supporter_count(), 2)

    def test_supporter_count_anonymous_and_user(self):
        self._create_donation(user=self.some_user,
                              status=StatusDefinition.SUCCESS)
        self._create_donation(user=self.some_user,
                              status=StatusDefinition.SUCCESS)

        self._create_donation(user=self.another_user,
                              status=StatusDefinition.SUCCESS)

        self._create_donation(status=StatusDefinition.SUCCESS)
        self._create_donation(status=StatusDefinition.SUCCESS)
        self.assertEqual(self.some_project.supporter_count(), 4)

    def _create_donation(self, user=None, status=StatusDefinition.NEW):
        """ Helper method for creating donations."""
        order = Order.objects.create(status=status, user=user)
        donation = Donation.objects.create(amount=100,
                                           project=self.some_project,
                                           order=order)

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


class TestProjectPopularity(BluebottleTestCase):
    def setUp(self):
        super(TestProjectPopularity, self).setUp()
        self.init_projects()

        self.project = ProjectFactory.create()

        VoteFactory.create(project=self.project)
        task = TaskFactory.create(project=self.project)
        TaskMemberFactory.create(task=task)

        order = OrderFactory.create(status=StatusDefinition.SUCCESS)

        DonationFactory(order=order, project=self.project)

    def test_update_popularity(self):
        Project.update_popularity()

        self.assertEqual(Project.objects.get(id=self.project.id).popularity, 11)
