import json

from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.projects.models import PartnerOrganization
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory


class PartnerEndpointTestCase(BluebottleTestCase):
    """
    Integration tests for the Partner API.
    """

    def setUp(self):
        super(PartnerEndpointTestCase, self).setUp()
        self.init_projects()
        self.campaign_phase = ProjectPhase.objects.get(slug='campaign')

    def test_partner_project(self):
        """ BB-3671 - serialization fails using bluebottle.projects' serializer
            because it depends on certain annotations being present """
        organization = OrganizationFactory.create()
        organization.save()

        po = PartnerOrganization.objects.create(name="OPC", slug="opc",
                                                description="1%")

        ProjectFactory.create(title="Project with partner org",
                              partner_organization=po,
                              organization=organization,
                              status=self.campaign_phase)

        url = reverse('partner-detail', kwargs={'slug': po.slug})
        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)


class PartnerPreviewEndpointTestCase(BluebottleTestCase):
    """
    Integration tests for the Partner API.
    """

    def setUp(self):
        super(PartnerPreviewEndpointTestCase, self).setUp()
        self.init_projects()
        self.campaign_phase = ProjectPhase.objects.get(slug='campaign')

    def test_partner_project(self):
        organization = OrganizationFactory.create()
        organization.save()

        po = PartnerOrganization.objects.create(name="OPC", slug="opc",
                                                description="1%")

        ProjectFactory.create(title="Project with partner org",
                              partner_organization=po,
                              organization=organization,
                              status=self.campaign_phase)

        url = reverse('partner-preview-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEquals(len(data), 1)
        self.assertIn('id', data[0])
        self.assertIn('name', data[0])
        self.assertNotIn('projects', data[0])
