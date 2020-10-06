# -*- coding: utf-8 -*-
from bluebottle.assignments.tests.factories import AssignmentFactory

from bluebottle.events.tests.factories import EventFactory

from bluebottle.initiatives.tests.factories import InitiativeFactory
from django.urls.base import reverse

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
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
        event = EventFactory()
        self.wallpost = MediaWallpostFactory.create(content_object=event)
        url = reverse('admin:wallposts_mediawallpost_change', args=(self.wallpost.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertContains(response, event.title)

    def test_task_textwallpost_admin(self):
        task = AssignmentFactory.create()
        self.wallpost = MediaWallpostFactory.create(content_object=task)
        url = reverse('admin:wallposts_mediawallpost_change', args=(self.wallpost.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertContains(response, task.title)

    def test_project_systemwallpost_admin(self):
        funding = FundingFactory.create()
        donation = DonationFactory(activity=funding)
        self.wallpost = MediaWallpostFactory.create(content_object=funding, donation=donation)
        url = reverse('admin:wallposts_mediawallpost_change', args=(self.wallpost.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertContains(response, funding.title)
