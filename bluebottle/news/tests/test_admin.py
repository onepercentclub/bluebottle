# -*- coding: utf-8 -*-
from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory

from bluebottle.news.admin import NewsItemAdmin
from bluebottle.news.models import NewsItem
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.news import NewsItemFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class MockUser:
    def __init__(self, perms=None, is_staff=True):
        self.perms = perms or []
        self.is_staff = is_staff

    def has_perm(self, perm):
        return perm in self.perms


class TestNewsAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestNewsAdmin, self).setUp()
        self.client.force_login(self.superuser)
        self.init_projects()
        self.site = AdminSite()
        self.news_admin = NewsItemAdmin(NewsItem, self.site)

    def test_update_author(self):
        user = BlueBottleUserFactory.create()
        news_item = NewsItemFactory.create()

        self.request_factory = RequestFactory()
        self.request = self.request_factory.post('/')
        self.request.user = self.superuser

        form = []
        news_item.author = None
        self.news_admin.save_model(request=self.request,
                                   obj=news_item,
                                   form=form, change=True)
        news_item.refresh_from_db()
        self.assertEquals(news_item.author, self.superuser)

        news_item.author = user
        self.news_admin.save_model(request=self.request,
                                   obj=news_item,
                                   form=form, change=True)
        news_item.refresh_from_db()
        self.assertEquals(news_item.author, user)
