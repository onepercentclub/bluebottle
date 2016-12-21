from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.slides import SlideFactory, DraftSlideFactory


class SlideTestCase(BluebottleTestCase):
    """
    Base class for test cases for ``slide`` module.

    The testing classes for ``slide`` module related to the API must
    subclass this.
    """

    def setUp(self):
        super(SlideTestCase, self).setUp()

        self.user = BlueBottleUserFactory.create()

        self.slide1 = SlideFactory.create(author=self.user, language='nl')
        self.slide2 = SlideFactory.create(author=self.user, language='en')
        self.slide3 = DraftSlideFactory.create(author=self.user,
                                               language='en', )


class SlideListTestCase(SlideTestCase):
    """
    Test case for ``SlideList`` API view.

    Endpoint: /api/textwallposts/
    """

    def test_slides_list(self):
        """
        Ensure we return list of published slides list.
        """
        response = self.client.get(reverse('slide_list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_api_slides_list_filtered(self):
        """
        Ensure slides can be filtered by language
        """
        response = self.client.get(reverse('slide_list'), {'language': 'en'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_slides_list_data(self):
        """
        Ensure get request returns record with correct data.
        """
        response = self.client.get(reverse('slide_list'), {'language': 'nl'})
        slide = response.data['results'][0]

        self.assertEqual(slide['title'], self.slide1.title)
        self.assertEqual(slide['body'], self.slide1.body)
        self.assertEqual(slide['author'], self.slide1.author.id)
        self.assertEqual(slide['status'], self.slide1.status)
        self.assertEqual(slide['sequence'], self.slide1.sequence)
