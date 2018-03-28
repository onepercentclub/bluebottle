# -*- coding: utf-8 -*-
from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory

from bluebottle.pages.admin import PageAdmin
from bluebottle.pages.models import Page
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.pages import PageFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class TestPageAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestPageAdmin, self).setUp()
        self.client.force_login(self.superuser)
        self.init_projects()
        self.site = AdminSite()
        self.page_admin = PageAdmin(Page, self.site)

    def test_update_author(self):
        user = BlueBottleUserFactory.create()
        page = PageFactory.create()

        self.request_factory = RequestFactory()
        self.request = self.request_factory.post('/')
        self.request.user = self.superuser

        form = []
        page.author = None
        self.page_admin.save_model(request=self.request,
                                   obj=page,
                                   form=form, change=True)
        page.refresh_from_db()
        self.assertEquals(page.author, self.superuser)

        page.author = user
        self.page_admin.save_model(request=self.request,
                                   obj=page,
                                   form=form, change=True)
        page.refresh_from_db()
        self.assertEquals(page.author, user)
