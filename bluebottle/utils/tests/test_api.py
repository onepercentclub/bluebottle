from django.core.urlresolvers import reverse
from rest_framework import status

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.models import TranslationPlatformSettings


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
            response.data['platform']['translations'],
            {}
        )

    def test_with_translation(self):
        TranslationPlatformSettings.objects.create(
            office='Site',
            whats_the_location_of_your_office='What is your office site'
        )
        response = self.client.get(self.settings_url)
        self.assertEqual(
            response.data['platform']['translations']['Office'],
            'Site'
        )
        self.assertEqual(
            response.data['platform']['translations'][u'What\u2019s the location of your office?'],
            'What is your office site'
        )
