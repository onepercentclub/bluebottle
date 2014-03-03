import json

from django.core.urlresolvers import reverse

from rest_framework.compat import patterns, url
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.test import APITestCase

from fluent_contents.models import Placeholder
from bluebottle.test.factory_models.pages import PageFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

class PageTestCase(APITestCase):
	"""
	Base class for test cases for ``page`` module.

	The testing classes for ``page`` module related to the API must
	subclass this.
	"""
	def setUp(self):
		self.user = BlueBottleUserFactory.create()

		self.page1 = PageFactory.create(author=self.user, language = 'nl')
		placeholder1 = Placeholder.objects.create_for_object(self.page1, 'blog_contents')
		placeholder1.save()

		self.page2 = PageFactory.create(author=self.user, language = 'en')
		placeholder2 = Placeholder.objects.create_for_object(self.page2, 'blog_contents')

class PageListTestCase(PageTestCase):
	"""
	Test case for ``PageList`` API view.

	Endpoint: /api/pages/<language>/pages
	"""
	def test_api_pages_list_success(self):
		"""
		Ensure get request returns 200.
		"""
		response = self.client.get(reverse('page_list', kwargs={'language': 'nl'}))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['count'], 1)


	def test_api_pages_list_content(self):
		"""
		Ensure get request returns record with correct data.
		"""
		response = self.client.get(reverse('page_list', kwargs={'language': 'nl'}))

		page = response.data['results'][0]
		self.assertEqual(page['title'], self.page1.title)
		self.assertEqual(page['language'], self.page1.language)
		self.assertEqual(page['body'], '<!-- no items in placeholder \'blog_contents\' -->')
		self.assertEqual(page['full_page'], self.page1.full_page)

class PageDetailTestCase(PageTestCase):
	"""
	Test case for ``PageDetail`` API view.

	Endpoint: /api/pages/<language>/pages/<slug>
	"""
	def test_api_pages_detail_content(self):
		"""
		Ensure get request returns record with correct data.
		"""
		response = self.client.get(reverse('page_detail', kwargs={'language': 'en', 'slug': self.page2.slug}))

		results = response.data
		self.assertEqual(results['title'], self.page2.title)
		self.assertEqual(results['language'], self.page2.language)
		self.assertEqual(results['body'], '<!-- no items in placeholder \'blog_contents\' -->')
		self.assertEqual(results['full_page'], self.page2.full_page)