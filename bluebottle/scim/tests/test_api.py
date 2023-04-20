from future import standard_library
standard_library.install_aliases()

import factory

from urllib.parse import urlencode
from builtins import object

from django.contrib.auth.models import Group
from django.core import mail
from django.urls import reverse
from django.test.utils import override_settings

from bluebottle.members.models import Member
from bluebottle.test.factory_models.geo import LocationFactory
from bluebottle.scim.models import SCIMPlatformSettings, SCIMSegmentSetting
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.segments.tests.factories import SegmentTypeFactory, SegmentFactory


class SCIMEndpointTestCaseMixin(object):
    def setUp(self):
        self.token = 'Bearer {}'.format(
            SCIMPlatformSettings.objects.get().bearer_token
        )
        super(SCIMEndpointTestCaseMixin, self).setUp()


class AuthenticatedSCIMEndpointTestCaseMixin(object):
    def setUp(self):
        self.token = 'Bearer {}'.format(
            SCIMPlatformSettings.objects.get().bearer_token
        )
        super(AuthenticatedSCIMEndpointTestCaseMixin, self).setUp()

    def test_get_no_authentication(self):
        """
        Test unauthenticated request
        """
        response = self.client.get(self.url)
        data = response.data

        self.assertEqual(response.status_code, 401)
        self.assertEqual(data['status'], 401)
        self.assertTrue('details' in data)
        self.assertEqual(data['schemas'], ['urn:ietf:params:scim:api:messages:2.0:Error'])

    def test_get_incorrect_token(self):
        """
        Test incorrectly authenticated request
        """
        response = self.client.get(
            self.url,
            token='Bearer blibli'
        )
        data = response.data

        self.assertEqual(response.status_code, 401)
        self.assertEqual(data['status'], 401)
        self.assertTrue('details' in data)
        self.assertEqual(data['schemas'], ['urn:ietf:params:scim:api:messages:2.0:Error'])

    def test_get_user_token(self):
        """
        Test authenticated with user token request
        """
        user = BlueBottleUserFactory.create()
        response = self.client.get(
            self.url,
            token="JWT {0}".format(user.get_jwt_token())
        )
        data = response.data

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(data['status'], 401)
        self.assertTrue('details' in data)
        self.assertEqual(data['schemas'], ['urn:ietf:params:scim:api:messages:2.0:Error'])


class SCIMServiceProviderConfigViewTest(SCIMEndpointTestCaseMixin, BluebottleTestCase):
    @property
    def url(self):
        return reverse('scim-service-provider-config')

    def test_get(self):
        """
        Test authenticated request
        """
        response = self.client.get(
            self.url,
            token=self.token
        )

        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            data['bulk']['supported'], False
        )
        self.assertEqual(
            data['filter']['supported'], False
        )
        self.assertEqual(
            data['etag']['supported'], False
        )
        self.assertEqual(
            data['sort']['supported'], False
        )
        self.assertEqual(
            data['patch']['supported'], False
        )
        self.assertEqual(
            data['changePassword']['supported'], False
        )
        self.assertEqual(
            data['schemas'],
            ['urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig']
        )
        self.assertEqual(
            len(data['authenticationSchemes']), 1
        )
        self.assertEqual(
            data['authenticationSchemes'][0]['type'],
            'oauthbearertoken'
        )

    def test_get_unauthenticated(self):
        """
        Test authenticated request
        """
        response = self.client.get(
            self.url,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)


