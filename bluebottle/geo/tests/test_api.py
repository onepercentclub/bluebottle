import json

from django.core.urlresolvers import reverse

from rest_framework.compat import patterns, url
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.test import APITestCase

from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.projects import ProjectFactory

class GeoTestCase(APITestCase):
	"""
	Base class for test cases for ``slide`` module.

	The testing classes for ``slide`` module related to the API must
	subclass this.
	"""
	def setUp(self):
		self.country_1 = CountryFactory.create(name="Afghanistan")
		self.country_2 = CountryFactory.create(name="Albania")

class CountryListTestCase(GeoTestCase):
	"""
	Test case for ``CountryList`` API view.

	Endpoint: /api/geo/countries
	"""
	def test_api_country_list_endpoint(self):
		"""
		Ensure get request returns 200.
		"""
		response = self.client.get(reverse('country-list'))
		
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 2)


	def test_api_country_list_data(self):
		"""
		Ensure get request returns record with correct data.
		"""
		response = self.client.get(reverse('country-list'))

		country = response.data[0]
		self.assertEqual(country['id'], 1)
		self.assertEqual(country['name'], 'Afghanistan')
		self.assertEqual(country['oda'], False)
		self.assertEqual(country['code'], '')

class UsedCountryListTestCase(GeoTestCase):

	def setUp(self):
		super(UsedCountryListTestCase, self).setUp()

		self.project = ProjectFactory.create(country=self.country_1)

	"""
	Test case for ``CountryList`` API view.

	Endpoint: /api/geo/used_countries
	"""
	def test_api_used_country_list_endpoint(self):
		"""
		Ensure get request returns 200.
		"""
		response = self.client.get(reverse('used-country-list'))
		
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
