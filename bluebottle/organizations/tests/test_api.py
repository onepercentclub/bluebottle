
from future import standard_library
standard_library.install_aliases()
from urllib.parse import urlencode
import datetime
import json

from django.urls import reverse
from django.utils.timezone import now
from moneyed import Money
from rest_framework import status

from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.funding.tests.factories import DonorFactory, FundingFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.organizations.models import Organization
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import (
    OrganizationContactFactory, OrganizationFactory
)
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DateParticipantFactory,
    DateRegistrationFactory,
    DeadlineActivityFactory,
    DeadlineParticipantFactory,
)


class OrganizationsEndpointTestCase(BluebottleTestCase):
    """
    Base class for test cases for ``organizations`` module.

    The testing classes for ``organization`` module related to the API must
    subclass this.
    """

    def setUp(self):
        super(OrganizationsEndpointTestCase, self).setUp()
        self.client = JSONAPITestClient()

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
                                   user=self.user_1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['meta']['pagination']['count'], 5)

    def test_api_organizations_search(self):
        """
        Tests that the organizations search is not intelligent.
        """
        # Search for organizations with "evil" in their name.
        url = "{}?{}".format(reverse('organization_list'), urlencode({'filter[search]': 'Evil'}))
        response = self.client.get(url, user=self.user_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Expect two organizations with 'ev'
        self.assertEqual(response.data['meta']['pagination']['count'], 1)

    def test_api_organizations_search_extended(self):
        """
        Tests that the list of organizations can be obtained from its
        endpoint with different order.
        """
        url = "{}?{}".format(reverse('organization_list'), urlencode({'filter[search]': 'Knight'}))
        response = self.client.get(url, user=self.user_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['meta']['pagination']['count'], 2)

    def test_api_organizations_search_case_insensitve(self):
        """
        Tests that the organizations search is case insensitive.
        """
        url = "{}?{}".format(reverse('organization_list'), urlencode({'filter[search]': 'kids'}))
        response = self.client.get(url, user=self.user_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['meta']['pagination']['count'], 2)


class OrganizationDetailTestCase(OrganizationsEndpointTestCase):
    """
    Test case for ``OrganizationsList`` API view.

    Endpoint: /api/organizations/{pk}
    """

    def test_anonymous_api_organizations_detail_endpoint(self):
        response = self.client.get(
            reverse('organization_detail', kwargs={'pk': self.organization_1.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['id'], str(self.organization_1.pk))
        stats = response.json()['data']['meta']['stats']
        self.assertEqual(stats['hours'], 0)
        self.assertEqual(stats['effort'], 0)
        self.assertEqual(stats['contributors'], 0)
        self.assertEqual(stats['amount'], {'amount': 0, 'currency': stats['amount']['currency']})
        self.assertEqual(stats['collected'], [])
        self.assertEqual(stats['impact'], [])

    def test_get_stats(self):
        initiative = InitiativeFactory.create(status='approved')

        deadline_activity = DeadlineActivityFactory.create(
            initiative=initiative,
            organization=self.organization_1,
            status='succeeded',
            start=datetime.date.today() - datetime.timedelta(weeks=2),
            deadline=datetime.date.today() - datetime.timedelta(weeks=1),
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=3)
        )
        DeadlineParticipantFactory.create_batch(3, activity=deadline_activity)

        date_activity = DateActivityFactory.create(
            initiative=initiative,
            organization=self.organization_1,
            status='succeeded',
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=2),
        )
        slot = DateActivitySlotFactory.create(
            activity=date_activity,
            start=now() - datetime.timedelta(weeks=1),
        )

        registrations = DateRegistrationFactory.create_batch(3, activity=date_activity)
        for registration in registrations:
            DateParticipantFactory.create(slot=slot, registration=registration)

        funding = FundingFactory.create(
            initiative=initiative,
            organization=self.organization_1,
            deadline=now() + datetime.timedelta(weeks=1),
            status='open'
        )
        for donor in DonorFactory.create_batch(3, activity=funding, user=None, amount=Money(10, 'USD')):
            donor.contributions.get().states.succeed(save=True)
        for donor in DonorFactory.create_batch(3, activity=funding, user=None, amount=Money(10, 'EUR')):
            donor.contributions.get().states.succeed(save=True)

        deed_activity = DeedFactory.create(
            initiative=initiative,
            organization=self.organization_1,
            status='open',
            start=datetime.date.today() - datetime.timedelta(days=10),
            end=datetime.date.today() + datetime.timedelta(days=5)
        )

        DeedParticipantFactory.create_batch(3, activity=deed_activity)
        participants = DeedParticipantFactory.create_batch(3, activity=deed_activity)
        for participant in participants:
            participant.states.withdraw(save=True)

        collect_activity = CollectActivityFactory.create(
            initiative=initiative,
            organization=self.organization_1,
            status='open',
            start=datetime.date.today() - datetime.timedelta(weeks=2),
        )
        collect_activity.realized = 100
        collect_activity.save()
        CollectContributorFactory.create_batch(3, activity=collect_activity)

        unrelated_activity = DeadlineActivityFactory.create(
            initiative=initiative,
            status='open',
            start=datetime.date.today() - datetime.timedelta(weeks=2),
            deadline=datetime.date.today() + datetime.timedelta(weeks=1),
            registration_deadline=datetime.date.today() - datetime.timedelta(weeks=3)
        )
        DeadlineParticipantFactory.create_batch(3, activity=unrelated_activity)

        response = self.client.get(
            reverse('organization_detail', kwargs={'pk': self.organization_1.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        stats = response.json()['data']['meta']['stats']
        self.assertEqual(stats['hours'], 18.0)
        self.assertEqual(stats['amount'], {'amount': 75.0, 'currency': 'EUR'})
        self.assertEqual(stats['contributors'], 18)
        self.assertEqual(stats['effort'], 3)

    def test_anonymous_cannot_update(self):
        data = {
            'data': {
                'type': 'organizations',
                'id': self.organization_1.pk,
                'attributes': {
                    'name': 'Hacked',
                    'description': 'nope',
                }
            }
        }
        response = self.client.put(
            reverse('organization_detail', kwargs={'pk': self.organization_1.pk}),
            json.dumps(data),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ManageOrganizationListTestCase(OrganizationsEndpointTestCase):
    """
    Test case for ``ManageOrganizationsList`` API view.

    Endpoint: /api/organizations
    """

    def setUp(self):
        super(ManageOrganizationListTestCase, self).setUp()

        self.post_data = {
            'data': {
                'type': 'organizations',
                'attributes': {
                    'name': '1%Club',
                    'slug': 'hm',
                    'description': 'some description',
                    'website': 'http://onepercentclub.com',
                }
            }
        }

    def test_api_manage_organizations_list_user_filter(self):
        """
        Tests that all organizations are returned if there is not a search term supplied.
        """
        response = self.client.get(reverse('organization_list'), user=self.user_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['meta']['pagination']['count'], 5)

    def test_api_manage_organizations_list_post(self):
        """
        Tests POSTing new data to the endpoint.
        """
        post_data = self.post_data

        response = self.client.post(
            reverse('organization_list'),
            json.dumps(post_data),
            user=self.user_1)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        org_id = response.data['id']

        # Check the data.
        organization = Organization.objects.get(pk=org_id)
        self.assertEqual(organization.name, '1%Club')
        self.assertEqual(organization.slug, '1club')
        self.assertEqual(organization.description, 'some description')

    def test_api_manage_organizations_update_description(self):
        """
        Tests POSTing new data to the endpoint.
        """
        response = self.client.post(
            reverse('organization_list'),
            json.dumps(self.post_data),
            user=self.user_1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Update description
        org_id = response.data['id']
        self.post_data['data']['id'] = org_id
        self.post_data['data']['attributes']['description'] = 'Bla bla'
        url = reverse('organization_detail', kwargs={'pk': org_id})

        response = self.client.put(
            url,
            json.dumps(self.post_data),
            user=self.user_1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check the data.
        organization = Organization.objects.get(pk=org_id)
        self.assertEqual(organization.description, 'Bla bla')

    def test_api_manage_organizations_update_other_user(self):
        """
        Tests POSTing new data to the endpoint.
        """
        response = self.client.post(
            reverse('organization_list'),
            json.dumps(self.post_data),
            user=self.user_1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Update description
        org_id = response.data['id']
        self.post_data['data']['id'] = org_id
        self.post_data['data']['attributes']['description'] = 'Bla bla'
        url = reverse('organization_detail', kwargs={'pk': org_id})

        response = self.client.put(
            url,
            json.dumps(self.post_data),
            user=BlueBottleUserFactory.create())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.patch(
            url,
            json.dumps(self.post_data),
            user=BlueBottleUserFactory.create())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ManageOrganizationContactTestCase(OrganizationsEndpointTestCase):
    """
    Test case for ``OrganizationContact`` API

    Endpoint: /api/organizations/contacts
    """

    def test_create_contact(self):
        data = {
            'data': {
                'type': 'organization-contacts',
                'attributes': {
                    'name': 'Brian Brown',
                    'email': 'brian@brown.com',
                    'phone': '555-1243'
                }
            }
        }

        response = self.client.post(
            reverse('organization_contact_list'),
            json.dumps(data),
            user=self.user_1
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Brian Brown')

    def test_create_contact_without_phone(self):
        data = {
            'data': {
                'type': 'organization-contacts',
                'attributes': {
                    'name': 'Brian Brown',
                    'email': 'brian@brown.com'
                }
            }
        }

        response = self.client.post(
            reverse('organization_contact_list'),
            json.dumps(data),
            user=self.user_1
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Brian Brown')

    def test_organization_contact(self):
        contact = OrganizationContactFactory.create(owner=self.user_1)

        response = self.client.get(
            reverse('organization_contact_detail', kwargs={'pk': contact.pk}),
            user=self.user_1
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], contact.name)


class ManageOrganizationDetailTestCase(OrganizationsEndpointTestCase):
    """
    Test case for ``OrganizationsList`` API view.

    Endpoint: /api/organizations/{pk}
    """

    def test_manage_organizations_detail_get_anonymous(self):
        """
        Public platforms allow anonymous GET of organization detail.
        """
        response = self.client.get(
            reverse('organization_detail',
                    kwargs={'pk': self.organization_1.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_manage_organizations_detail_get_success(self):
        """
        Tests a successful GET request over the endpoint.
        """
        response = self.client.get(reverse('organization_detail',
                                           kwargs={
                                               'pk': self.organization_1.pk}),
                                   user=self.user_1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stats', response.json()['data']['meta'])