class SCIMSchemaListTest(AuthenticatedSCIMEndpointTestCaseMixin, BluebottleTestCase):
    @property
    def url(self):
        return reverse('scim-schema-list')

    def test_get(self):
        """
        Test authenticated request
        """
        response = self.client.get(
            self.url,
            token=self.token
        )

        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['totalResults'], 6)
        self.assertEqual(data['startIndex'], 1)
        self.assertEqual(data['itemsPerPage'], 1000)
        self.assertEqual(
            data['schemas'],
            ['urn:ietf:params:scim:api:messages:2.0:ListResponse']
        )
        self.assertEqual(
            {resource['id'] for resource in data['Resources']},
            {
                'urn:ietf:params:scim:schemas:core:2.0:Schema',
                'urn:ietf:params:scim:schemas:core:2.0:ResourceType',
                'urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig',
                'urn:ietf:params:scim:schemas:core:2.0:Group',
                'urn:ietf:params:scim:schemas:core:2.0:User',
                'urn:ietf:params:scim:schemas:extension:enterprise:2.0:User',
            }
        )


class SCIMSchemaDetailTest(AuthenticatedSCIMEndpointTestCaseMixin, BluebottleTestCase):
    schema_id = 'urn:ietf:params:scim:schemas:core:2.0:Schema'

    @property
    def url(self):
        return reverse('scim-schema-detail', args=(self.schema_id,))

    def test_get(self):
        """
        Test authenticated request
        """
        response = self.client.get(
            self.url,
            token=self.token
        )

        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['id'], self.schema_id)

    def test_get_unknown(self):
        """
        Test authenticated request
        """
        url = reverse('scim-schema-detail', args=(self.schema_id + ':something',))
        response = self.client.get(
            url,
            token=self.token
        )
        data = response.data
        self.assertEqual(response.status_code, 404)

        self.assertEqual(data['status'], 404)
        self.assertEqual(
            data['details'],
            'Resource not found: urn:ietf:params:scim:schemas:core:2.0:Schema:something'
        )
        self.assertEqual(data['schemas'], ['urn:ietf:params:scim:api:messages:2.0:Error'])


class SCIMResourceTypeListTest(AuthenticatedSCIMEndpointTestCaseMixin, BluebottleTestCase):
    @property
    def url(self):
        return reverse('scim-resource-type-list')

    def test_get(self):
        """
        Test authenticated request
        """
        response = self.client.get(
            self.url,
            token=self.token
        )

        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['totalResults'], 2)
        self.assertEqual(data['startIndex'], 1)
        self.assertEqual(data['itemsPerPage'], 1000)
        self.assertEqual(
            data['schemas'],
            ['urn:ietf:params:scim:api:messages:2.0:ListResponse']
        )
        self.assertEqual(
            {resource['id'] for resource in data['Resources']},
            {'Group', 'User'}
        )


class SCIMResourceTypeDetailTest(AuthenticatedSCIMEndpointTestCaseMixin, BluebottleTestCase):
    @property
    def url(self):
        return reverse('scim-resource-type-detail', args=('User',))

    def test_get(self):
        """
        Test authenticated request
        """
        response = self.client.get(
            self.url,
            token=self.token
        )

        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['id'], 'User')
        self.assertEqual(
            data['schemas'], ['urn:ietf:params:scim:schemas:core:2.0:ResourceType']
        )

    def test_get_unknown(self):
        """
        Test authenticated request
        """
        url = reverse('scim-resource-type-detail', args=('SomethingElse',))
        response = self.client.get(
            url,
            token=self.token
        )
        self.assertEqual(response.status_code, 404)


class SCIMUserFactory(BlueBottleUserFactory):
    remote_id = factory.Faker('uuid4')
    scim_external_id = factory.Faker('uuid4')


