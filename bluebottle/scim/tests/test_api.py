from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

from bluebottle.members.models import Member
from bluebottle.scim.models import SCIMPlatformSettings
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class SCIMEndpointTestCaseMixin(object):
    def setUp(self):
        self.token = 'Bearer {}'.format(
            SCIMPlatformSettings.objects.get().bearer_token
        )
        super(SCIMEndpointTestCaseMixin, self).setUp()

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


class SCIMSchemaListTest(SCIMEndpointTestCaseMixin, BluebottleTestCase):
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
        self.assertEqual(data['totalResults'], 5)
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
                'urn:ietf:params:scim:schemas:core:2.0:User'
            }
        )


class SCIMSchemaDetailTest(SCIMEndpointTestCaseMixin, BluebottleTestCase):
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


class SCIMResourceTypeListTest(SCIMEndpointTestCaseMixin, BluebottleTestCase):
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


class SCIMResourceTypeDetailTest(SCIMEndpointTestCaseMixin, BluebottleTestCase):
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


class SCIMUserListTest(SCIMEndpointTestCaseMixin, BluebottleTestCase):
    @property
    def url(self):
        return reverse('scim-user-list')

    def setUp(self):
        for i in range(9):
            BlueBottleUserFactory.create(is_superuser=False)

        super(SCIMUserListTest, self).setUp()

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
        self.assertEqual(data['totalResults'], 10)
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
        data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'externalId': '123',
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
        user = Member.objects.get(pk=data['id'])

        self.assertEqual(user.email, data['emails'][0]['value'])
        self.assertEqual(user.remote_id, data['externalId'])
        self.assertEqual(user.is_active, data['active'])
        self.assertEqual(user.first_name, data['name']['givenName'])
        self.assertEqual(user.last_name, data['name']['familyName'])
        self.assertEqual(
            data['schemas'], ['urn:ietf:params:scim:schemas:core:2.0:User']
        )
        self.assertEqual(data['meta']['resourceType'], 'User')
        self.assertEqual(
            data['meta']['location'],
            reverse('scim-user-detail', args=(user.id, ))
        )

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

    def test_post_existing(self):
        """
        Test creating a user twice request
        """
        data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'externalId': '123',
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

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['status'], 400)


class SCIMUserDetailTest(SCIMEndpointTestCaseMixin, BluebottleTestCase):
    @property
    def url(self):
        return reverse('scim-user-detail', args=(self.user.id, ))

    def setUp(self):
        self.user = BlueBottleUserFactory.create(is_superuser=False)
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

        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['name']['givenName'], self.user.first_name)
        self.assertEqual(data['name']['familyName'], self.user.last_name)
        self.assertEqual(data['active'], True)
        self.assertEqual(len(data['emails']), 1)
        self.assertEqual(data['emails'][0]['value'], self.user.email)
        self.assertEqual(data['emails'][0]['primary'], True)
        self.assertEqual(data['emails'][0]['type'], 'work')
        self.assertEqual(
            data['schemas'], ['urn:ietf:params:scim:schemas:core:2.0:User']
        )
        self.assertEqual(data['meta']['resourceType'], 'User')
        self.assertEqual(
            data['meta']['location'],
            reverse('scim-user-detail', args=(self.user.id, ))
        )
        self.assertEqual(
            len(data['groups']), 1
        )

    def test_put(self):
        """
        Test authenticated put request
        """
        request_data = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'],
            'id': self.user.id,
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

    def test_delete(self):
        response = self.client.delete(
            self.url,
            token=self.token
        )

        self.assertEqual(response.status_code, 204)
        self.assertRaises(
            Member.DoesNotExist,
            self.user.refresh_from_db
        )


class SCIMGroupListTest(SCIMEndpointTestCaseMixin, BluebottleTestCase):
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
        self.assertEqual(data['totalResults'], 3)
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


class SCIMGroupDetailTest(SCIMEndpointTestCaseMixin, BluebottleTestCase):
    @property
    def url(self):
        return reverse('scim-group-detail', args=(self.group.id, ))

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

        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['id'], self.group.id)
        self.assertEqual(data['displayName'], self.group.name)
        self.assertEqual(len(data['members']), 1)
        self.assertEqual(data['members'][0]['value'], self.user.pk)
        self.assertEqual(
            data['members'][0]['$ref'],
            reverse('scim-user-detail', args=(self.user.pk, ))
        )

    def test_put_add_to_group(self):
        new_user = BlueBottleUserFactory.create()
        request_data = {
            'id': self.group.pk,
            'displayName': self.group.name,
            'members': [
                {'value': self.user.pk},
                {'value': new_user.pk},
            ]
        }
        response = self.client.put(
            self.url,
            data=request_data,
            token=self.token
        )

        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['members']), 2)
        self.assertTrue(
            self.group in new_user.groups.all()
        )

    def test_missing_members_are_removed(self):
        request_data = {
            'id': self.group.pk,
            'displayName': self.group.name,
            'members': [],
        }
        response = self.client.put(
            self.url,
            data=request_data,
            token=self.token
        )

        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['members']), 0)

    def test_add_non_existant_user(self):
        request_data = {
            'id': self.group.pk,
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

        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['members']), 0)
