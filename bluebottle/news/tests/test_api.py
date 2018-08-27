from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.news import NewsItemFactory


class NewsItemApiTestCase(BluebottleTestCase):
    """
    Integration tests for the NewsItem API.
    """

    def setUp(self):
        super(NewsItemApiTestCase, self).setUp()

        self.some_dutch_news = NewsItemFactory.create(language='nl')
        self.some_other_dutch_news = NewsItemFactory.create(language='nl')
        self.third_dutch_news = NewsItemFactory.create(language='nl')

        self.some_english_news = NewsItemFactory.create(language='en')
        self.some_other_english_news = NewsItemFactory.create(language='en')
        self.some_unpublished_english_news = NewsItemFactory.create(status='draft', language='en')


class NewsItemsApiTest(NewsItemApiTestCase):
    """
    Test case for the ``NewsItem`` API view

    Endpoint: /api/news/items/
    """

    def test_news_list_unfiltered(self):
        """
        Test retrieving news items.
        """
        response = self.client.get(reverse('news_item_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)

    def test_news_list_filtered(self):
        """
        Test filtering news items by language.
        """
        # Check that we have 3 dutch news items
        response = self.client.get(reverse('news_item_list'),
                                   {'language': 'nl'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        # Check that we have 2 english news items
        response = self.client.get(reverse('news_item_list'),
                                   {'language': 'en'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_news_post_details(self):
        """
        Test retrieving a single news item.
        """
        news_item_url = reverse('news_post_detail',
                                kwargs={'slug': self.some_dutch_news.slug})
        response = self.client.get(news_item_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['title'], self.some_dutch_news.title)
