from django.core.urlresolvers import reverse

from bluebottle.utils.utils import StatusDefinition

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.test.factory_models.orders import OrderFactory

from bluebottle.statistics.models import Statistic
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.tasks.models import Task


class HomepageEndpointTestCase(BluebottleTestCase):
    """
    Integration tests for the Statistics API.
    """
    def setUp(self):
        super(HomepageEndpointTestCase, self).setUp()
        self.init_projects()

        self.stats = Statistic.objects.create()

        """
        Create 10 Project instances for one user with half in the campaign phase
        and the other half in the done-complete phase
        This will create:
            - 10 running or realised projects
            - 10 campaigners (eg 10 new people involved)
        """
        self.user1 = BlueBottleUserFactory.create()
        self.campaign_phase = ProjectPhase.objects.get(slug='campaign')
        self.plan_phase = ProjectPhase.objects.get(slug='done-complete')
        projects = []

        for char in 'abcdefghij':
            # Put half of the projects in the campaign phase.
            if ord(char) % 2 == 1:
                project = ProjectFactory.create(title=char * 3, slug=char * 3, status=self.campaign_phase)
            else:
                project = ProjectFactory.create(title=char * 3, slug=char * 3, status=self.plan_phase)

            projects.append(project)

        """
        Create 10 TaskMember instances for one project.
        This will create:
            - 1 realised task
            - 1 task owner (eg 1 new person involved)
            - 10 task members (eg 10 new people involved)
        """
        self.task = TaskFactory.create(project=projects[0], status=Task.TaskStatuses.realized)
        for char in 'abcdefghij':
            # Put half of the projects in the campaign phase.
            if ord(char) % 2 == 1:
                task = TaskMemberFactory.create(task=self.task)
            else:
                task = TaskMemberFactory.create(task=self.task)

        """
        Create 10 Donations with half to fundraisers
        This will create:
            - 10 donations of 1000 (total amount of 10000)
            - 10 donators (eg 10 new people involved)
            - 5 fundraisers (eg 5 new people involved)
        """
        for char in 'abcdefghij':
            if ord(char) % 2 == 1:
                self.order = OrderFactory.create(status=StatusDefinition.SUCCESS)
                self.donation = DonationFactory.create(amount=1000, order=self.order, fundraiser=None)
            else:
                self.order = OrderFactory.create(status=StatusDefinition.SUCCESS)
                self.donation = DonationFactory.create(amount=1000, order=self.order)

    def test_homepage_stats(self):
        response = self.client.get(reverse('stats'))
        
        self.assertEqual(response.data['donated'], Decimal('10000.00'))
        self.assertEqual(response.data['projects_online'], 5)
        self.assertEqual(response.data['projects_realized'], 5)
        self.assertEqual(response.data['tasks_realized'], 1)
        self.assertEqual(response.data['people_involved'], 36)
