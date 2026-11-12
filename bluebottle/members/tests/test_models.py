from bluebottle.members.models import PasswordAuthentication
from bluebottle.test.utils import BluebottleTestCase

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from bluebottle.members.models import SAMLAuthentication
from bluebottle.members.tests.factories import (
    FacebookAuthenticationFactory, GoogleAuthenticationFactory, PasswordAuthenticationFactory,
    SAMLAuthenticationFactory
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
