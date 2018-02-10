# -*- coding: utf-8 -*-
from django.urls.base import reverse

from bluebottle.test.factory_models.wallposts import MediaWallpostFactory, MediaWallpostPhotoFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class TestWallpostAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestWallpostAdmin, self).setUp()
        wallpost = MediaWallpostFactory.create()
        MediaWallpostPhotoFactory.create_batch(10, mediawallpost=wallpost)
        self.client.force_login(self.superuser)
        self.media_wallpost_url = reverse('admin:wallposts_mediawallpost_changelist')

    def test_mediawallpost_admin(self):
        response = self.client.get(self.media_wallpost_url)
        self.assertContains(response, '9 more')
