# -*- coding: utf-8 -*-
from bluebottle.test.factory_models.wallposts import MediaWallpostFactory, MediaWallpostPhotoFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class TestWallpostAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestWallpostAdmin, self).setUp()
        wallpost = MediaWallpostFactory.create()
        MediaWallpostPhotoFactory.create_batch(10, mediawallpost=wallpost)
        wallpost.save()
        self.client.force_login(self.superuser)
        # Don't user reverse here, because polymorphic sometimes makes a mistake.
        self.media_wallpost_url = '/en/admin/wallposts/mediawallpost/'

    def test_mediawallpost_admin(self):
        response = self.client.get(self.media_wallpost_url)
        self.assertContains(response, '9 more')
