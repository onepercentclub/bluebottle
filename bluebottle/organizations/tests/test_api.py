
from future import standard_library
standard_library.install_aliases()
from urllib.parse import urlencode
import datetime
import json
import os
from datetime import timedelta

from django.conf import settings
from django.test import tag
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import now
from django_elasticsearch_dsl.test import ESTestCase
from moneyed import Money
from rest_framework import status

from bluebottle.collect.tests.factories import CollectActivityFactory, CollectContributorFactory
from bluebottle.deeds.tests.factories import DeedFactory, DeedParticipantFactory
from bluebottle.funding.tests.factories import DonorFactory, FundingFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.members.models import MemberPlatformSettings
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
                    'slogan': 'nope',
                }
            }
        }
        response = self.client.put(
            reverse('organization_detail', kwargs={'pk': self.organization_1.pk}),
            json.dumps(data),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_closed_platform_anonymous(self):
        MemberPlatformSettings.objects.update(closed=True)
        try:
            response = self.client.get(
                reverse('organization_detail', kwargs={'pk': self.organization_1.pk})
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        finally:
            MemberPlatformSettings.objects.update(closed=False)

    def test_closed_platform_authenticated(self):
        MemberPlatformSettings.objects.update(closed=True)
        try:
            response = self.client.get(
                reverse('organization_detail', kwargs={'pk': self.organization_1.pk}),
                user=self.user_1,
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        finally:
            MemberPlatformSettings.objects.update(closed=False)


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
                    'slogan': 'some slogan',
                    'story': '<p>some story</p>',
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
        self.assertEqual(organization.slogan, 'some slogan')
        self.assertIn('some story', organization.story.html)

    def test_api_manage_organizations_update_slogan(self):
        """
        Tests POSTing new data to the endpoint.
        """
        response = self.client.post(
            reverse('organization_list'),
            json.dumps(self.post_data),
            user=self.user_1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Update slogan
        org_id = response.data['id']
        self.post_data['data']['id'] = org_id
        self.post_data['data']['attributes']['slogan'] = 'Bla bla'
        url = reverse('organization_detail', kwargs={'pk': org_id})

        response = self.client.put(
            url,
            json.dumps(self.post_data),
            user=self.user_1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check the data.
        organization = Organization.objects.get(pk=org_id)
        self.assertEqual(organization.slogan, 'Bla bla')

    def test_api_manage_organizations_update_other_user(self):
        """
        Tests POSTing new data to the endpoint.
        """
        response = self.client.post(
            reverse('organization_list'),
            json.dumps(self.post_data),
            user=self.user_1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Update slogan
        org_id = response.data['id']
        self.post_data['data']['id'] = org_id
        self.post_data['data']['attributes']['slogan'] = 'Bla bla'
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


TEST_IMAGE = os.path.join(
    settings.PROJECT_ROOT, 'bluebottle', 'files', 'tests', 'files', 'test-image.png'
)


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
@tag('elasticsearch')
class OrganizationPreviewListAPITestCase(ESTestCase, BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.client = JSONAPITestClient()
        self.url = reverse('organization-preview-list')
        self.user = BlueBottleUserFactory.create()

    def search(self, search=None, sort=None, user=None, **params):
        if search is not None:
            params['filter[search]'] = search
        if sort:
            params['sort'] = sort

        if user is None:
            user = self.user

        self.response = self.client.get(self.url, params, user=user)
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)
        self.data = json.loads(self.response.content)
        return self.data

    def assertFound(self, matching, count=None):
        self.assertEqual(
            self.data['meta']['pagination']['count'],
            len(matching) if count is None else count
        )
        self.assertEqual(
            set(item['id'] for item in self.data['data']),
            set(str(organization.pk) for organization in matching)
        )

    def get_result(self, organization):
        for item in self.data['data']:
            if item['id'] == str(organization.pk):
                return item
        self.fail(f'Organization {organization.pk} not found in results')

    # Permissions

    def test_anonymous(self):
        OrganizationFactory.create()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated(self):
        OrganizationFactory.create()
        response = self.client.get(self.url, user=self.user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_closed_platform_anonymous(self):
        MemberPlatformSettings.objects.update(closed=True)
        try:
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        finally:
            MemberPlatformSettings.objects.update(closed=False)

    def test_closed_platform_authenticated(self):
        MemberPlatformSettings.objects.update(closed=True)
        try:
            response = self.client.get(self.url, user=self.user)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        finally:
            MemberPlatformSettings.objects.update(closed=False)

    # Listing and serialization

    def test_list(self):
        organizations = OrganizationFactory.create_batch(3)

        self.search()
        self.assertFound(organizations)

    def test_list_empty(self):
        self.search()
        self.assertFound([])
        self.assertEqual(self.data['data'], [])

    def test_attributes(self):
        organization = OrganizationFactory.create(
            name='Red Cross',
            slogan='Helping people in need',
            website='https://example.com',
            image=TEST_IMAGE,
            logo=TEST_IMAGE,
        )

        organization.refresh_from_db()
        for field in (organization.image, organization.logo):
            self.assertTrue(field.name.endswith('.png'))
            self.assertTrue(field.storage.exists(field.name))

        self.search()
        result = self.get_result(organization)

        self.assertEqual(result['type'], 'organizations/preview')
        self.assertEqual(result['id'], str(organization.pk))

        attributes = result['attributes']
        self.assertEqual(attributes['name'], 'Red Cross')
        self.assertEqual(attributes['slug'], organization.slug)
        self.assertEqual(attributes['slogan'], 'Helping people in need')
        self.assertEqual(attributes['website'], 'https://example.com')
        self.assertEqual(attributes['verified'], False)
        self.assertEqual(attributes['activity-count'], {'succeeded': 0, 'open': 0})

        image = attributes['image']
        self.assertTrue(image.startswith(settings.MEDIA_URL))
        self.assertTrue(image.endswith('.png'))
        self.assertNotEqual(image, settings.MEDIA_URL + organization.image.name)

        logo = attributes['logo']
        self.assertEqual(
            set(logo.keys()),
            {'full', 'large', 'small', 'square', 'wide', 'original'}
        )
        for url in logo.values():
            self.assertTrue(url.startswith('http'), url)
            self.assertIn(f'{settings.MEDIA_URL}cache/', url)

        self.assertIn('created', result['meta'])

    def test_activity_counts(self):
        organization = OrganizationFactory.create()

        DeadlineActivityFactory.create_batch(2, organization=organization, status='open')
        DeadlineActivityFactory.create(organization=organization, status='running')
        DeadlineActivityFactory.create(organization=organization, status='succeeded')
        DeadlineActivityFactory.create(organization=organization, status='draft')
        DeadlineActivityFactory.create(organization=organization, status='cancelled')
        DeadlineActivityFactory.create(organization=OrganizationFactory.create(), status='open')

        self.search()
        attributes = self.get_result(organization)['attributes']

        self.assertEqual(attributes['activity-count'], {'succeeded': 1, 'open': 3})

    def test_activity_count_updates_index(self):
        organization = OrganizationFactory.create()
        activity = DeadlineActivityFactory.create(organization=organization, status='open')

        self.search()
        attributes = self.get_result(organization)['attributes']
        self.assertEqual(attributes['activity-count'], {'succeeded': 0, 'open': 1})

        activity.status = 'succeeded'
        activity.save()

        self.search()
        attributes = self.get_result(organization)['attributes']
        self.assertEqual(attributes['activity-count'], {'succeeded': 1, 'open': 0})

    def test_update_organization_updates_index(self):
        organization = OrganizationFactory.create(name='Old name')

        organization.name = 'New name'
        organization.save()

        self.search()
        self.assertEqual(self.get_result(organization)['attributes']['name'], 'New name')

    def test_delete_organization_removes_from_index(self):
        organization = OrganizationFactory.create()
        other = OrganizationFactory.create()

        organization.delete()

        self.search()
        self.assertFound([other])

    def test_search_name(self):
        matching = OrganizationFactory.create(name='Red Cross')
        OrganizationFactory.create(name='Salvation Army', slogan='Something else')

        self.search('Red Cross')
        self.assertFound([matching])

    def test_search_name_prefix(self):
        matching = OrganizationFactory.create(name='Greenpeace')
        OrganizationFactory.create(name='Salvation Army', slogan='Something else')

        self.search('Greenp')
        self.assertFound([matching])

    def test_search_name_case_insensitive(self):
        matching = OrganizationFactory.create(name='Greenpeace')
        OrganizationFactory.create(name='Salvation Army', slogan='Something else')

        self.search('greenpeace')
        self.assertFound([matching])

    def test_search_slogan(self):
        matching = OrganizationFactory.create(name='Foo', slogan='Saving the oceans')
        OrganizationFactory.create(name='Bar', slogan='Something else')

        self.search('oceans')
        self.assertFound([matching])

    def test_search_story(self):
        matching = OrganizationFactory.create(
            name='Foo',
            story=json.dumps({'html': '<p>We plant trees in the rainforest</p>', 'delta': ''})
        )
        OrganizationFactory.create(name='Bar', slogan='Something else')

        self.search('rainforest')
        self.assertFound([matching])

    def test_search_ranks_name_first(self):
        in_slogan = OrganizationFactory.create(name='Foo', slogan='We love kittens')
        in_name = OrganizationFactory.create(name='Kittens united', slogan='Something else')

        self.search('kittens')
        self.assertFound([in_slogan, in_name])
        self.assertEqual(self.data['data'][0]['id'], str(in_name.pk))

    def test_search_no_match(self):
        OrganizationFactory.create(name='Red Cross')

        self.search('nonexistent')
        self.assertFound([])

    def test_search_empty(self):
        organizations = OrganizationFactory.create_batch(2)

        self.search('')
        self.assertFound(organizations)

    def test_sort_default_created_descending(self):
        newest = OrganizationFactory.create(created=now() - timedelta(days=1))
        oldest = OrganizationFactory.create(created=now() - timedelta(days=10))
        middle = OrganizationFactory.create(created=now() - timedelta(days=5))

        self.search()
        self.assertEqual(
            [item['id'] for item in self.data['data']],
            [str(newest.pk), str(middle.pk), str(oldest.pk)]
        )

    def test_sort_created(self):
        newest = OrganizationFactory.create(created=now() - timedelta(days=1))
        oldest = OrganizationFactory.create(created=now() - timedelta(days=10))
        middle = OrganizationFactory.create(created=now() - timedelta(days=5))

        self.search(sort='created')
        self.assertEqual(
            [item['id'] for item in self.data['data']],
            [str(oldest.pk), str(middle.pk), str(newest.pk)]
        )

    def test_sort_created_descending(self):
        newest = OrganizationFactory.create(created=now() - timedelta(days=1))
        oldest = OrganizationFactory.create(created=now() - timedelta(days=10))
        middle = OrganizationFactory.create(created=now() - timedelta(days=5))

        self.search(sort='-created')
        self.assertEqual(
            [item['id'] for item in self.data['data']],
            [str(newest.pk), str(middle.pk), str(oldest.pk)]
        )

    def test_sort_unknown_falls_back_to_default(self):
        newest = OrganizationFactory.create(created=now() - timedelta(days=1))
        oldest = OrganizationFactory.create(created=now() - timedelta(days=10))

        self.search(sort='foo')
        self.assertEqual(
            [item['id'] for item in self.data['data']],
            [str(newest.pk), str(oldest.pk)]
        )

    # Pagination

    def test_pagination(self):
        organizations = OrganizationFactory.create_batch(10)

        self.search()
        self.assertEqual(self.data['meta']['pagination']['count'], 10)
        self.assertEqual(self.data['meta']['pagination']['pages'], 2)
        self.assertEqual(len(self.data['data']), 8)
        self.assertIsNotNone(self.data['links']['next'])

        first_page = set(item['id'] for item in self.data['data'])

        self.search(**{'page[number]': 2})
        self.assertEqual(len(self.data['data']), 2)
        self.assertIsNone(self.data['links']['next'])

        second_page = set(item['id'] for item in self.data['data'])

        self.assertFalse(first_page & second_page)
        self.assertEqual(
            first_page | second_page,
            set(str(organization.pk) for organization in organizations)
        )

    def test_pagination_with_search(self):
        matching = OrganizationFactory.create_batch(9, slogan='Saving the oceans')
        OrganizationFactory.create_batch(3, slogan='Something else')

        self.search('oceans')
        self.assertEqual(self.data['meta']['pagination']['count'], len(matching))
        self.assertEqual(len(self.data['data']), 8)

    def test_facets_empty(self):
        OrganizationFactory.create()

        self.search()
        self.assertEqual(self.data['meta']['facets'], {})
