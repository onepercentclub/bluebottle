import re
from datetime import datetime, timezone
from bluebottle.members.models import PasswordAuthentication
from bluebottle.test.utils import BluebottleTestCase

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse

from bluebottle.members.models import SAMLAuthentication
from bluebottle.members.tests.factories import (
    IDP_CERTIFICATE, FacebookAuthenticationFactory, GoogleAuthenticationFactory,
    PasswordAuthenticationFactory, SAMLAuthenticationFactory
)
from bluebottle.test.factory_models.organizations import OrganizationFactory


class SingletonAuthenticationMethodTestMixin:
    factory = None

    def setUp(self):
        super().setUp()
        self.method = self.factory.create()

    @property
    def model(self):
        return self.factory._meta.model

    def test_create(self):
        self.assertEqual(self.model.objects.count(), 1)

    def test_create_second(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.model.objects.create()

        self.assertEqual(self.model.objects.count(), 1)

    def test_create_second_disabled(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.model.objects.create(enabled=False)

    def test_factory_updates_existing(self):
        method = self.factory.create(enabled=False)

        self.assertEqual(method.pk, self.method.pk)
        self.assertEqual(self.model.objects.count(), 1)
        self.method.refresh_from_db()
        self.assertFalse(self.method.enabled)

    def test_validate_second(self):
        with self.assertRaises(ValidationError):
            self.factory.build().full_clean()

    def test_update_existing(self):
        self.method.enabled = False
        self.method.full_clean()
        self.method.save()

        self.method.refresh_from_db()
        self.assertFalse(self.method.enabled)

    def test_create_after_delete(self):
        self.method.delete()
        self.factory.create()

        self.assertEqual(self.model.objects.count(), 1)


class PasswordAuthenticationTestCase(SingletonAuthenticationMethodTestMixin, BluebottleTestCase):
    factory = PasswordAuthenticationFactory

    def disable(self):
        self.method.enabled = False
        self.method.save()

    def test_load_enabled(self):
        self.assertEqual(PasswordAuthentication.load(), self.method)

    def test_load_returns_concrete_instance(self):
        self.assertIsInstance(PasswordAuthentication.load(), PasswordAuthentication)

    def test_load_disabled(self):
        self.disable()
        self.assertIsNone(PasswordAuthentication.load())

    def test_load_ignores_other_methods(self):
        self.method.delete()
        GoogleAuthenticationFactory.create()
        self.assertIsNone(PasswordAuthentication.load())

    def test_load_none(self):
        self.method.delete()
        self.assertIsNone(PasswordAuthentication.load())

    def test_is_enabled_none(self):
        self.method.delete()
        self.assertFalse(PasswordAuthentication.is_enabled())

    def test_is_enabled(self):
        self.assertTrue(PasswordAuthentication.is_enabled())

    def test_is_enabled_disabled(self):
        self.disable()
        self.assertFalse(PasswordAuthentication.is_enabled())

    def test_is_enabled_after_disabling(self):
        self.assertTrue(PasswordAuthentication.is_enabled())

        self.disable()
        self.assertFalse(PasswordAuthentication.is_enabled())

    def test_is_enabled_other_method(self):
        self.method.delete()
        GoogleAuthenticationFactory.create()
        self.assertFalse(PasswordAuthentication.is_enabled())

    def test_confirm_signup_enabled_none(self):
        self.method.delete()
        self.assertFalse(PasswordAuthentication.confirm_signup_enabled())

    def test_confirm_signup_enabled_default(self):
        self.assertFalse(PasswordAuthentication.confirm_signup_enabled())

    def test_confirm_signup_enabled(self):
        self.method.confirm_signup = True
        self.method.save()
        self.assertTrue(PasswordAuthentication.confirm_signup_enabled())

    def test_confirm_signup_enabled_method_disabled(self):
        self.method.confirm_signup = True
        self.disable()
        self.assertFalse(PasswordAuthentication.confirm_signup_enabled())


class FacebookAuthenticationTestCase(SingletonAuthenticationMethodTestMixin, BluebottleTestCase):
    factory = FacebookAuthenticationFactory


class GoogleAuthenticationTestCase(SingletonAuthenticationMethodTestMixin, BluebottleTestCase):
    factory = GoogleAuthenticationFactory


class SAMLAuthenticationTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.method = SAMLAuthenticationFactory.create()

    def test_parse(self):
        self.assertEqual(
            self.method.name_id_format, 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress'
        )
        self.assertTrue(
            re.match('https://idp\d+.example.com/sso', self.method.signon_url)
        )
        self.assertTrue(
            re.match('https://idp\d+.example.com', self.method.idp_entity_id)
        )

    def test_certificate(self):
        self.assertEqual(
            str(self.method.certificate.subject),
            '<Name(C=NO,ST=Andreas Solberg,L=Foo,O=UNINETT,CN=feide.erlang.no,1.2.840.113549.1.9.1=andreas@uninett.no)>'
        )
        self.assertEqual(
            self.method.certificate.not_valid_after_utc, datetime(2007, 8, 14, 12, 1, 35, tzinfo=timezone.utc)
        )

    def test_idp_metadata(self):
        entity_id = self.method.entity_id
        idp = self.method.idp_metadata['idp']

        self.assertEqual(idp['entityId'], entity_id)
        self.assertEqual(idp['x509cert'], IDP_CERTIFICATE)
        self.assertEqual(
            idp['singleSignOnService'],
            {
                'url': f'{entity_id}/sso',
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            }
        )
        self.assertEqual(
            idp['singleLogoutService'],
            {
                'url': f'{entity_id}/slo',
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            }
        )
        self.assertEqual(
            self.method.idp_metadata['sp']['NameIDFormat'],
            'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress'
        )

    def test_idp_metadata_cached(self):
        self.assertIs(self.method.idp_metadata, self.method.idp_metadata)

    def test_metadata(self):
        metadata = self.method.metadata

        self.assertEqual(metadata['idp'], self.method.idp_metadata['idp'])
        self.assertEqual(
            metadata['sp'],
            {
                'entityId': self.method.entity_id,
                'NameIDFormat': 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
                'assertionConsumerService': {
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
                    'url': reverse('token-auth:saml-login'),
                },
                'singleLogoutService': {
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
                    'url': reverse('token-auth:saml-logout'),
                },
            }
        )

    def test_settings(self):
        self.method.strict = True
        self.method.debug = True

        settings = self.method.settings

        self.assertTrue(settings['strict'])
        self.assertTrue(settings['debug'])
        self.assertEqual(settings['security'], {'requestedAuthnContext': False})
        self.assertEqual(settings['idp'], self.method.metadata['idp'])
        self.assertEqual(settings['sp'], self.method.metadata['sp'])

    def test_settings_defaults(self):
        settings = self.method.settings

        self.assertFalse(settings['strict'])
        self.assertFalse(settings['debug'])

    def test_create_multiple(self):
        SAMLAuthenticationFactory.create_batch(2)

        self.assertEqual(SAMLAuthentication.objects.count(), 3)

    def test_validate_second(self):
        second = SAMLAuthenticationFactory.build(organization=OrganizationFactory.create())

        try:
            second.full_clean()
        except ValidationError as error:
            self.fail(f'A second SAML authentication should be valid, got: {error.message_dict}')

        second.save()
        self.assertEqual(SAMLAuthentication.objects.count(), 2)

    def test_multiple_alongside_singletons(self):
        PasswordAuthenticationFactory.create()
        FacebookAuthenticationFactory.create()
        GoogleAuthenticationFactory.create()

        SAMLAuthenticationFactory.create()

        self.assertEqual(SAMLAuthentication.objects.count(), 2)
