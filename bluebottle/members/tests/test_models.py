from bluebottle.members.models import GoogleAuthentication, PasswordAuthentication
from bluebottle.test.utils import BluebottleTestCase

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from bluebottle.members.models import SAMLAuthentication
from bluebottle.members.tests.factories import (
    FacebookAuthenticationFactory, GoogleAuthenticationFactory, PasswordAuthenticationFactory,
    SAMLAuthenticationFactory
)
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.utils import BluebottleTestCase


class SingletonAuthenticationMethodTestMixin:
    factory = None

    @property
    def model(self):
        return self.factory._meta.model

    def test_create(self):
        self.factory.create()
        self.assertEqual(self.model.objects.count(), 1)

    def test_create_second(self):
        self.factory.create()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.factory.create()

        self.assertEqual(self.model.objects.count(), 1)

    def test_create_second_disabled(self):
        self.factory.create()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.factory.create(enabled=False)

    def test_validate_second(self):
        self.factory.create()

        with self.assertRaises(ValidationError):
            self.factory.build().full_clean()

    def test_update_existing(self):
        method = self.factory.create()
        method.enabled = False
        method.full_clean()
        method.save()

        method.refresh_from_db()
        self.assertFalse(method.enabled)

    def test_create_after_delete(self):
        self.factory.create().delete()
        self.factory.create()

        self.assertEqual(self.model.objects.count(), 1)


class PasswordAuthenticationTestCase(SingletonAuthenticationMethodTestMixin, BluebottleTestCase):
    factory = PasswordAuthenticationFactory

    def test_load_enabled(self):
        method = PasswordAuthentication.objects.create()
        self.assertEqual(PasswordAuthentication.load(), method)

    def test_load_returns_concrete_instance(self):
        PasswordAuthentication.objects.create()
        self.assertIsInstance(PasswordAuthentication.load(), PasswordAuthentication)

    def test_load_disabled(self):
        PasswordAuthentication.objects.create(enabled=False)
        self.assertIsNone(PasswordAuthentication.load())

    def test_load_ignores_other_methods(self):
        GoogleAuthentication.objects.create(secret='secret', client_id='client-id')
        self.assertIsNone(PasswordAuthentication.load())

    def test_load_none(self):
        self.assertIsNone(PasswordAuthentication.load())

    def test_is_enabled_none(self):
        self.assertFalse(PasswordAuthentication.is_enabled())

    def test_is_enabled(self):
        PasswordAuthentication.objects.create()
        self.assertTrue(PasswordAuthentication.is_enabled())

    def test_is_enabled_disabled(self):
        PasswordAuthentication.objects.create(enabled=False)
        self.assertFalse(PasswordAuthentication.is_enabled())

    def test_is_enabled_after_disabling(self):
        method = PasswordAuthentication.objects.create()
        self.assertTrue(PasswordAuthentication.is_enabled())

        method.enabled = False
        method.save()
        self.assertFalse(PasswordAuthentication.is_enabled())

    def test_is_enabled_other_method(self):
        GoogleAuthentication.objects.create(secret='secret', client_id='client-id')
        self.assertFalse(PasswordAuthentication.is_enabled())

    def test_confirm_signup_enabled_none(self):
        self.assertFalse(PasswordAuthentication.confirm_signup_enabled())

    def test_confirm_signup_enabled_default(self):
        PasswordAuthentication.objects.create()
        self.assertFalse(PasswordAuthentication.confirm_signup_enabled())

    def test_confirm_signup_enabled(self):
        PasswordAuthentication.objects.create(confirm_signup=True)
        self.assertTrue(PasswordAuthentication.confirm_signup_enabled())

    def test_confirm_signup_enabled_method_disabled(self):
        PasswordAuthentication.objects.create(confirm_signup=True, enabled=False)
        self.assertFalse(PasswordAuthentication.confirm_signup_enabled())


class FacebookAuthenticationTestCase(SingletonAuthenticationMethodTestMixin, BluebottleTestCase):
    factory = FacebookAuthenticationFactory


class GoogleAuthenticationTestCase(SingletonAuthenticationMethodTestMixin, BluebottleTestCase):
    factory = GoogleAuthenticationFactory


class SAMLAuthenticationTestCase(BluebottleTestCase):
    def test_create_multiple(self):
        SAMLAuthenticationFactory.create_batch(3)

        self.assertEqual(SAMLAuthentication.objects.count(), 3)

    def test_validate_second(self):
        SAMLAuthenticationFactory.create()

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

        SAMLAuthenticationFactory.create_batch(2)

        self.assertEqual(SAMLAuthentication.objects.count(), 2)
