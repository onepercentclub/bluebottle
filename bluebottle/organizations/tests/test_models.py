from bluebottle.organizations.models import Organization

from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.organizations import (
    OrganizationFactory, OrganizationMemberFactory
)
from bluebottle.test.utils import BluebottleTestCase


class OrganizationModelTest(BluebottleTestCase):
    def setUp(self):
        super(OrganizationModelTest, self).setUp()
        self.init_projects()

        for name in ['test', 'tast', 'tist', 'tust']:
            organization = OrganizationFactory.create(name=name)
            ProjectFactory(
                organization=organization
            )
            OrganizationMemberFactory.create(organization=organization)

    def test_merge(self):
        master = Organization.objects.get(name='test')

        master.merge(
            Organization.objects.filter(name__in=('tast', 'tist'))
        )

        self.assertEqual(len(Organization.objects.all()), 2)
        self.assertEqual(len(master.projects.all()), 3)
        self.assertEqual(len(master.members.all()), 3)

        not_merged = Organization.objects.get(name='tust')
        self.assertEqual(len(not_merged.projects.all()), 1)
        self.assertEqual(len(not_merged.members.all()), 1)