class SCIMUserListTest(AuthenticatedSCIMEndpointTestCaseMixin, BluebottleTestCase):
    @property
    def url(self):
        return reverse('scim-user-list')

    def setUp(self):
        self.users = SCIMUserFactory.create_batch(10, is_superuser=False)

        super(SCIMUserListTest, self).setUp()

    def test_get(self):
        """
        Test authenticated request
        """
        response = self.client.get(
            self.url,
            token=self.token
        )

        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['totalResults'], 10)
        self.assertEqual(data['startIndex'], 1)
        self.assertEqual(data['itemsPerPage'], 1000)
        self.assertEqual(
            data['schemas'],
            ['urn:ietf:params:scim:api:messages:2.0:ListResponse']
        )

        first = data['Resources'][0]
        user = Member.objects.get(remote_id=first['userName'])

        self.assertEqual(user.scim_external_id, first['externalId'])
        self.assertEqual(user.first_name, first['name']['givenName'])
        self.assertEqual(user.last_name, first['name']['familyName'])
        self.assertEqual(user.email, first['emails'][0]['value'])
        self.assertEqual(first['active'], True)
        self.assertEqual(first['schemas'], ['urn:ietf:params:scim:schemas:core:2.0:User'])

    def test_get_filtered(self):
        response = self.client.get(
            self.url + f"?filter=userName eq {self.users[0].remote_id}",
            token=self.token
        )
        data = response.json()
        self.assertEqual(data['totalResults'], 1)
        self.assertEqual(data['startIndex'], 1)

    def test_get_invalid_filter(self):
        response = self.client.get(
            self.url + f"?filter=userName ge {self.users[0].remote_id}",
            token=self.token
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.get(
            self.url + f"?filter=somefield eq {self.users[0].remote_id}",
            token=self.token
        )
        self.assertEqual(response.status_code, 400)

    def test_get_paged(self):
        params = urlencode({
            'count': 8,
            'startIndex': 1
        })

        response = self.client.get(
            '{}?{}'.format(self.url, params),
            token=self.token
        )
        data = response.data
        self.assertEqual(data['totalResults'], 10)
        self.assertEqual(data['startIndex'], 1)
        self.assertEqual(len(data['Resources']), 8)

    def test_get_next_page(self):
        params = urlencode({
            'count': 8,
            'startIndex': 9
        })

        response = self.client.get(
            '{}?{}'.format(self.url, params),
            token=self.token
        )
        data = response.data
        self.assertEqual(data['totalResults'], 10)
        self.assertEqual(data['startIndex'], 9)
        self.assertEqual(len(data['Resources']), 2)

    def test_get_page_to_far(self):
        params = urlencode({
            'count': 8,
            'startIndex': 12
        })

        response = self.client.get(
            '{}?{}'.format(self.url, params),
            token=self.token
        )
        data = response.data
        self.assertEqual(data['totalResults'], 10)
        self.assertEqual(data['startIndex'], 12)
        self.assertEqual(len(data['Resources']), 0)

    @override_settings(SEND_WELCOME_MAIL=True)
    def test_post(self):
        """
        Test authenticated request
        """
        data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'externalId': '123',
            'username': 'some-id-for-smal',
            'active': True,
            'emails': [{
                'type': 'work',
                'primary': True,
                'value': 'test@example.com'
            }],
            'name': {
                'givenName': 'Tester',
                'familyName': 'Example'
            }
        }

        response = self.client.post(
            self.url,
            data,
            token=self.token
        )

        data = response.data
        self.assertEqual(response.status_code, 201)
        user = Member.objects.get(pk=data['id'].replace('goodup-user-', ''))

        self.assertEqual(user.email, data['emails'][0]['value'])
        self.assertEqual(user.scim_external_id, data['externalId'])
        self.assertEqual(user.remote_id, data['userName'])
        self.assertEqual(user.is_active, data['active'])
        self.assertEqual(user.first_name, data['name']['givenName'])
        self.assertEqual(user.last_name, data['name']['familyName'])
        self.assertEqual(
            data['schemas'], ['urn:ietf:params:scim:schemas:core:2.0:User']
        )
        self.assertEqual(data['meta']['resourceType'], 'User')
        self.assertEqual(
            data['meta']['location'],
            reverse('scim-user-detail', args=(user.pk, ))
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_post_empty_email(self):
        """
        Test authenticated request
        """
        data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'externalId': '123',
            'active': True,
            'emails': [{
                'type': 'work',
                'primary': True,
                'value': ''
            }],
            'name': {
                'givenName': 'Tester',
                'familyName': 'Example'
            }
        }

        response = self.client.post(
            self.url,
            data,
            token=self.token
        )

        data = response.data
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            data['details'],
            'emails: This field may not be blank.'
        )
        self.assertEqual(data['schemas'], ['urn:ietf:params:scim:api:messages:2.0:Error'])

    def test_post_missing_remote_id(self):
        """
        Test authenticated request
        """
        data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'active': True,
            'emails': [{
                'type': 'work',
                'primary': True,
                'value': 'test@example.com'
            }],
            'name': {
                'givenName': 'Tester',
                'familyName': 'Example'
            }
        }

        response = self.client.post(
            self.url,
            data,
            token=self.token
        )

        data = response.data
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            data['details'],
            'externalId: This field is required.'
        )
        self.assertEqual(data['schemas'], ['urn:ietf:params:scim:api:messages:2.0:Error'])

    @override_settings(SEND_WELCOME_MAIL=True)
    def test_post_existing(self):
        """
        Test creating a user twice request
        """
        data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'externalId': '123',
            'userName': '123',
            'active': True,
            'emails': [{
                'type': 'work',
                'primary': True,
                'value': 'test@example.com'
            }],
            'name': {
                'givenName': 'Tester',
                'familyName': 'Example'
            }
        }

        self.client.post(
            self.url,
            data,
            token=self.token
        )
        response = self.client.post(
            self.url,
            data,
            token=self.token
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['status'], 409)
        self.assertEqual(response.data['scimType'], 'uniqueness')
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(SEND_WELCOME_MAIL=True)
    def test_post_existing_remote_id(self):
        """
        Test creating a user twice request
        """
        remote_id = '123'
        BlueBottleUserFactory.create(remote_id=remote_id, scim_external_id='some-id')
        mail.outbox = []

        data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'active': True,
            'userName': remote_id,
            'externalId': 'some-external-id',
            'emails': [{
                'type': 'work',
                'primary': True,
                'value': 'test@example.com'
            }],
            'name': {
                'givenName': 'Tester',
                'familyName': 'Example'
            }
        }

        response = self.client.post(
            self.url,
            data,
            token=self.token
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['status'], 409)
        self.assertEqual(response.data['scimType'], 'uniqueness')
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(SEND_WELCOME_MAIL=True)
    def test_post_existing_remote_id_without_external_id(self):
        """
        Test creating a user twice request
        """
        remote_id = '123'
        user = BlueBottleUserFactory.create(
            email='test@example.com', remote_id=remote_id, scim_external_id=None
        )

        data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'active': True,
            'userName': remote_id,
            'externalId': 'some-external-id',
            'emails': [{
                'type': 'work',
                'primary': True,
                'value': 'test@example.com'
            }],
            'name': {
                'givenName': 'Tester',
                'familyName': 'Example'
            }
        }

        response = self.client.post(
            self.url,
            data,
            token=self.token
        )

        self.assertEqual(response.status_code, 201)

        user.refresh_from_db()
        self.assertEqual(user.scim_external_id, data['externalId'])
        self.assertEqual(user.email, data['emails'][0]['value'])
        self.assertEqual(user.first_name, data['name']['givenName'])
        self.assertEqual(user.last_name, data['name']['familyName'])

    def test_post_location(self):
        """
        Create a user with a location
        """
        location = LocationFactory.create(name='test location!', slug='test-location')
        data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'active': True,
            'userName': '123',
            'externalId': 'some-external-id',
            'addresses': [{
                'type': 'work',
                'locality': location.name,
            }],
            'emails': [{
                'type': 'work',
                'primary': True,
                'value': 'test@example.com'
            }],
            'name': {
                'givenName': 'Tester',
                'familyName': 'Example'
            }
        }

        response = self.client.post(
            self.url,
            data,
            token=self.token
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(response.json()['addresses'][0]['locality'], location.name)
        user = Member.objects.get(pk=response.json()['id'].replace('goodup-user-', ''))
        self.assertEqual(user.location, location)

    def test_post_new_location(self):
        """
        Create a user with a location that does not exist yet.
        """
        location_name = 'New test location'
        data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'active': True,
            'userName': '123',
            'externalId': 'some-external-id',
            'addresses': [{
                'type': 'work',
                'locality': location_name,
            }],
            'emails': [{
                'type': 'work',
                'primary': True,
                'value': 'test@example.com'
            }],
            'name': {
                'givenName': 'Tester',
                'familyName': 'Example'
            }
        }

        response = self.client.post(
            self.url,
            data,
            token=self.token
        )
        self.assertEqual(response.status_code, 201)

        self.assertEqual(response.json()['addresses'][0]['locality'], location_name)
        user = Member.objects.get(pk=response.json()['id'].replace('goodup-user-', ''))
        self.assertEqual(user.location.name, location_name)

    def test_post_segment(self):
        """
        Create a user with a location that does not exist yet.
        """
        department = SegmentTypeFactory.create(name="Department", slug="department")

        SCIMSegmentSetting.objects.create(
            path='urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:department',
            segment_type=department
        )

        country = SegmentTypeFactory.create(name='Country', slug='country')
        SCIMSegmentSetting.objects.create(
            path='addresses[type eq "work"].country',
            segment_type=country
        )
        country_name = 'NL'
        department_name = 'Engineering'

        data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'active': True,
            'userName': '123',
            'externalId': 'some-external-id',
            'emails': [{
                'type': 'work',
                'primary': True,
                'value': 'test@example.com'
            }],
            'name': {
                'givenName': 'Tester',
                'familyName': 'Example'
            },
            'addresses': [
                {'country': 'NL', 'type': 'work'}
            ],
            'urn:ietf:params:scim:schemas:extension:enterprise:2.0:User': {
                'department': department_name
            }
        }

        response = self.client.post(
            self.url,
            data,
            token=self.token
        )
        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            response.json()['urn:ietf:params:scim:schemas:extension:enterprise:2.0:User']['department'],
            department_name
        )

        self.assertEqual(
            response.json()['addresses'][0]['country'],
            country_name
        )
        user = Member.objects.get(pk=response.json()['id'].replace('goodup-user-', ''))
        self.assertEqual(user.segments.get(segment_type=department).name, department_name)
        self.assertEqual(user.segments.get(segment_type=country).name, country_name)


