# -*- coding: utf-8 -*-

from bluebottle.time_based.tests.factories import DateActivityFactory, PeriodActivityFactory

from bluebottle.initiatives.tests.factories import InitiativeFactory
from django.urls.base import reverse

from bluebottle.funding.tests.factories import FundingFactory, DonorFactory
from bluebottle.test.factory_models.wallposts import (
    MediaWallpostFactory, MediaWallpostPhotoFactory
)
from bluebottle.test.utils import BluebottleAdminTestCase


class TestWallpostAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestWallpostAdmin, self).setUp()
        self.client.force_login(self.superuser)
        self.media_wallpost_url = '/en/admin/wallposts/mediawallpost/'

    def test_mediawallpost_admin(self):
        initiative = InitiativeFactory.create()
        self.wallpost = MediaWallpostFactory.create(content_object=initiative)
        MediaWallpostPhotoFactory.create_batch(10, mediawallpost=self.wallpost)
        self.wallpost.save()
        response = self.client.get(self.media_wallpost_url)
        self.assertContains(response, '9 more')

        url = reverse('admin:wallposts_mediawallpost_change', args=(self.wallpost.id, ))
        response = self.client.get(url)
        self.assertContains(response, initiative.title)

    def test_fundraiser_textwallpost_admin(self):
        activity = DateActivityFactory()
        self.wallpost = MediaWallpostFactory.create(content_object=activity)
        url = reverse('admin:wallposts_mediawallpost_change', args=(self.wallpost.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertContains(response, activity.title)

    def test_period_activity_textwallpost_admin(self):
        activity = PeriodActivityFactory.create()
        self.wallpost = MediaWallpostFactory.create(content_object=activity)
        url = reverse('admin:wallposts_mediawallpost_change', args=(self.wallpost.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertContains(response, activity.title)

    def test_project_systemwallpost_admin(self):
        funding = FundingFactory.create()
        donation = DonorFactory(activity=funding)
        self.wallpost = MediaWallpostFactory.create(content_object=funding, donation=donation)
        url = reverse('admin:wallposts_mediawallpost_change', args=(self.wallpost.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertContains(response, funding.title)
