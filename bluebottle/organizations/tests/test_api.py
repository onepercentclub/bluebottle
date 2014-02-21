import json

from django.core.urlresolvers import reverse
from django.test import TestCase

from bluebottle.organizations.models import Organization
from bluebottle.test.factory_models.accounts_factories import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations_factories import (
    OrganizationFactory, OrganizationMemberFactory)


class OrganizationsEndpointTestCase(TestCase):
    """
    Base class for test cases for ``organizations`` module.

    The testing classes for ``organization`` odule related to the API must
    subclass this.
    """
    def setUp(self):
        self.user_1 = BlueBottleUserFactory.create()
        self.user_2 = BlueBottleUserFactory.create()

        self.organization_1 = OrganizationFactory.create()
        self.organization_2 = OrganizationFactory.create()
        self.organization_3 = OrganizationFactory.create()

        self.member_1 = OrganizationMemberFactory(organization=self.organization_1, user=self.user_1)
        self.member_2 = OrganizationMemberFactory(organization=self.organization_2, user=self.user_1)
        self.member_3 = OrganizationMemberFactory(organization=self.organization_3, user=self.user_2)


class OrganizationListTestCase(OrganizationsEndpointTestCase):
    """
    Test case for ``OrganizationsList`` API view.

    Endpoint: /api/organizations/
    """
    def test_api_organizations_list_endpoint(self):
        """
        Tests that the list of organizations can be obtained from its
        endpoint.
        """
        response = self.client.get(reverse('organization_list'))

        self.assertEqual(response.status_code, 200)

        # We received the three organizations created.
        data = json.loads(response.content)
        self.assertEqual(data['count'], 3)


class OrganizationDetailTestCase(OrganizationsEndpointTestCase):
    """
    Test case for ``OrganizationsList`` API view.

    Endpoint: /api/organizations/{pk}
    """
    def test_api_organizations_detail_endpoint(self):
        response = self.client.get(reverse('organization_detail', kwargs={'pk': self.organization_1.pk}))

        self.assertEqual(response.status_code, 200)


class ManageOrganizationListTestCase(OrganizationsEndpointTestCase):
    """
    Test case for ``ManageOrganizationsList`` API view.

    Endpoint: /api/organizations/manage/
    """
    def test_api_manage_organizations_list_user_filter(self):
        """
        Tests that the organizations returned are those which belongs to the
        logged-in user.
        """
        self.client.login(email=self.user_1.email, password='testing')
        response = self.client.get(reverse('manage_organization_list'))

        self.assertEqual(response.status_code, 200)

        # The user ``user_1`` only have membership for two organizations now.
        data = json.loads(response.content)
        self.assertEqual(data['count'], 2)

    def test_api_manage_organizations_list_post(self):
        """
        Tests POSTing new data to the endpoint.
        """
        post_data = {
            'name': '1% Club',
            'slug': '1-club',
            'address_line1': "'s Gravenhekje 1a",
            'address_line2': '1011 TG',
            'city': 'Amsterdam',
            'state': 'North Holland',
            'country': self.organization_1.country.pk,
            'postal_code': '1011TG',
            'phone_number': '(+31) 20 715 8980',
            'website': 'http://onepercentclub.com',
            'email': 'info@onepercentclub.com',
            'twitter': '@1percentclub',
            'facebook': '/onepercentclub',
            'skype': 'onepercentclub'
        }

        self.client.login(email=self.user_1.email, password='testing')
        response = self.client.post(reverse('manage_organization_list'), post_data)

        self.assertEqual(response.status_code, 201)

        # Check the data.
        organization = Organization.objects.latest('pk')
        self.assertEqual(organization.name, post_data['name'])
        self.assertEqual(organization.slug, post_data['slug'])
        self.assertEqual(organization.address_line1, post_data['address_line1'])
        self.assertEqual(organization.address_line2, post_data['address_line2'])
        self.assertEqual(organization.city, post_data['city'])
        self.assertEqual(organization.state, post_data['state'])
        self.assertEqual(organization.country.pk, post_data['country'])
        self.assertEqual(organization.postal_code, post_data['postal_code'])
        self.assertEqual(organization.phone_number, post_data['phone_number'])
        self.assertEqual(organization.website, post_data['website'])
        self.assertEqual(organization.email, post_data['email'])
        self.assertEqual(organization.twitter, post_data['twitter'])
        self.assertEqual(organization.facebook, post_data['facebook'])
        self.assertEqual(organization.skype, post_data['skype'])


class ManageOrganizationDetailTestCase(OrganizationsEndpointTestCase):
    """
    Test case for ``OrganizationsList`` API view.

    Endpoint: /api/organizations/manage/{pk}
    """
    def test_manage_organizations_detail_login_required(self):
        """
        Tests that the endpoint first restricts results to logged-in users.
        """
        # Making the request without logging in...
        response = self.client.get(reverse('manage_organization_detail', kwargs={'pk': self.organization_1.pk}))

        self.assertEqual(response.status_code, 403)

    def test_manage_organizations_detail_user_restricted(self):
        """
        Tests that the endpoint restricts the access to the users who have
        membership for the requested organization.
        """
        self.client.login(email=self.user_1.email, password='testing')

        # Requesting an organization for which the user have no membership...
        response = self.client.get(reverse('manage_organization_detail', kwargs={'pk': self.organization_3.pk}))

        # ...it fails.
        self.assertEqual(response.status_code, 403)

    def test_manage_organizations_detail_get_success(self):
        """
        Tests a successful GET request over the endpoint.
        """
        self.client.login(email=self.user_1.email, password='testing')
        response = self.client.get(reverse('manage_organization_detail', kwargs={'pk': self.organization_1.pk}))

        self.assertEqual(response.status_code, 200)

    def test_manage_organizations_detail_put_success(self):
        """
        Tests a successful PUT request over the endpoint.
        """
        put_data = {
            'name': 'New name',
            'slug': 'new-slug',
            'address_line1': 'new address',
            'address_line2': 'new address (2)',
            'city': 'Utrecht',
            'state': 'Utrecht',
            'country': self.organization_1.country.pk,
            'postal_code': '3581WJ',
            'phone_number': '(+31) 20 123 4567',
            'website': 'http://www.utrecht.nl',
            'email': 'info@utrecht.nl',
            'twitter': 'utrecht',
            'facebook': '/utrecht',
            'skype': 'utrecht'
        }

        data = json.dumps(put_data)

        self.client.login(email=self.user_1.email, password='testing')
        response = self.client.put(
            reverse('manage_organization_detail', kwargs={'pk': self.organization_1.pk}), data,
            content_type='application/json')

        self.assertEqual(response.status_code, 200)

        # Check the data.
        organization = Organization.objects.get(pk=self.organization_1.pk)
        self.assertEqual(organization.name, put_data['name'])
        self.assertEqual(organization.slug, put_data['slug'])
        self.assertEqual(organization.address_line1, put_data['address_line1'])
        self.assertEqual(organization.address_line2, put_data['address_line2'])
        self.assertEqual(organization.city, put_data['city'])
        self.assertEqual(organization.state, put_data['state'])
        self.assertEqual(organization.country.pk, put_data['country'])
        self.assertEqual(organization.postal_code, put_data['postal_code'])
        self.assertEqual(organization.phone_number, put_data['phone_number'])
        self.assertEqual(organization.website, put_data['website'])
        self.assertEqual(organization.email, put_data['email'])
        self.assertEqual(organization.twitter, put_data['twitter'])
        self.assertEqual(organization.facebook, put_data['facebook'])
        self.assertEqual(organization.skype, put_data['skype'])
