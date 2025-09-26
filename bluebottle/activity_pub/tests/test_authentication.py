from django.test import RequestFactory

from bluebottle.activity_pub.authentication import (
    HTTPSignatureAuthentication
)

from bluebottle.activity_pub.tests.utils import SignedRequestFactory
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.activity_pub.tests.factories import OrganizationFactory


class JSONLdAuthenticationTestCase(BluebottleTestCase):
    def setUp(self):
        self.actor = OrganizationFactory.create(iri='https://example.com')
        self.request_factory = SignedRequestFactory(self.actor.iri)
        self.authentication = HTTPSignatureAuthentication()

    def test_signed_get(self):
        request = self.request_factory.get(path='/')

        (_, actor) = self.authentication.authenticate(request)
        self.assertEqual(actor, self.actor)

    def test_signed_post(self):
        request = self.request_factory.post(path='/', data={'id': 'test-id'})

        (_, actor) = self.authentication.authenticate(request)

        self.assertEqual(actor, self.actor)

    def test_signed_post_different_url(self):
        self.request_factory.override(path='/some-url')

        request = self.request_factory.post(path='/', data={'id': 'test-id'})
        result = self.authentication.authenticate(request)

        self.assertIsNone(result)

    def test_unsigned(self):
        request = RequestFactory().post(path='/', data={'id': 'test-id'})
        result = self.authentication.authenticate(request)

        self.assertIsNone(result)

    def test_unknown_key(self):
        request = self.request_factory.post(path='', data={'id': 'test-id'})
        self.actor.delete()

        result = self.authentication.authenticate(request)

        self.assertIsNone(result)
