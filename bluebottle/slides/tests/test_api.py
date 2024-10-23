from django.core.files import File
from django.urls import reverse
from fluent_contents.models import Placeholder

from rest_framework import status

from bluebottle.cms.models import HomePage, SlidesContent
from bluebottle.test.factory_models.cms import HomePageFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.slides import SlideFactory, DraftSlideFactory


class SlideTestCase(BluebottleTestCase):

    def setUp(self):
        super(SlideTestCase, self).setUp()
        self.user = BlueBottleUserFactory.create()
        self.slide1 = SlideFactory.create(
            author=self.user,
            title='Ons platform',
            language='nl')
        self.slide2 = SlideFactory.create(
            author=self.user,
            title='Our platform',
            language='en')

        with open('bluebottle/slides/tests/files/sparks.mp4', 'rb') as video:
            self.slide2.video.save(
                'sparks.mp4',
                File(video)
            )

        self.slide3 = SlideFactory.create(
            author=self.user,
            title='Things to do',
            language='en')
        self.slide4 = DraftSlideFactory.create(author=self.user, language='nl')
        self.homepage_url = reverse('home-detail')

        HomePage.objects.get(pk=1).delete()
        self.page = HomePageFactory(pk=1)
        placeholder = Placeholder.objects.create_for_object(self.page, slot='content')
        SlidesContent.objects.create_for_placeholder(placeholder, language_code='en')
        SlidesContent.objects.create_for_placeholder(placeholder, language_code='nl')

        self.url = reverse('home-detail')

    def test_slides_list(self):
        """
        Ensure we return list of published slides list.
        """
        response = self.client.get(self.homepage_url, HTTP_X_APPLICATION_LANGUAGE='nl')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slides = response.data['blocks'][0]['slides']
        self.assertEqual(len(slides), 1)

    def test_api_slides_list_filtered(self):
        """
        Ensure slides can be filtered by language
        """
        response = self.client.get(self.homepage_url, HTTP_X_APPLICATION_LANGUAGE='nl')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slides = response.data['blocks'][0]['slides']
        self.assertEqual(len(slides), 1)
        self.assertEqual(slides[0]['title'], self.slide1.title)

    def test_slides_list_data(self):
        """
        Ensure get request returns record with correct data.
        """
        response = self.client.get(self.homepage_url, HTTP_X_APPLICATION_LANGUAGE='en')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slides = response.data['blocks'][0]['slides']
        self.assertEqual(len(slides), 2)
        slide = slides[0]
        self.assertEqual(slide['title'], self.slide2.title)
        self.assertTrue(slide['video'].startswith('http://testserver/media/banner_slides/sparks'))
        self.assertEqual(slide['body'], self.slide2.body)
