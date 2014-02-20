import json

from django.core.urlresolvers import reverse

from rest_framework.compat import patterns, url
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.test import APITestCase

from bluebottle.test.factory_models.slides import SlideFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

class SlideTestCase(APITestCase):
	"""
	Base class for test cases for ``slide`` module.

	The testing classes for ``slide`` module related to the API must
	subclass this.
	"""
	def setUp(self):
		self.user = BlueBottleUserFactory.create()
		self.slide = SlideFactory.create(author=self.user)


class SlideListTestCase(SlideTestCase):
	"""
	Test case for ``SlideList`` API view.

	Endpoint: /api/textwallposts/
	"""
	def test_api_slides_list_endpoint(self):
		"""
		Ensure we return a slides list.
		"""
		response = self.client.get(reverse('slide_list'))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['count'], 1)

	def test_api_slides_list_data(self):
		"""
		Ensure get request returns record with correct data.
		"""
		response = self.client.get(reverse('slide_list'))
		print(response.data)
		slide = response.data['results'][0]
		self.assertEqual(slide['title'], 'Slide Title 1')
		self.assertEqual(slide['body'], 'Slide Body 1')
		self.assertEqual(slide['author'], self.user.id)
		self.assertEqual(slide['status'], 'published')
		self.assertEqual(slide['sequence'], 1)