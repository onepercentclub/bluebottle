from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.tasks import TaskFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.donations import DonationFactory

from bluebottle.utils.model_dispatcher import get_task_model
TASK_MODEL = get_task_model()

@override_settings(SEND_WELCOME_MAIL=False)
class TestDeadlineStatus(BluebottleTestCase):
    """
    Test the handling of projects passing their deadlines
    """

    def pay(self, project, amount):
        order = OrderFactory.create()
        DonationFactory.create(project=project, order=order, amount=amount)
        order.locked()
        order.succeeded()
        order.save()

        return order

    def setUp(self):
        super(TestDeadlineStatus, self).setUp()

        self.init_projects()
        self.status_running = ProjectPhase.objects.get(slug='campaign')
        self.complete = ProjectPhase.objects.get(slug='done-complete')
        self.incomplete = ProjectPhase.objects.get(slug='done-incomplete')
        self.project = ProjectFactory.create(status=self.status_running)

    def test_funding_reached(self):
        """ More funded than asked  means complete """
        self.project.amount_asked = 90

        self.pay(self.project, 100)

        self.project.save()

        self.project.deadline_reached()

        self.assertEquals(self.project.status, self.complete)

    def test_funding_notreached(self):
        """ less funded than asked means incomplete """
        self.project.amount_asked = 100

        self.pay(self.project, 90)

        self.project.save()

        self.project.deadline_reached()

        self.assertEquals(self.project.status, self.incomplete)

    def test_sourcing_tasks_complete(self):
        """ one remaining open task """
        self.project.amount_asked = 0 # makes it sourcing
        TaskFactory.create(project=self.project,
                           status=TASK_MODEL.TaskStatuses.realized)
        self.project.deadline_reached()

        self.assertEquals(self.project.status, self.complete)


    def test_sourcing_tasks_incomplete_open(self):
        """ on remaining in progress task """
        self.project.amount_asked = 0 # makes it sourcing
        TaskFactory.create(project=self.project,
                           status=TASK_MODEL.TaskStatuses.open)
        self.project.deadline_reached()

        self.assertEquals(self.project.status, self.incomplete)

    def test_sourcing_tasks_incomplete_in_progress(self):
        self.project.amount_asked = 0 # makes it sourcing
        TaskFactory.create(project=self.project,
                           status=TASK_MODEL.TaskStatuses.in_progress)
        self.project.deadline_reached()

        self.assertEquals(self.project.status, self.incomplete)

    def test_sourcing_tasks_incomplete_mix(self):
        """ A mix of realized, open, in progress tasks """
        self.project.amount_asked = 0 # makes it sourcing
        TaskFactory.create(project=self.project,
                           status=TASK_MODEL.TaskStatuses.realized)
        TaskFactory.create(project=self.project,
                           status=TASK_MODEL.TaskStatuses.open)
        TaskFactory.create(project=self.project,
                           status=TASK_MODEL.TaskStatuses.in_progress)
        self.project.deadline_reached()

        self.assertEquals(self.project.status, self.incomplete)

    def test_funding_tasks_incomplete(self):
        """ a funding project with incomplete tasks is still complete """
        self.project.amount_asked = 100
        self.pay(self.project, 100)
        self.project.save()

        TaskFactory.create(project=self.project, status=TASK_MODEL.TaskStatuses.open)
        self.project.deadline_reached()

        self.assertEquals(self.project.status, self.complete)

