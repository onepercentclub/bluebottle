import json

from rest_framework_json_api.renderers import JSONRenderer

from bluebottle.members.serializers import AuthenticationMethodSerializer
from bluebottle.members.tests.factories import (
    PasswordAuthenticationFactory, FacebookAuthenticationFactory,
    GoogleAuthenticationFactory, SAMLAuthenticationFactory
)
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.utils import BluebottleTestCase


class RendererContext:
    def get_serializer_class(self):
        return AuthenticationMethodSerializer


class AuthenticationMethodSerializerTestCase(BluebottleTestCase):
    def serialize(self, instance, many=False):
        data = AuthenticationMethodSerializer(instance, many=many).data
        return json.loads(
            JSONRenderer().render(data, renderer_context={'view': RendererContext()})
        )


class PasswordAuthenticationSerializerTestCase(AuthenticationMethodSerializerTestCase):
    def setUp(self):
        super().setUp()
        self.method = PasswordAuthenticationFactory.create(
            confirm_signup=True,
            account_creation_rules='whitelist_and_request',
            email_domains=['example.com', 'goodup.com'],
            request_access_method='instructions',
            request_access_instructions='Ask your manager',
            request_access_email='access@example.com',
            request_access_code='secret-code',
        )

    def test_render(self):
        result = self.serialize(self.method)

        self.assertEqual(set(result.keys()), {'data'})

        resource = result['data']
        self.assertEqual(resource['type'], 'authentication-methods/password')
        self.assertEqual(resource['id'], str(self.method.pk))
        self.assertEqual(resource['attributes']['confirm-signup'], True)
        self.assertEqual(resource['attributes']['account-creation-rules'], 'whitelist_and_request')
        self.assertEqual(resource['attributes']['email-domains'], ['example.com', 'goodup.com'])
        self.assertEqual(resource['attributes']['request-access-method'], 'instructions')
        self.assertEqual(resource['attributes']['request-access-instructions'], 'Ask your manager')
        self.assertNotIn('relationships', resource)
        self.assertNotIn('meta', resource)

        self.assertNotIn('secret-code', json.dumps(result))
        self.assertNotIn('access@example.com', json.dumps(result))


class FacebookAuthenticationSerializerTestCase(AuthenticationMethodSerializerTestCase):
    def setUp(self):
        super().setUp()
        self.method = FacebookAuthenticationFactory.create(client_id='fb-client-id', secret='fb-secret')

    def test_render(self):
        result = self.serialize(self.method)

        self.assertEqual(set(result.keys()), {'data'})

        resource = result['data']
        self.assertEqual(resource['type'], 'authentication-methods/facebook')
        self.assertEqual(resource['id'], str(self.method.pk))

        self.assertEqual(resource['attributes']['client-id'], 'fb-client-id')
        self.assertNotIn('relationships', resource)
        self.assertNotIn('meta', resource)
        self.assertNotIn('fb-secret', json.dumps(result))


class GoogleAuthenticationSerializerTestCase(AuthenticationMethodSerializerTestCase):
    def setUp(self):
        super().setUp()
        self.method = GoogleAuthenticationFactory.create(client_id='google-client-id', secret='google-secret')

    def test_render(self):
        result = self.serialize(self.method)

        self.assertEqual(set(result.keys()), {'data'})

        resource = result['data']
        self.assertEqual(resource['type'], 'authentication-methods/google')
        self.assertEqual(resource['id'], str(self.method.pk))
        self.assertEqual(resource['attributes']['client-id'], 'google-client-id')
        self.assertNotIn('relationships', resource)
        self.assertNotIn('meta', resource)
        self.assertNotIn('google-secret', json.dumps(result))


class SAMLAuthenticationSerializerTestCase(AuthenticationMethodSerializerTestCase):
    def setUp(self):
        super().setUp()
        self.organization = OrganizationFactory.create()
        self.method = SAMLAuthenticationFactory.create(
            organization=self.organization,
            admin_login_enabled=False,
        )

    def test_render(self):
        result = self.serialize(self.method)

        self.assertEqual(set(result.keys()), {'data', 'included'})

        resource = result['data']
        self.assertEqual(resource['type'], 'authentication-methods/saml')
        self.assertEqual(resource['id'], str(self.method.pk))

        self.assertEqual(resource['attributes']['admin-login-enabled'], False)
        self.assertEqual(resource['relationships']['organization']['data']['id'], str(self.method.organization.pk))
        self.assertEqual(resource['meta']['redirect-url'], self.method.redirect_url)

        self.assertEqual(
            [(resource['type'], resource['id']) for resource in result['included']],
            [('organizations', str(self.organization.pk))]
        )
