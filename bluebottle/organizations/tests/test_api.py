import json
import urllib

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from rest_framework import status

from bluebottle.organizations.models import Organization
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import (
    OrganizationContactFactory, OrganizationFactory
)
from bluebottle.test.utils import BluebottleTestCase


class OrganizationsEndpointTestCase(BluebottleTestCase):
    """
    Base class for test cases for ``organizations`` module.

    The testing classes for ``organization`` module related to the API must
    subclass this.
    """

    def setUp(self):
        super(OrganizationsEndpointTestCase, self).setUp()

        self.user_1 = BlueBottleUserFactory.create()
        self.user_1_token = "JWT {0}".format(self.user_1.get_jwt_token())

        self.user_2 = BlueBottleUserFactory.create()

        self.organization_1 = OrganizationFactory.create(
            owner=self.user_1,
            name='Evil Knight'
        )
        self.organization_2 = OrganizationFactory.create(
            owner=self.user_1,
            name='Evel Knievel'
        )
        self.organization_3 = OrganizationFactory.create(
            owner=self.user_1,
            name='Hanson Kids'
        )
        self.organization_4 = OrganizationFactory.create(
            owner=self.user_1,
            name='Knight Rider'
        )
        self.organization_5 = OrganizationFactory.create(
            owner=self.user_2,
            name='Kids Club'
        )


class OrganizationListTestCase(OrganizationsEndpointTestCase):
    """
    Test case for ``OrganizationsList`` API view.
    """

    def test_unauth_api_organizations_list_endpoint(self):
        """
        Tests that the list of organizations can not be accessed if
        not authenticated.
        """
        response = self.client.get(reverse('organization_list'))

        self.assertEqual(response.status_code, 401)

    def test_auth_api_organizations_list_endpoint(self):
        """
        Tests that the list of organizations can be queried if authenticated
        but it will not return results unless a search term is supplied.
        """
        response = self.client.get(reverse('organization_list'),
                                   token=self.user_1_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['meta']['pagination']['count'], 5)

    def test_api_organizations_search(self):
        """
        Tests that the organizations search is not intelligent.
        """
        # Search for organizations with "evil" in their name.
        url = "{}?{}".format(reverse('organization_list'), urllib.urlencode({'search': 'Evil'}))
        response = self.client.get(url, token=self.user_1_token)
        self.assertEqual(response.status_code, 200)
        # Expect two organizations with 'ev'
        self.assertEqual(response.data['meta']['pagination']['count'], 1)

    def test_api_organizations_search_extended(self):
        """
        Tests that the list of organizations can be obtained from its
        endpoint with different order.
        """
        url = "{}?{}".format(reverse('organization_list'), urllib.urlencode({'search': 'Knight'}))
        response = self.client.get(url, token=self.user_1_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['meta']['pagination']['count'], 2)

    def test_api_organizations_search_case_insensitve(self):
        """
        Tests that the organizations search is case insensitive.
        """
        url = "{}?{}".format(reverse('organization_list'), urllib.urlencode({'search': 'kids'}))
        response = self.client.get(url, token=self.user_1_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['meta']['pagination']['count'], 2)


class OrganizationDetailTestCase(OrganizationsEndpointTestCase):
    """
    Test case for ``OrganizationsList`` API view.

    Endpoint: /api/organizations/{pk}
    """

    def test_unauth_api_organizations_detail_endpoint(self):
        response = self.client.get(
            reverse('organization_detail',
                    kwargs={'pk': self.organization_1.pk}))

        self.assertEqual(response.status_code, 401)


