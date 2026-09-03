from django.urls import reverse
from rest_framework import status

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.test.utils import BluebottleTestCase


class TestLanguageApi(BluebottleTestCase):
    def setUp(self):
        super(TestLanguageApi, self).setUp()
        self.language_url = reverse("utils_language_list")

    def test_languages(self):
        """ simple language list """
        response = self.client.get(self.language_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TranslationSettingsTestCase(BluebottleTestCase):

    def setUp(self):
        super(TranslationSettingsTestCase, self).setUp()
        self.settings_url = reverse('settings')

    def test_no_translations(self):
        response = self.client.get(self.settings_url)
        self.assertEqual(
            response.data['platform']['members']['translate_user_content'],
            False
        )

    def test_with_translation(self):
        member_settings = MemberPlatformSettings.load()
        member_settings.translate_user_content = True
        member_settings.save()

        response = self.client.get(self.settings_url)
        self.assertEqual(
            response.data['platform']['members']['translate_user_content'],
            True
        )
