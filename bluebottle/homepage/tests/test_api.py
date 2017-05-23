from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.statistics.views import Statistics
from bluebottle.tasks.models import Task
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.statistics import StatisticFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import StatusDefinition
from bluebottle.utils.models import Language

from ..models import HomePage


class HomepagePreviewProjectsTestCase(BluebottleTestCase):
    def setUp(self):
        super(HomepagePreviewProjectsTestCase, self).setUp()
        self.init_projects()

        self.user1 = BlueBottleUserFactory.create()

        self.phases = {}
        for phase in ('plan-new', 'plan-submitted', 'plan-needs-work',
                      'campaign', 'done-complete', 'done-incomplete',
                      'closed'):
            self.phases[phase] = ProjectPhase.objects.get(slug=phase)

        self.en = Language.objects.get(code='en')

    def test_plan_new(self):
        """ plan_new shouldn't be visible """
        ProjectFactory.create(title="plan-new project", slug="plan-new",
                              is_campaign=True,
                              language=self.en,
                              status=self.phases['plan-new'])
        self.assertEquals(len(HomePage().get('en').projects), 0)

    def test_plan_submitted(self):
        """ plan_submitted shouldn't be visible """
        ProjectFactory.create(title="plan-submitted project",
                              is_campaign=True,
                              slug="plan-submitted",
                              language=self.en,
                              status=self.phases['plan-submitted'])
        self.assertEquals(len(HomePage().get('en').projects), 0)

    def test_plan_needs_work(self):
        """ plan_needs_work shouldn't be visible """
        ProjectFactory.create(title="plan-needs-work project",
                              is_campaign=True,
                              slug="plan-needs-work",
                              language=self.en,
                              status=self.phases['plan-needs-work'])
        self.assertEquals(len(HomePage().get('en').projects), 0)

    def test_closed(self):
        """ done_incomplete shouldn't be visible """
        ProjectFactory.create(title="closed project",
                              is_campaign=True,
                              slug="closed",
                              language=self.en,
                              status=self.phases['closed'])
        self.assertEquals(len(HomePage().get('en').projects), 0)

    def test_campaign(self):
        """ plan_new should be visible """
        p = ProjectFactory.create(title="campaign project",
                                  is_campaign=True,
                                  slug="campaign",
                                  language=self.en,
                                  status=self.phases['campaign'])
        self.assertEquals(HomePage().get('en').projects, [p])

    def test_done_complete(self):
        """ done-complete should be visible """
        p = ProjectFactory.create(title="done-complete project",
                                  is_campaign=True,
                                  slug="done-complete",
                                  language=self.en,
                                  status=self.phases['done-complete'])
        self.assertEquals(HomePage().get('en').projects, [p])

    def test_done_incomplete(self):
        """ done_incomplete should be visible """
        p = ProjectFactory.create(title="done-incomplete project",
                                  is_campaign=True,
                                  slug="done-incomplete",
                                  language=self.en,
                                  status=self.phases['done-incomplete'])
        self.assertEquals(HomePage().get('en').projects, [p])

    def test_not_campaign(self):
        """ if it's not a campaign, don't show """
        ProjectFactory.create(title="done-complete project",
                              is_campaign=False,
                              slug="done-complete",
                              language=self.en,
                              status=self.phases['done-complete'])
        self.assertEquals(len(HomePage().get('en').projects), 0)


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
)
class HomepageEndpointTestCase(BluebottleTestCase):
    """
    Integration tests for the Statistics API.
    """

    def setUp(self):
        super(HomepageEndpointTestCase, self).setUp()
        self.init_projects()

        self.stats = Statistics()

        """
        Create 10 Project instances for one user with half in the campaign phase
        and the other half in the done-complete phase
        This will create:
            - 10 running or realised projects
            - 10 campaigners (eg 10 new people involved)
        """
        self.user1 = BlueBottleUserFactory.create()
        self.campaign_phase = ProjectPhase.objects.get(slug='campaign', viewable=True)
        self.plan_phase = ProjectPhase.objects.get(slug='done-complete')
        self.en = Language.objects.get(code='en')
        projects = []

        for char in 'abcdefghij':
            # Put half of the projects in the campaign phase.
            if ord(char) % 2 == 1:
                project = ProjectFactory.create(title=char * 3, slug=char * 3,
                                                status=self.campaign_phase,
                                                language=self.en,
                                                is_campaign=True)
            else:
                project = ProjectFactory.create(title=char * 3, slug=char * 3,
                                                status=self.plan_phase,
                                                language=self.en)

            projects.append(project)

        """
        Create 10 TaskMember instances for one project.
        This will create:
            - 1 realised task
            - 1 task owner (eg 1 new person involved)
            - 10 task members (eg 10 new people involved)
        """
        self.task = TaskFactory.create(project=projects[0],
                                       status=Task.TaskStatuses.realized)
        for char in 'abcdefghij':
            # Put half of the projects in the campaign phase.
            if ord(char) % 2 == 1:
                TaskMemberFactory.create(task=self.task)
            else:
                TaskMemberFactory.create(task=self.task)

        """
        Create 10 Donations with half to fundraisers
        This will create:
            - 10 donations of 1000 (total amount of 10000)
            - 10 donators (eg 10 new people involved)
            - 5 fundraisers (eg 5 new people involved)
        """
        for char in 'abcdefghij':
            if ord(char) % 2 == 1:
                self.order = OrderFactory.create(
                    status=StatusDefinition.SUCCESS)
                self.donation = DonationFactory.create(amount=1000,
                                                       order=self.order,
                                                       fundraiser=None)
            else:
                self.order = OrderFactory.create(
                    status=StatusDefinition.SUCCESS)
                self.donation = DonationFactory.create(amount=1000,
                                                       order=self.order)

        StatisticFactory.create(type='donated_total', title='Donated', language='en')
        StatisticFactory.create(type='projects_online', title='Projects online', language='en')
        StatisticFactory.create(type='projects_realized', title='Projects realised', language='en')
        StatisticFactory.create(type='tasks_realized', title='Tasks realised', language='en')
        StatisticFactory.create(type='people_involved', title='Peeps', language='en')
        StatisticFactory.create(type='manual', title='Rating', value='9.3', language='en')

    def test_homepage_stats(self):
        response = self.client.get(reverse('stats', kwargs={'language': 'en'}))

        self.assertEqual(len(response.data['projects']), 4)

        impact = response.data['statistics']
        self.assertEqual(impact[0]['title'], 'Donated')
        self.assertEqual(impact[0]['value'], u'10000')
        self.assertEqual(impact[1]['title'], 'Projects online')
        self.assertEqual(impact[1]['value'], u'5')
        self.assertEqual(impact[2]['title'], 'Projects realised')
        self.assertEqual(impact[2]['value'], u'5')
        self.assertEqual(impact[3]['title'], 'Tasks realised')
        self.assertEqual(impact[3]['value'], u'1')
        self.assertEqual(impact[4]['title'], 'Peeps')
        self.assertEqual(impact[4]['value'], u'36')

        self.assertEqual(impact[5]['title'], 'Rating')
        self.assertEqual(impact[5]['value'], '9.3')