class SCIMUserDetailTest(AuthenticatedSCIMEndpointTestCaseMixin, BluebottleTestCase):
    @property
    def url(self):
        return reverse('scim-user-detail', args=(self.user.pk, ))

    def setUp(self):
        self.user = BlueBottleUserFactory.create(is_superuser=False)
        self.user.remote_id = '1243'
        self.user.scim_external_id = '1243'
        self.user.save()
        self.user.groups.add(Group.objects.get(name='Staff'))

        super(SCIMUserDetailTest, self).setUp()

    def test_get(self):
        """
        Test authenticated request
        """
        response = self.client.get(
            self.url,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data['id'], 'goodup-user-{}'.format(self.user.pk))
        self.assertEqual(data['name']['givenName'], self.user.first_name)
        self.assertEqual(data['name']['familyName'], self.user.last_name)
        self.assertEqual(data['active'], True)
        self.assertEqual(len(data['emails']), 1)
        self.assertEqual(data['emails'][0]['value'], self.user.email)
        self.assertEqual(data['emails'][0]['primary'], True)
        self.assertEqual(data['emails'][0]['type'], 'work')
        self.assertEqual(data['addresses'], [])
        self.assertEqual(
            data['schemas'], ['urn:ietf:params:scim:schemas:core:2.0:User']
        )
        self.assertEqual(data['meta']['resourceType'], 'User')
        self.assertEqual(
            data['meta']['location'],
            reverse('scim-user-detail', args=(self.user.pk, ))
        )
        self.assertEqual(
            len(data['groups']), 1
        )
        group = data['groups'][0]
        self.assertEqual(group['id'], 'goodup-group-{}'.format(Group.objects.get(name='Staff').pk))

    def test_get_segments(self):
        """
        Test authenticated request
        """
        segment_type = SegmentTypeFactory.create(name="Department", slug="department")
        segment = SegmentFactory.create(segment_type=segment_type)

        SCIMSegmentSetting.objects.create(
            path='urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:department',
            segment_type=segment_type
        )
        self.user.segments.add(segment)

        response = self.client.get(
            self.url,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(
            data['urn:ietf:params:scim:schemas:extension:enterprise:2.0:User']['department'],
            segment.name
        )

    def test_put(self):
        """
        Test authenticated put request
        """
        request_data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'id': 'goodup-user-{}'.format(self.user.pk),
            'userName': self.user.remote_id,
            'externalId': '123',
            'active': False,
            'emails': [{
                'type': 'work',
                'primary': True,
                'value': 'OostrumA@delagelanden.com'
            }],
            'name': {
                'givenName': 'Tester',
                'familyName': 'Example'
            }
        }

        response = self.client.put(
            self.url,
            request_data,
            token=self.token
        )
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data['id'], request_data['id'])
        self.assertEqual(data['active'], False)
        self.assertEqual(data['name']['givenName'], request_data['name']['givenName'])
        self.assertEqual(data['name']['familyName'], request_data['name']['familyName'])
        self.assertEqual(len(data['emails']), 1)
        self.assertEqual(data['emails'][0]['value'], request_data['emails'][0]['value'])

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, request_data['name']['givenName'])
        self.assertEqual(self.user.last_name, request_data['name']['familyName'])
        self.assertEqual(self.user.email, request_data['emails'][0]['value'])
        self.assertEqual(len(mail.outbox), 0)

    def test_put_location(self):
        """
        Test authenticated put request
        """
        location = LocationFactory.create()
        request_data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'id': 'goodup-user-{}'.format(self.user.pk),
            'userName': self.user.remote_id,
            'externalId': '123',
            'active': False,
            'emails': [{
                'type': 'work',
                'primary': True,
                'value': self.user.email
            }],
            'name': {
                'givenName': self.user.first_name,
                'familyName': self.user.first_name
            },
            'addresses': [{
                'type': 'work',
                'locality': location.name
            }],
        }

        response = self.client.put(
            self.url,
            request_data,
            token=self.token
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['addresses'][0]['locality'], location.name)
        self.user.refresh_from_db()
        self.assertEqual(self.user.location, location)

    def test_put_new_location(self):
        """
        Test authenticated put request
        """
        location_name = 'Test Location'
        request_data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'id': 'goodup-user-{}'.format(self.user.pk),
            'userName': self.user.remote_id,
            'externalId': '123',
            'active': False,
            'emails': [{
                'type': 'work',
                'primary': True,
                'value': self.user.email
            }],
            'name': {
                'givenName': self.user.first_name,
                'familyName': self.user.first_name
            },
            'addresses': [{
                'type': 'work',
                'locality': location_name
            }],
        }

        response = self.client.put(
            self.url,
            request_data,
            token=self.token
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['addresses'][0]['locality'], location_name)
        self.user.refresh_from_db()
        self.assertEqual(self.user.location.name, location_name)

    def test_put_deleted(self):
        """
        Test authenticated put request
        """
        request_data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'id': 'goodup-user-{}'.format(self.user.pk),
            'userName': self.user.remote_id,
            'externalId': '123',
            'active': False,
            'emails': [{
                'type': 'work',
                'primary': True,
                'value': 'test@example.com'
            }],
            'name': {
                'givenName': 'Tester',
                'familyName': 'Example'
            }
        }
        url = self.url
        self.user.delete()

        response = self.client.put(
            url,
            request_data,
            token=self.token
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['status'], 404)
        self.assertEqual(response.json()['schemas'], ['urn:ietf:params:scim:api:messages:2.0:Error'])

    def test_patch(self):
        request_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "Replace",
                    "path": "name.givenName",
                    "value": "Tester"
                },
                {
                    "op": "Replace",
                    "path": "name.familyName",
                    "value": "Example"
                },
                {
                    "op": "Add",
                    "path": 'emails[type eq "work"].value',
                    "value": 'test@example.com'
                }
            ]
        }

        response = self.client.patch(
            self.url,
            request_data,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.user.refresh_from_db()
        self.assertEqual(data['emails'][0]['value'], 'test@example.com')
        self.assertEqual(data['name']['givenName'], 'Tester')
        self.assertEqual(data['name']['familyName'], 'Example')

        self.assertEqual(self.user.first_name, 'Tester')
        self.assertEqual(self.user.last_name, 'Example')
        self.assertEqual(self.user.email, 'test@example.com')

    def test_patch_segment(self):
        department = SegmentTypeFactory.create(name='Department', slug='department')

        SCIMSegmentSetting.objects.create(
            path='urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:department',
            segment_type=department
        )
        country = SegmentTypeFactory.create(name='Country', slug='country')
        SCIMSegmentSetting.objects.create(
            path='addresses[type eq "work"].country',
            segment_type=country
        )

        request_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "Add",
                    "path": 'urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:department',
                    "value": 'Engineering'
                },

                {
                    "op": "Add",
                    "path": 'addresses[type eq "work"].country',
                    "value": 'NL'
                },

            ]
        }

        response = self.client.patch(
            self.url,
            request_data,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.user.refresh_from_db()
        segment = self.user.segments.get(segment_type=department)
        self.assertEqual(segment.name, 'Engineering')

        self.assertEqual(
            data['urn:ietf:params:scim:schemas:extension:enterprise:2.0:User']['department'],
            segment.name
        )
        self.assertEqual(
            data['addresses'][0]['country'],
            'NL'
        )

    def test_patch_deactivate(self):
        request_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "Replace",
                    "path": "active",
                    "value": "False"
                },
            ]
        }

        response = self.client.patch(
            self.url,
            request_data,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.is_active, False)

    def test_patch_location(self):
        location = LocationFactory.create()
        request_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    'op': 'Add',
                    'path': 'addresses[type eq "work"].locality',
                    'value': location.name
                },
            ]
        }

        response = self.client.patch(
            self.url,
            request_data,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['addresses'][0]['locality'], location.name)

        self.user.refresh_from_db()
        self.assertEqual(self.user.location, location)

    def test_patch_new_location(self):
        location_name = 'Test Location'
        request_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{
                "op": "Add",
                "path": 'addresses[type eq \\"work\\"].locality',
                "value": "Test Location"
            }, {
                "op": "Add",
                "path": 'addresses[type eq \\"work\\"].country',
                "value": "Netherlands"
            }]
        }
        response = self.client.patch(
            self.url,
            request_data,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['addresses'][0]['locality'], location_name)

        self.user.refresh_from_db()
        self.assertEqual(self.user.location.name, location_name)

    def test_delete(self):
        response = self.client.delete(
            self.url,
            token=self.token
        )

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.user.is_active, False)
        self.assertEqual(self.user.is_anonymized, True)
        self.assertEqual(self.user.first_name, 'Deactivated')

        response = self.client.get(
            self.url,
            token=self.token
        )

        self.assertEqual(response.status_code, 404)


