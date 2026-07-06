from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from bluebottle.members.models import MemberPlatformSettings, SingleSignOnProvider
from bluebottle.members.serializers import MemberPlatformSettingsSerializer
from bluebottle.members.sso import (
    get_configured_sso_providers,
    get_sso_provider,
    get_token_auth_settings,
)
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.token_auth.tests.saml_settings import TOKEN_AUTH_SETTINGS


class SingleSignOnProviderTestCase(TestCase):
    def setUp(self):
        self.platform_settings = MemberPlatformSettings.objects.create()

    def test_display_name_uses_idp_domain(self):
        provider = SingleSignOnProvider.objects.create(
            settings=self.platform_settings,
            idp_entity_id='http://idp.example.com/',
            idp_sso_url='http://idp.example.com/SSOService.php',
            sp_entity_id='http://stuff.com/endpoints/metadata.php',
            sp_acs_url='http://stuff.com/endpoints/endpoints/acs.php',
        )
        self.assertEqual(provider.display_name, 'idp.example.com')

    def test_to_token_auth_settings(self):
        provider = SingleSignOnProvider.from_token_auth_settings(
            self.platform_settings,
            TOKEN_AUTH_SETTINGS,
        )
        settings = provider.to_token_auth_settings()

        self.assertEqual(
            settings['backend'],
            'token_auth.auth.saml.SAMLAuthentication',
        )
        self.assertEqual(
            settings['idp']['singleSignOnService']['url'],
            TOKEN_AUTH_SETTINGS['idp']['singleSignOnService']['url'],
        )
        self.assertEqual(
            settings['security']['requestedAuthnContext'],
            TOKEN_AUTH_SETTINGS['security']['requestedAuthnContext'],
        )


class SSOUtilsTestCase(BluebottleTestCase):
    def setUp(self):
        super(SSOUtilsTestCase, self).setUp()
        self.platform_settings = MemberPlatformSettings.objects.get_or_create()[0]
        SingleSignOnProvider.objects.filter(settings=self.platform_settings).delete()

    def _create_provider(self, entity_id, sso_url):
        return SingleSignOnProvider.objects.create(
            settings=self.platform_settings,
            idp_entity_id=entity_id,
            idp_sso_url=sso_url,
            sp_entity_id='http://stuff.com/endpoints/metadata.php',
            sp_acs_url='http://stuff.com/endpoints/endpoints/acs.php',
        )

    def test_get_configured_sso_providers(self):
        self._create_provider(
            'http://idp.example.com/',
            'http://idp.example.com/SSOService.php',
        )
        providers = get_configured_sso_providers()
        self.assertEqual(len(providers), 1)

    def test_get_sso_provider_by_id(self):
        provider = self._create_provider(
            'http://idp.example.com/',
            'http://idp.example.com/SSOService.php',
        )
        resolved = get_sso_provider(provider.pk)
        self.assertEqual(resolved.pk, provider.pk)

    def test_get_sso_provider_requires_id_for_multiple(self):
        self._create_provider(
            'http://idp-one.example.com/',
            'http://idp-one.example.com/SSOService.php',
        )
        self._create_provider(
            'http://idp-two.example.com/',
            'http://idp-two.example.com/SSOService.php',
        )
        with self.assertRaises(ImproperlyConfigured):
            get_sso_provider(require=True)

    def test_get_token_auth_settings_uses_first_provider(self):
        self._create_provider(
            'http://idp-one.example.com/',
            'http://idp-one.example.com/SSOService.php',
        )
        self._create_provider(
            'http://idp-two.example.com/',
            'http://idp-two.example.com/SSOService.php',
        )
        settings = get_token_auth_settings()
        self.assertEqual(
            settings['idp']['singleSignOnService']['url'],
            'http://idp-one.example.com/SSOService.php',
        )


class MemberPlatformSettingsSerializerTestCase(TestCase):
    def test_sso_login_methods(self):
        platform_settings = MemberPlatformSettings.objects.create()
        provider = SingleSignOnProvider.objects.create(
            settings=platform_settings,
            name='Okta',
            idp_entity_id='http://idp.example.com/',
            idp_sso_url='http://idp.example.com/SSOService.php',
            sp_entity_id='http://stuff.com/endpoints/metadata.php',
            sp_acs_url='http://stuff.com/endpoints/endpoints/acs.php',
        )

        data = MemberPlatformSettingsSerializer(platform_settings).data

        self.assertEqual(
            data['sso_login_methods'],
            [{'id': str(provider.pk), 'name': 'Okta'}],
        )
