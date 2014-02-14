from django.test import TestCase
from bluebottle.test.factory_models.organizations_factories import OrganizationFactory
from bluebottle.bb_organizations import get_organization_model

ORGANIZATION_MODEL = get_organization_model()


class BaseOrganizationTestCase(TestCase):
    """
    Demo Testcase for abstract organization
    """

    def setUp(self):
        pass

    def test_fake(self):
        self.assertEquals(ORGANIZATION_MODEL.objects.count(), 0)
        organization = OrganizationFactory.create()
        self.assertEquals(ORGANIZATION_MODEL.objects.count(), 1)