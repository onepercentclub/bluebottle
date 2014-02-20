import json

from django.core.urlresolvers import reverse

from rest_framework.compat import patterns, url
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.test import APITestCase

from bluebottle.test.factory_models.quotes import QuoteFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

class QuoteTestCase(APITestCase):
	"""
	Base class for test cases for ``slide`` module.

	The testing classes for ``slide`` module related to the API must
	subclass this.
	"""
	def setUp(self):
		self.user = BlueBottleUserFactory.create()
		self.quote = QuoteFactory.create(user=self.user, quote="The best things in life are free.")

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
		self.assertEqual(response.data['count'], 1)


	def test_api_quotes_list_data(self):
		"""
		Ensure get request returns record with correct data.
		"""
		response = self.client.get(reverse('quote_list'))

		quote = response.data['results'][0]
		self.assertEqual(quote['id'], 1)
		self.assertEqual(quote['user']['id'], self.user.id)
		self.assertEqual(quote['quote'], 'The best things in life are free.')