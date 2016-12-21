from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.test.factory_models.quotes import QuoteFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class QuoteTestCase(BluebottleTestCase):
    """
    Base class for test cases for ``slide`` module.

    The testing classes for ``slide`` module related to the API must
    subclass this.
    """

    def setUp(self):
        super(QuoteTestCase, self).setUp()

        self.author = BlueBottleUserFactory.create()
        self.user = BlueBottleUserFactory.create()
        self.quote1 = QuoteFactory.create(
            author=self.author, user=self.user,
            quote="The best things in life are free.", language='en')
        self.quote2 = QuoteFactory.create(
            author=self.author, user=self.user,
            quote="Always forgive your enemies; nothing annoys them so much.",
            language='nl')


class QuoteListTestCase(QuoteTestCase):
    """
    Test case for ``QuoteList`` API view.

    Endpoint: /api/quotes/
    """

    def test_api_quotes_list_endpoint(self):
        """
        Ensure get request returns 200.
        """
        response = self.client.get(reverse('quote_list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_api_quotes_list_filtering(self):
        """
        Ensure filtering returns correct results
        """
        response = self.client.get(reverse('quote_list'), {'language': 'en'})
        self.assertEqual(response.data['count'], 1)

    def test_api_quotes_list_data(self):
        """
        Ensure get request returns record with correct data.
        """
        response = self.client.get(reverse('quote_list'))
        quote = response.data['results'][0]

        self.assertEqual(quote['id'], self.quote1.id)
        self.assertEqual(quote['user']['id'], self.user.id)
        self.assertEqual(quote.get('author', None), None)
        self.assertEqual(quote['quote'], self.quote1.quote)