class ManageOrganizationListTestCase(OrganizationsEndpointTestCase):
    """
    Test case for ``ManageOrganizationsList`` API view.

    Endpoint: /api/organizations
    """

    def setUp(self):
        super(ManageOrganizationListTestCase, self).setUp()

        self.post_data = {
            'name': '1% Club',
            'description': 'some description',
            'website': 'http://onepercentclub.com',
        }

    def test_api_manage_organizations_list_user_filter(self):
        """
        Tests that no organizations are returned if there is not a search term supplied.
        """
        response = self.client.get(reverse('organization_list'), token=self.user_1_token)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 0)

    def test_api_manage_organizations_list_post(self):
        """
        Tests POSTing new data to the endpoint.
        """
        post_data = self.post_data

        response = self.client.post(
            reverse('organization_list'),
            post_data,
            token=self.user_1_token)

        self.assertEqual(response.status_code, 201)

        # Check the data.
        organization = Organization.objects.latest('pk')
        self.assertEqual(organization.name, post_data['name'])
        self.assertEqual(organization.slug, '1-club')
        self.assertEqual(
            organization.address_line1, post_data['address_line1'])
        self.assertEqual(
            organization.address_line2, post_data['address_line2'])
        self.assertEqual(organization.city, post_data['city'])
        self.assertEqual(organization.state, post_data['state'])
        self.assertEqual(organization.country.pk, post_data['country'])
        self.assertEqual(organization.postal_code, post_data['postal_code'])
        self.assertEqual(organization.phone_number, post_data['phone_number'])
        self.assertEqual(organization.website, post_data['website'])
        self.assertEqual(organization.email, post_data['email'])

    def test_api_manage_organizations_list_post_blank_description(self):
        """
        Tests POSTing new data to the endpoint.
        """
        post_data = self.post_data
        post_data['description'] = ''

        response = self.client.post(
            reverse('organization_list'),
            post_data,
            token=self.user_1_token)

        self.assertEqual(response.status_code, 201)

    @override_settings(CLOSED_SITE=False)
    def test_api_manage_organizations_membership(self):
        """
        Tests POSTing new data to the endpoint.
        """
        post_data = self.post_data

        response = self.client.post(
            reverse('organization_list'),
            post_data,
            token=self.user_1_token)

        self.assertEqual(response.status_code, 201)


class ManageOrganizationContactTestCase(OrganizationsEndpointTestCase):
    """
    Test case for ``OrganizationContact`` API

    Endpoint: /api/organizations/contacts
    """

    def test_create_contact(self):
        post_data = {
            'name': 'Brian Brown',
            'email': 'brian@brown.com',
            'phone': '555-1243',
            'organization': self.organization_1.pk
        }

        response = self.client.post(
            reverse('organization_contact_list'),
            post_data,
            token=self.user_1_token)

        data = json.loads(response.content)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['owner'], self.user_1.pk)
        self.assertEqual(data['name'], post_data['name'])
        self.assertEqual(data['phone'], post_data['phone'])
        self.assertEqual(data['email'], post_data['email'])
        self.assertEqual(data['organization'], self.organization_1.pk)

    def test_organization_contact(self):
        contact = OrganizationContactFactory.create(owner=self.user_1, organization=self.organization_1)

        response = self.client.get(
            reverse('organization_detail',
                    kwargs={'pk': self.organization_1.pk}),
            token=self.user_1_token)

        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('contacts' in data)

        contact_data = data['contacts'][0]
        self.assertEqual(contact_data['name'], contact.name)
        self.assertEqual(contact_data['phone'], contact.phone)
        self.assertEqual(contact_data['email'], contact.email)

    def test_organization_without_contact(self):
        # create contact for user_2
        OrganizationContactFactory.create(owner=self.user_2, organization=self.organization_2)

        # request organization as user_1
        response = self.client.get(
            reverse('organization_detail',
                    kwargs={'pk': self.organization_2.pk}),
            token=self.user_1_token)

        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['contacts']), 0)

    def test_organization_contacts_ordering(self):
        for name in ['one', 'two', 'three']:
            OrganizationContactFactory.create(name=name, owner=self.user_1, organization=self.organization_1)

        response = self.client.get(
            reverse('organization_detail',
                    kwargs={'pk': self.organization_1.pk}),
            token=self.user_1_token)

        data = json.loads(response.content)
        contacts = data['contacts']
        self.assertEqual(len(contacts), 3)
        self.assertEqual(contacts[0]['name'], 'three')


class ManageOrganizationDetailTestCase(OrganizationsEndpointTestCase):
    """
    Test case for ``OrganizationsList`` API view.

    Endpoint: /api/organizations/{pk}
    """

    def test_manage_organizations_detail_login_required(self):
        """
        Tests that the endpoint first restricts results to logged-in users.
        """
        # Making the request without logging in...
        response = self.client.get(
            reverse('organization_detail',
                    kwargs={'pk': self.organization_1.pk}))
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)

    def test_manage_organizations_detail_get_success(self):
        """
        Tests a successful GET request over the endpoint.
        """
        response = self.client.get(reverse('organization_detail',
                                           kwargs={
                                               'pk': self.organization_1.pk}),
                                   token=self.user_1_token)

        self.assertEqual(response.status_code, 200)
