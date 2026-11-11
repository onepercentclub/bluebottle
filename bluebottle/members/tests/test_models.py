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
