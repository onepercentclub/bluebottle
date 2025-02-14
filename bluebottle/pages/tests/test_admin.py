# -*- coding: utf-8 -*-

from django.contrib.admin.sites import AdminSite
from django.test.client import RequestFactory
from django.urls import reverse
from fluent_contents.models import Placeholder

from bluebottle.pages.admin import PageAdmin
from bluebottle.pages.models import Page, DocumentItem
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
        self.assertEqual(page.author, self.superuser)

        page.author = user
        self.page_admin.save_model(request=self.request,
                                   obj=page,
                                   form=form, change=True)
        page.refresh_from_db()
        self.assertEqual(page.author, user)

    def test_upload_link_to_png(self):
        page = PageFactory.create()
        placeholder = Placeholder.objects.create_for_object(page, 'blog_contents')
        placeholder.save()
        page_admin_url = reverse('admin:pages_page_change', args=(page.id,))
        response = self.client.get(page_admin_url)
        csrf = self.get_csrf_token(response)
        with open('./bluebottle/files/tests/files/test-image.png', "rb") as image:
            data = {
                "csrfmiddlewaretoken": csrf,
                "slug": page.slug,
                "title": page.title,
                "language": 'en',
                "auhtor": page.author.id,
                "status": "published",
                "publication_date_0": "2013-07-05",
                "publication_date_1": "14:13:53",
                "initial-publication_date_0": "2013-07-05",
                "initial-publication_date_1": "14:13:53",
                "publication_end_date_0": "",
                "publication_end_date_1": "",

                "placeholder-fs-TOTAL_FORMS": 1,
                "placeholder-fs-INITIAL_FORMS": 1,
                "placeholder-fs-MIN_NUM_FORMS": 0,
                "placeholder-fs-MAX_NUM_FORMS": 1000,
                "placeholder-fs-0-id": placeholder.id,
                "placeholder-fs-0-slot": 'blog_contents',
                "placeholder-fs-0-role": "m",
                "placeholder-fs-0-title": "Body",

                "documentitem-TOTAL_FORMS": 1,
                "documentitem-INITIAL_FORMS": 0,
                "documentitem-MIN_NUM_FORMS": 0,
                "documentitem-MAX_NUM_FORMS": 1000,
                # "documentitem-0-contentitem_ptr": '',
                "documentitem-0-placeholder": placeholder.id,
                "documentitem-0-placeholder_slot": "blog_contents",
                "documentitem-0-sort_order": 0,
                "documentitem-0-text": "Link",
                "documentitem-0-document": image,

                "actionitem-TOTAL_FORMS": "0",
                "actionitem-INITIAL_FORMS": "0",
                "rawhtmlitem-TOTAL_FORMS": "0",
                "rawhtmlitem-INITIAL_FORMS": "0",
                "oembeditem-TOTAL_FORMS": "0",
                "oembeditem-INITIAL_FORMS": "0",
                "pictureitem-TOTAL_FORMS": "0",
                "pictureitem-INITIAL_FORMS": "0",
                "imagetextitem-TOTAL_FORMS": "0",
                "imagetextitem-INITIAL_FORMS": "0",
                "imageplaintextitem-TOTAL_FORMS": "0",
                "imageplaintextitem-INITIAL_FORMS": "0",
                "textitem-TOTAL_FORMS": "0",
                "textitem-INITIAL_FORMS": "0",
                "imagetextrounditem-TOTAL_FORMS": "0",
                "imagetextrounditem-INITIAL_FORMS": "0",
                "columnsitem-TOTAL_FORMS": "0",
                "columnsitem-INITIAL_FORMS": "0",

                '_continue': 'Save and continue editing',
            }

            response = self.client.post(page_admin_url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(page.content.contentitems.count(), 1)
        self.assertEqual(DocumentItem.objects.count(), 1)

    def test_upload_link_to_capital_png(self):
        page = PageFactory.create()
        placeholder = Placeholder.objects.create_for_object(page, 'blog_contents')
        placeholder.save()
        page_admin_url = reverse('admin:pages_page_change', args=(page.id,))
        response = self.client.get(page_admin_url)
        csrf = self.get_csrf_token(response)

        with open('./bluebottle/files/tests/files/Test-Image2.PNG', "rb") as image:
            data = {
                "csrfmiddlewaretoken": csrf,
                "slug": page.slug,
                "title": page.title,
                "language": 'en',
                "auhtor": page.author.id,
                "status": "published",
                "publication_date_0": "2013-07-05",
                "publication_date_1": "14:13:53",
                "initial-publication_date_0": "2013-07-05",
                "initial-publication_date_1": "14:13:53",
                "publication_end_date_0": "",
                "publication_end_date_1": "",

                "placeholder-fs-TOTAL_FORMS": 1,
                "placeholder-fs-INITIAL_FORMS": 1,
                "placeholder-fs-MIN_NUM_FORMS": 0,
                "placeholder-fs-MAX_NUM_FORMS": 1000,
                "placeholder-fs-0-id": placeholder.id,
                "placeholder-fs-0-slot": 'blog_contents',
                "placeholder-fs-0-role": "m",
                "placeholder-fs-0-title": "Body",

                "documentitem-TOTAL_FORMS": 1,
                "documentitem-INITIAL_FORMS": 0,
                "documentitem-MIN_NUM_FORMS": 0,
                "documentitem-MAX_NUM_FORMS": 1000,
                # "documentitem-0-contentitem_ptr": '',
                "documentitem-0-placeholder": placeholder.id,
                "documentitem-0-placeholder_slot": "blog_contents",
                "documentitem-0-sort_order": 0,
                "documentitem-0-text": "Link",
                "documentitem-0-document": image,

                "actionitem-TOTAL_FORMS": "0",
                "actionitem-INITIAL_FORMS": "0",
                "rawhtmlitem-TOTAL_FORMS": "0",
                "rawhtmlitem-INITIAL_FORMS": "0",
                "oembeditem-TOTAL_FORMS": "0",
                "oembeditem-INITIAL_FORMS": "0",
                "pictureitem-TOTAL_FORMS": "0",
                "pictureitem-INITIAL_FORMS": "0",
                "imagetextitem-TOTAL_FORMS": "0",
                "imagetextitem-INITIAL_FORMS": "0",
                "imageplaintextitem-TOTAL_FORMS": "0",
                "imageplaintextitem-INITIAL_FORMS": "0",
                "textitem-TOTAL_FORMS": "0",
                "textitem-INITIAL_FORMS": "0",
                "imagetextrounditem-TOTAL_FORMS": "0",
                "imagetextrounditem-INITIAL_FORMS": "0",
                "columnsitem-TOTAL_FORMS": "0",
                "columnsitem-INITIAL_FORMS": "0",

                '_continue': 'Save and continue editing',
            }

            response = self.client.post(page_admin_url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(page.content.contentitems.count(), 1)
        self.assertEqual(DocumentItem.objects.count(), 1)

    def test_upload_link_to_pptx(self):
        page = PageFactory.create()
        placeholder = Placeholder.objects.create_for_object(page, 'blog_contents')
        placeholder.save()
        page_admin_url = reverse('admin:pages_page_change', args=(page.id,))
        response = self.client.get(page_admin_url)
        csrf = self.get_csrf_token(response)
        with open('./bluebottle/files/tests/files/test.pptx', "rb") as image:
            data = {
                "csrfmiddlewaretoken": csrf,
                "slug": page.slug,
                "title": page.title,
                "language": 'en',
                "auhtor": page.author.id,
                "status": "published",
                "publication_date_0": "2013-07-05",
                "publication_date_1": "14:13:53",
                "initial-publication_date_0": "2013-07-05",
                "initial-publication_date_1": "14:13:53",
                "publication_end_date_0": "",
                "publication_end_date_1": "",

                "placeholder-fs-TOTAL_FORMS": 1,
                "placeholder-fs-INITIAL_FORMS": 1,
                "placeholder-fs-MIN_NUM_FORMS": 0,
                "placeholder-fs-MAX_NUM_FORMS": 1000,
                "placeholder-fs-0-id": placeholder.id,
                "placeholder-fs-0-slot": 'blog_contents',
                "placeholder-fs-0-role": "m",
                "placeholder-fs-0-title": "Body",

                "documentitem-TOTAL_FORMS": 1,
                "documentitem-INITIAL_FORMS": 0,
                "documentitem-MIN_NUM_FORMS": 0,
                "documentitem-MAX_NUM_FORMS": 1000,
                # "documentitem-0-contentitem_ptr": '',
                "documentitem-0-placeholder": placeholder.id,
                "documentitem-0-placeholder_slot": "blog_contents",
                "documentitem-0-sort_order": 0,
                "documentitem-0-text": "Link",
                "documentitem-0-document": image,

                "actionitem-TOTAL_FORMS": "0",
                "actionitem-INITIAL_FORMS": "0",
                "rawhtmlitem-TOTAL_FORMS": "0",
                "rawhtmlitem-INITIAL_FORMS": "0",
                "oembeditem-TOTAL_FORMS": "0",
                "oembeditem-INITIAL_FORMS": "0",
                "pictureitem-TOTAL_FORMS": "0",
                "pictureitem-INITIAL_FORMS": "0",
                "imagetextitem-TOTAL_FORMS": "0",
                "imagetextitem-INITIAL_FORMS": "0",
                "imageplaintextitem-TOTAL_FORMS": "0",
                "imageplaintextitem-INITIAL_FORMS": "0",
                "textitem-TOTAL_FORMS": "0",
                "textitem-INITIAL_FORMS": "0",
                "imagetextrounditem-TOTAL_FORMS": "0",
                "imagetextrounditem-INITIAL_FORMS": "0",
                "columnsitem-TOTAL_FORMS": "0",
                "columnsitem-INITIAL_FORMS": "0",

                '_continue': 'Save and continue editing',
            }

            response = self.client.post(page_admin_url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(page.content.contentitems.count(), 1)
        self.assertEqual(DocumentItem.objects.count(), 1)

    def test_upload_malicious_html(self):
        page = PageFactory.create()
        placeholder = Placeholder.objects.create_for_object(page, 'blog_contents')
        placeholder.save()
        page_admin_url = reverse('admin:pages_page_change', args=(page.id,))
        response = self.client.get(page_admin_url)
        csrf = self.get_csrf_token(response)
        with open('./bluebottle/pages/tests/files/xss.html', "rb") as image:
            data = {
                "csrfmiddlewaretoken": csrf,
                "slug": page.slug,
                "title": page.title,
                "language": 'en',
                "auhtor": page.author.id,
                "status": "published",
                "publication_date_0": "2013-07-05",
                "publication_date_1": "14:13:53",
                "initial-publication_date_0": "2013-07-05",
                "initial-publication_date_1": "14:13:53",
                "publication_end_date_0": "",
                "publication_end_date_1": "",

                "placeholder-fs-TOTAL_FORMS": 1,
                "placeholder-fs-INITIAL_FORMS": 1,
                "placeholder-fs-MIN_NUM_FORMS": 0,
                "placeholder-fs-MAX_NUM_FORMS": 1000,
                "placeholder-fs-0-id": placeholder.id,
                "placeholder-fs-0-slot": 'blog_contents',
                "placeholder-fs-0-role": "m",
                "placeholder-fs-0-title": "Body",

                "documentitem-TOTAL_FORMS": 1,
                "documentitem-INITIAL_FORMS": 0,
                "documentitem-MIN_NUM_FORMS": 0,
                "documentitem-MAX_NUM_FORMS": 1000,
                "documentitem-0-placeholder": placeholder.id,
                "documentitem-0-placeholder_slot": "blog_contents",
                "documentitem-0-sort_order": 0,
                "documentitem-0-text": "Link",
                "documentitem-0-document": image,

                "actionitem-TOTAL_FORMS": "0",
                "actionitem-INITIAL_FORMS": "0",
                "rawhtmlitem-TOTAL_FORMS": "0",
                "rawhtmlitem-INITIAL_FORMS": "0",
                "oembeditem-TOTAL_FORMS": "0",
                "oembeditem-INITIAL_FORMS": "0",
                "pictureitem-TOTAL_FORMS": "0",
                "pictureitem-INITIAL_FORMS": "0",
                "imagetextitem-TOTAL_FORMS": "0",
                "imagetextitem-INITIAL_FORMS": "0",
                "imageplaintextitem-TOTAL_FORMS": "0",
                "imageplaintextitem-INITIAL_FORMS": "0",
                "textitem-TOTAL_FORMS": "0",
                "textitem-INITIAL_FORMS": "0",
                "imagetextrounditem-TOTAL_FORMS": "0",
                "imagetextrounditem-INITIAL_FORMS": "0",
                "columnsitem-TOTAL_FORMS": "0",
                "columnsitem-INITIAL_FORMS": "0",

                '_continue': 'Save and continue editing',
            }

            response = self.client.post(page_admin_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Mime type &#x27;application/pdf&#x27; doesn&#x27;t match the filename extension &#x27;.html&#x27;"
        )
        self.assertEqual(page.content.contentitems.count(), 0)
        self.assertEqual(DocumentItem.objects.count(), 0)
