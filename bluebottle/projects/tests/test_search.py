from datetime import datetime, timedelta

from django.test.utils import override_settings
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.utils.timezone import get_current_timezone, now

from django_elasticsearch_dsl.test import ESTestCase
from django_elasticsearch_dsl.registries import registry

from bluebottle.test.factory_models.categories import CategoryFactory
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectThemeFactory
from bluebottle.test.factory_models.geo import LocationFactory, CountryFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory, SkillFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.votes import VoteFactory

from bluebottle.test.utils import BluebottleTestCase

from bluebottle.bb_projects.views import ProjectPreviewList
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.projects.models import Project


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
class ProjectSearchTest(ESTestCase, BluebottleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = ProjectPreviewList().as_view()

        for index in registry.get_indices([Project]):
            index.create()

    def search(self, query=None):
        url = reverse('project_preview_list')

        request = self.factory.get(url, query)
        return self.view(request)

    def test_no_filter(self):
        project = ProjectFactory.create()

        result = self.search()
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_location_filter(self):
        location = LocationFactory.create()
        project = ProjectFactory.create(location=location)
        ProjectFactory.create()

        result = self.search({'location': location.id})
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_country_filter(self):
        country = CountryFactory.create()
        project = ProjectFactory.create(country=country)
        ProjectFactory.create()

        result = self.search({'country': country.id})
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_status_filter(self):
        campaign = ProjectPhase.objects.get(slug='campaign')
        voting = ProjectPhase.objects.get(slug='voting')
        project = ProjectFactory.create(status=campaign)
        voting_project = ProjectFactory.create(status=voting)

        result = self.search({'status[]': [campaign.slug]})
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], project.title)

        result = self.search({'status[]': [voting.slug]})
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], voting_project.title)

        result = self.search({'status[]': [voting.slug, campaign.slug]})
        self.assertEqual(result.data['count'], 2)

    def test_type_sourcing_filter(self):
        project = ProjectFactory.create()
        TaskFactory.create(project=project)
        ProjectFactory.create()

        result = self.search({'project_type': 'volunteering'})
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_type_funding_filter(self):
        project = ProjectFactory.create(amount_asked=100)
        ProjectFactory.create(amount_asked=0)

        result = self.search({'project_type': 'funding'})
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_type_voting_filter(self):
        voting = ProjectPhase.objects.get(slug='voting')
        project = ProjectFactory.create(status=voting)
        ProjectFactory.create()

        result = self.search({'project_type': 'voting'})
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_start_filter(self):
        project = ProjectFactory.create()
        TaskFactory.create(
            project=project,
            deadline=datetime(2017, 01, 02, tzinfo=get_current_timezone())
        )
        other_project = ProjectFactory.create()
        TaskFactory.create(
            project=other_project,
            deadline=datetime(2016, 01, 02, tzinfo=get_current_timezone())
        )

        result = self.search({'start': '2017-01-01'})
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_start_end_filter(self):
        project = ProjectFactory.create()
        TaskFactory.create(
            project=project,
            type='event',
            deadline=datetime(2017, 01, 02, tzinfo=get_current_timezone())
        )
        other_project = ProjectFactory.create()
        TaskFactory.create(
            project=other_project,
            type='event',
            deadline=datetime(2017, 07, 01, tzinfo=get_current_timezone())
        )

        result = self.search({'start': '2017-01-01', 'end': '2017-06-01'})
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_start_end_filter_ongoing(self):
        project = ProjectFactory.create()
        TaskFactory.create(
            project=project,
            type='event',
            deadline=datetime(2017, 01, 02, tzinfo=get_current_timezone())
        )
        other_project = ProjectFactory.create()
        TaskFactory.create(
            project=other_project,
            type='ongoing',
            deadline=datetime(2017, 07, 01, tzinfo=get_current_timezone())
        )

        result = self.search({'start': '2017-01-01', 'end': '2017-06-01'})
        self.assertEqual(result.data['count'], 2)

    def test_theme_filter(self):
        theme = ProjectThemeFactory.create()
        project = ProjectFactory.create(theme=theme)
        other_theme = ProjectThemeFactory.create()
        ProjectFactory.create(theme=other_theme)

        result = self.search({'theme': theme.id})
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_category_filter(self):
        project = ProjectFactory.create()

        category = CategoryFactory.create()
        project.categories.add(category)
        project.categories.add(CategoryFactory.create())

        ProjectFactory.create()

        result = self.search({'category': category.id})
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_skill_filter(self):
        project = ProjectFactory.create()
        skill = SkillFactory.create()
        TaskFactory.create(project=project, skill=skill)
        ProjectFactory.create()

        result = self.search({'skill': skill.id})
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_text_query(self):
        project = ProjectFactory.create(
            title='Amsterdam Rotterdam Eindhoven Utrecht'
        )
        ProjectFactory.create(
            title='Rotterdam Eindhoven Utrecht Makkum',
            pitch='Amsterdam'
        )
        ProjectFactory.create(
            title='Rotterdam Eindhoven Utrecht Bolsward',
            story='Amsterdam'
        )
        task_title_project = ProjectFactory.create(
            title='Rotterdam Eindhoven Utrecht Harlingen',
        )
        TaskFactory.create(title='Amsterdam', project=task_title_project)
        task_description_project = ProjectFactory.create(
            title='Rotterdam Eindhoven Utrecht Franeker',
        )
        TaskFactory.create(description='Amsterdam', project=task_description_project)
        ProjectFactory.create()

        result = self.search({'text': 'Amsterdam'})
        self.assertEqual(result.data['count'], 5)
        # We boost the title, so the project with Amsterdam in the title should be first
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_combined_filters(self):
        location = LocationFactory.create()
        country = CountryFactory.create()
        project = ProjectFactory.create(
            location=location,
            country=country
        )
        ProjectFactory.create(
            country=country
        )
        ProjectFactory.create(
            location=location,
        )

        result = self.search({
            'location': location.id,
            'country': country.id
        })

        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_score_status(self):
        campaign = ProjectPhase.objects.get(slug='campaign')
        project = ProjectFactory.create(status=campaign)
        ProjectFactory.create()
        result = self.search({})

        self.assertEqual(result.data['count'], 2)
        self.assertEqual(result.data['results'][0]['title'], project.title)

    def test_score_donations(self):
        order = OrderFactory.create(status='settled')
        project = ProjectFactory.create()
        DonationFactory(
            order=order,
            project=project,
            fundraiser=None,
            created=now() - timedelta(days=10)
        )
        DonationFactory(
            order=order,
            project=project,
            fundraiser=None,
            created=now() - timedelta(days=10)
        )
        DonationFactory(
            order=order,
            project=project,
            fundraiser=None,
            created=now() - timedelta(days=10)
        )

        other_project = ProjectFactory.create()
        DonationFactory(
            order=order,
            project=other_project,
            fundraiser=None,
            created=now() - timedelta(days=1)
        )
        DonationFactory(
            order=order,
            project=other_project,
            fundraiser=None,
            created=now() - timedelta(days=1)
        )
        result = self.search({})

        self.assertEqual(result.data['count'], 2)
        self.assertEqual(result.data['results'][0]['title'], other_project.title)

    def test_score_taskmembers(self):
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        TaskMemberFactory(
            task=task,
            created=now() - timedelta(days=10)
        )
        TaskMemberFactory(
            task=task,
            created=now() - timedelta(days=10)
        )
        TaskMemberFactory(
            task=task,
            created=now() - timedelta(days=10)
        )

        other_project = ProjectFactory.create()
        other_task = TaskFactory.create(project=other_project)
        TaskMemberFactory(
            task=other_task,
            created=now() - timedelta(days=1)
        )
        TaskMemberFactory(
            task=other_task,
            created=now() - timedelta(days=1)
        )

        result = self.search({})

        self.assertEqual(result.data['count'], 2)
        self.assertEqual(result.data['results'][0]['title'], other_project.title)

    def test_score_votes(self):
        project = ProjectFactory.create()
        VoteFactory(
            project=project,
            created=now() - timedelta(days=10)
        )
        VoteFactory(
            project=project,
            created=now() - timedelta(days=10)
        )
        VoteFactory(
            project=project,
            created=now() - timedelta(days=10)
        )

        other_project = ProjectFactory.create()
        VoteFactory(
            project=other_project,
            created=now() - timedelta(days=1)
        )
        VoteFactory(
            project=other_project,
            created=now() - timedelta(days=1)
        )
        result = self.search({})

        self.assertEqual(result.data['count'], 2)
        self.assertEqual(result.data['results'][0]['title'], other_project.title)

    def test_combined_scores(self):
        project = ProjectFactory.create()
        task = TaskFactory.create(project=project)
        TaskMemberFactory(
            task=task,
            created=now() - timedelta(days=10)
        )
        TaskMemberFactory(
            task=task,
            created=now() - timedelta(days=10)
        )
        TaskMemberFactory(
            task=task,
            created=now() - timedelta(days=10)
        )

        other_project = ProjectFactory.create()
        VoteFactory(
            project=other_project,
            created=now() - timedelta(days=1)
        )
        VoteFactory(
            project=other_project,
            created=now() - timedelta(days=1)
        )
        result = self.search({})

        self.assertEqual(result.data['count'], 2)
        self.assertEqual(result.data['results'][0]['title'], other_project.title)



