# -*- coding: utf-8 -*-
from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory
from django.urls import reverse
from social_core.utils import slugify

from bluebottle.news.admin import NewsItemAdmin
from bluebottle.news.models import NewsItem
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.news import NewsItemFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class TestNewsAdmin(BluebottleAdminTestCase):
    LONG_TITLE = (
        "This is just a ridiculously long title, "
        "because there's people out there that think we should support that."
    )

    EXPECTED_SLUG = "this-is-just-a-ridiculously-long-title-because-the"

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super().setUp()
        self.app.set_user(self.staff_member)
        self.site = AdminSite()
        self.news_admin = NewsItemAdmin(NewsItem, self.site)
        self.request_factory = RequestFactory()

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
        self.assertEqual(news_item.author, self.superuser)

        news_item.author = user
        self.news_admin.save_model(request=self.request,
                                   obj=news_item,
                                   form=form, change=True)
        news_item.refresh_from_db()
        self.assertEqual(news_item.author, user)

    def test_long_title(self):
        add_url = reverse('admin:news_newsitem_add')
        page = self.app.get(add_url, user=self.superuser)
        main_form = page.forms.get('newsitem_form')
        self.assertIsNotNone(main_form, 'Admin add form with title/slug not found')
        main_form['title'] = self.LONG_TITLE
        main_form['slug'] = 'short-slug'
        main_form['language'] = 'en'
        main_form.submit()
        news_item = NewsItem.objects.order_by('-pk').first()
        self.assertIsNotNone(news_item, 'NewsItem was not created')
        self.assertEqual(news_item.title, self.LONG_TITLE)
        self.assertEqual(news_item.slug, 'short-slug')

    def test_long_slug(self):
        add_url = reverse('admin:news_newsitem_add')
        page = self.app.get(add_url, user=self.superuser)
        main_form = page.forms.get('newsitem_form')
        self.assertIsNotNone(main_form, 'Admin add form with title/slug not found')
        main_form['title'] = self.LONG_TITLE
        main_form['slug'] = slugify(self.LONG_TITLE)
        main_form['language'] = 'en'
        result = main_form.submit()
        self.assertIn('Please correct the error below', result)
        self.assertIn('Ensure this value has at most 50 characters (it has 104)', result)

    def test_long_slug_truncated_on_save(self):
        news_item = NewsItemFactory.create(
            language='en',
            author=self.superuser,
            title=self.LONG_TITLE,
        )
        slug_max_length = NewsItem._meta.get_field('slug').max_length
        request = self.request_factory.post('/')
        request.user = self.superuser
        self.news_admin.save_model(request=request, obj=news_item, form=[], change=True)
        news_item.refresh_from_db()
        self.assertLessEqual(len(news_item.slug), slug_max_length)
