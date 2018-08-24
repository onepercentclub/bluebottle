from datetime import timedelta
from django.test.utils import override_settings
from django.test import tag
from django.utils.timezone import now

from django_elasticsearch_dsl.test import ESTestCase
from elasticsearch_dsl import Q, SF

from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.tasks import TaskFactory, SkillFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.clients.utils import LocalTenant
from bluebottle.clients.models import Client
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.projects.documents import ProjectDocument, project
from bluebottle.donations.models import Donation


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
@tag('elasticsearch')
class ProjectIndexTestCase(ESTestCase, BluebottleTestCase):
    def setUp(self):
        super(ProjectIndexTestCase, self).setUp()
        self.search = ProjectDocument.search()

        self.project1 = ProjectFactory.create(
            title='One two three',
            pitch='One two',
            story='One two',
            status=ProjectPhase.objects.get(slug='campaign')
        )
        self.project1.projectlocation.latitude = 52.3737123
        self.project1.projectlocation.longitude = 4.9057741
        self.project1.projectlocation.save()

        self.project2 = ProjectFactory.create(
            title='One two',
            pitch='One two three',
            story='One two three four',
            status=ProjectPhase.objects.get(slug='done-complete')
        )
        self.project2.projectlocation.latitude = 52.389901
        self.project2.projectlocation.longitude = 4.8829646
        self.project2.projectlocation.save()

        self.project3 = ProjectFactory.create(
            title='One two four',
            pitch='One two four',
            story='One two four',
            status=ProjectPhase.objects.get(slug='done-complete')
        )
        self.project3.projectlocation.latitude = 52.0907322
        self.project3.projectlocation.longitude = 5.0864009
        self.project3.projectlocation.save()

    def test_index_name(self):
        self.assertEqual(ProjectDocument._doc_type.index, 'test-projects_ded_test')
        self.assertEqual(project._name, 'test-projects_ded_test')

        with LocalTenant(Client.objects.get(client_name='test2')):
            self.assertEqual(ProjectDocument._doc_type.index, 'test2-projects_ded_test')
            self.assertEqual(project._name, 'test2-projects_ded_test')

    def test_search(self):
        result = self.search.query(
            Q('match', title='three') |
            Q('match', pitch='three') |
            Q('match', story='three')
        ).to_queryset()

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[0], self.project2
        )
        self.assertEqual(
            result[1], self.project1
        )

    def test_search_boost(self):
        result = self.search.query(
            Q('match', title={'query': 'three', 'boost': 4}) |
            Q('match', pitch='three') |
            Q('match', story='three')
        ).to_queryset()

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[0], self.project1
        )
        self.assertEqual(
            result[1], self.project2
        )

    def test_search_filter(self):
        result = self.search.query(
            Q('match', title={'query': 'three', 'boost': 2}) |
            Q('match', pitch='three') |
            Q('match', story='three')
        ).to_queryset()

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[0], self.project1
        )
        self.assertEqual(
            result[1], self.project2
        )

    def test_search_task_title(self):
        TaskFactory.create(project=self.project3, title='One two three')
        result = self.search.query(
            Q('match', title='three') |
            Q('match', pitch='three') |
            Q('match', story='three') |
            Q('nested', path='task_set', query=Q('match', **{'task_set.title': 'three'}))
        ).to_queryset()

        self.assertEqual(len(result), 3)
        for proj in result:
            self.assertTrue(proj in [self.project1, self.project2, self.project3])

    def test_search_task_skill(self):
        skill = SkillFactory.create(name="Skill")
        other_skill = SkillFactory.create(name="Bla")

        TaskFactory.create(project=self.project1, skill=other_skill)
        TaskFactory.create(project=self.project2, skill=skill)
        TaskFactory.create(project=self.project3, skill=other_skill)

        query = self.search.query(
            Q('match', title='three') |
            Q(
                'nested',
                path='task_set',
                query=Q('match', **{'task_set.skill.id': {'query': skill.id, 'boost': 4}})
            )
        )
        result = query.to_queryset()

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[0], self.project2,
        )
        self.assertEqual(
            result[1], self.project1,
        )

    def test_search_location(self):
        query = self.search.query(
            Q(
                'function_score',
                query=Q('match', title='one'),
                functions=[
                    SF(
                        'gauss',
                        position={
                            'origin': (52.389901, 4.8829646),
                            'offset': "2km",
                            'scale': "50km"
                        }
                    ),
                ]
            )
        )
        result = query.to_queryset()
        self.assertEqual(len(result), 3)
        self.assertEqual(
            result[0], self.project2,
        )
        self.assertEqual(
            result[1], self.project1,
        )
        self.assertEqual(
            result[2], self.project3,
        )

    def test_search_recent_donation(self):
        order = OrderFactory.create()
        for days in [1]:
            donation = Donation.objects.create(
                project=self.project1, order=order
            )
            donation.created = now() - timedelta(days=days)
            donation.save()
        for days in [2]:
            donation = DonationFactory.create(
                project=self.project2, order=order
            )
            donation.created = now() - timedelta(days=days)
            donation.save()

        for days in [4]:
            donation = DonationFactory.create(
                project=self.project3, order=order
            )
            donation.created = now() - timedelta(days=days)
            donation.save()

        query = self.search.query(
            Q(
                'function_score',
                query=Q('exists', field='donations'),
                functions=[
                    SF({
                        'gauss': {
                            'donations': {
                                'scale': "10d",
                            },
                            'multi_value_mode': 'sum',
                        },
                    })
                ]
            )
        ).extra(explain=True)

        result = query.to_queryset()

        self.assertEqual(len(result), 3)
        self.assertEqual(
            result[0], self.project1,
        )
        self.assertEqual(
            result[1], self.project2,
        )
        self.assertEqual(
            result[2], self.project3,
        )

    def test_multi_tenant(self):
        with LocalTenant(Client.objects.get(client_name='test2')):
            ProjectFactory.create(
                title='One two three test2',
                pitch='One two',
                story='One two',
                status=ProjectPhase.objects.get(slug='campaign')
            )

        result = self.search.query(
            Q('match', title='three')
        ).to_queryset()

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0], self.project1,
        )
