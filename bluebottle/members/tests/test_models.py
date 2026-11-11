from bluebottle.members.models import GoogleAuthentication, PasswordAuthentication
from bluebottle.test.utils import BluebottleTestCase


class PasswordAuthenticationLoadTestCase(BluebottleTestCase):
    def test_load_none(self):
        self.assertIsNone(PasswordAuthentication.load())

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


class PasswordAuthenticationIsEnabledTestCase(BluebottleTestCase):
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


class PasswordAuthenticationConfirmSignupEnabledTestCase(BluebottleTestCase):
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