class SCIMGroupListTest(AuthenticatedSCIMEndpointTestCaseMixin, BluebottleTestCase):
    @property
    def url(self):
        return reverse('scim-group-list')

    def test_get(self):
        """
        Test authenticated request
        """
        response = self.client.get(
            self.url,
            token=self.token
        )

        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['totalResults'], 2)
        self.assertEqual(data['startIndex'], 1)
        self.assertEqual(data['itemsPerPage'], 1000)
        self.assertEqual(
            data['schemas'],
            ['urn:ietf:params:scim:api:messages:2.0:ListResponse']
        )

    def test_post(self):
        """
        Test authenticated request
        """
        response = self.client.post(
            self.url,
            token=self.token
        )
        self.assertEqual(response.status_code, 405)


class SCIMGroupDetailTest(AuthenticatedSCIMEndpointTestCaseMixin, BluebottleTestCase):
    @property
    def url(self):
        return reverse('scim-group-detail', args=(self.group.pk, ))

    def setUp(self):
        self.group = Group.objects.create(name='test')
        self.user = BlueBottleUserFactory.create()
        self.user.groups.add(self.group)

        super(SCIMGroupDetailTest, self).setUp()

    def test_get(self):
        """
        Test authenticated request
        """
        response = self.client.get(
            self.url,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data['id'], 'goodup-group-{}'.format(self.group.id))
        self.assertEqual(data['displayName'], self.group.name)
        self.assertEqual(len(data['members']), 1)
        self.assertEqual(data['members'][0]['value'], 'goodup-user-{}'.format(self.user.pk))
        self.assertEqual(
            data['members'][0]['$ref'],
            reverse('scim-user-detail', args=(self.user.pk, ))
        )
        self.assertEqual(
            data['members'][0]['type'], 'User'
        )

    def test_put_add_to_group(self):
        new_user = BlueBottleUserFactory.create()
        request_data = {
            'id': 'goodup-group-{}'.format(self.group.pk),
            'displayName': self.group.name,
            'members': [
                {'value': 'goodup-user-{}'.format(self.user.pk)},
                {'value': 'goodup-user-{}'.format(new_user.pk)},
            ]
        }
        response = self.client.put(
            self.url,
            data=request_data,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data['members']), 2)
        self.assertTrue(
            self.group in new_user.groups.all()
        )
        self.assertFalse(new_user.is_staff)

    def test_put_add_to_staff(self):
        new_user = BlueBottleUserFactory.create()
        group = Group.objects.get(name='Staff')
        url = reverse('scim-group-detail', args=(group.pk, ))
        request_data = {
            'id': 'goodup-group-{}'.format(group.pk),
            'displayName': group.name,
            'members': [
                {'value': 'goodup-user-{}'.format(new_user.pk)},
            ]
        }
        response = self.client.put(
            url,
            data=request_data,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data['members']), 1)
        self.assertTrue(
            group in new_user.groups.all()
        )
        new_user.refresh_from_db()
        self.assertTrue(new_user.is_staff)

    def test_missing_members_are_removed(self):
        request_data = {
            'id': 'goodup-group-{}'.format(self.group.pk),
            'displayName': self.group.name,
            'members': [],
        }
        response = self.client.put(
            self.url,
            data=request_data,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data['members']), 0)

    def test_add_non_existant_user(self):
        request_data = {
            'id': 'goodup-group-{}'.format(self.group.pk),
            'displayName': self.group.name,
            'members': [
                {'value': 1234},
            ],
        }
        response = self.client.put(
            self.url,
            data=request_data,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data['members']), 0)

    def test_add_incorrect_id(self):
        request_data = {
            'id': 'goodup-group-{}'.format(self.group.pk),
            'displayName': self.group.name,
            'members': [
                {'value': 'goodup-user-bla-bla-bla'},
            ],
        }
        response = self.client.put(
            self.url,
            data=request_data,
            token=self.token
        )

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data['members']), 0)

    def test_get_superuser(self):
        super_user = BlueBottleUserFactory.create(is_superuser=True)
        super_user.groups.add(self.group)
        response = self.client.get(
            self.url,
            token=self.token
        )
        self.assertEqual(len(response.data['members']), 1)
