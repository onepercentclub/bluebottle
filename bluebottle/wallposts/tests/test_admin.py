# -*- coding: utf-8 -*-
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.fundraisers import FundraiserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.wallposts import MediaWallpostFactory, MediaWallpostPhotoFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from django.urls.base import reverse


class TestWallpostAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestWallpostAdmin, self).setUp()
        self.client.force_login(self.superuser)
        # Don't user reverse here, because polymorphic sometimes makes a mistake.
        self.media_wallpost_url = '/en/admin/wallposts/mediawallpost/'

    def test_mediawallpost_admin(self):
        project = ProjectFactory.create()
        self.wallpost = MediaWallpostFactory.create(content_object=project)
        MediaWallpostPhotoFactory.create_batch(10, mediawallpost=self.wallpost)
        self.wallpost.save()
        response = self.client.get(self.media_wallpost_url)
        self.assertContains(response, '9 more')

        url = reverse('admin:wallposts_mediawallpost_change', args=(self.wallpost.id, ))
        response = self.client.get(url)
        self.assertContains(response, project.title)

    def test_fundraiser_textwallpost_admin(self):
        fundraiser = FundraiserFactory()
        self.wallpost = MediaWallpostFactory.create(content_object=fundraiser)
        url = reverse('admin:wallposts_mediawallpost_change', args=(self.wallpost.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertContains(response, fundraiser.title)

    def test_task_textwallpost_admin(self):
        task = FundraiserFactory()
        self.wallpost = MediaWallpostFactory.create(content_object=task)
        url = reverse('admin:wallposts_mediawallpost_change', args=(self.wallpost.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertContains(response, task.title)

    def test_project_systemwallpost_admin(self):
        project = ProjectFactory.create()
        donation = DonationFactory(project=project)
        self.wallpost = MediaWallpostFactory.create(content_object=project, donation=donation)
        url = reverse('admin:wallposts_mediawallpost_change', args=(self.wallpost.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertContains(response, project.title)
