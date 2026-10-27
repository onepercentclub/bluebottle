# -*- coding: utf-8 -*-

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.test.client import RequestFactory
from django.urls import reverse
from fluent_contents.models import Placeholder
from jet.dashboard.models import UserDashboardModule

from bluebottle.cms.models import ImagePlainTextItem, PeopleContent, PollContent
from bluebottle.pages.admin import PageAdmin
from bluebottle.pages.models import Page, DocumentItem
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.pages import PageFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.voting.models import Poll


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

    def test_change_page_with_cms_blocks(self):
        page = PageFactory.create()
        placeholder = Placeholder.objects.create_for_object(page, 'blog_contents')
        placeholder.save()

        poll = Poll()
        poll.set_current_language('en')
        poll.title = 'Favourite colour'
        poll.status = 'open'
        poll.save()
        PollContent.objects.create_for_placeholder(placeholder, poll=poll)
        ImagePlainTextItem.objects.create_for_placeholder(placeholder, title='Intro')
        people = PeopleContent.objects.create_for_placeholder(placeholder)
        people.persons.create(name='Ada', email='ada@example.com', role='Lead')

        page_admin_url = reverse('admin:pages_page_change', args=(page.id,))
        response = self.client.get(page_admin_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Favourite colour')
        self.assertContains(response, 'Intro')
        self.assertContains(response, 'Ada')

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
                "author": page.author.id,
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
                "scaledimagetextitem-TOTAL_FORMS": "0",
                "scaledimagetextitem-INITIAL_FORMS": "0",
                "imageplaintextitem-TOTAL_FORMS": "0",
                "imageplaintextitem-INITIAL_FORMS": "0",
                "textitem-TOTAL_FORMS": "0",
                "textitem-INITIAL_FORMS": "0",
                "imagetextrounditem-TOTAL_FORMS": "0",
                "imagetextrounditem-INITIAL_FORMS": "0",
                "columnsitem-TOTAL_FORMS": "0",
                "columnsitem-INITIAL_FORMS": "0",
                "peoplecontent-TOTAL_FORMS": "0",
                "peoplecontent-INITIAL_FORMS": "0",
                "pollcontent-TOTAL_FORMS": "0",
                "pollcontent-INITIAL_FORMS": "0",

                '_continue': 'Save and continue editing',
            }

            response = self.client.post(page_admin_url, data, format='multipart')

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
                "author": page.author.id,
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
                "scaledimagetextitem-TOTAL_FORMS": "0",
                "scaledimagetextitem-INITIAL_FORMS": "0",
                "imageplaintextitem-TOTAL_FORMS": "0",
                "imageplaintextitem-INITIAL_FORMS": "0",
                "textitem-TOTAL_FORMS": "0",
                "textitem-INITIAL_FORMS": "0",
                "imagetextrounditem-TOTAL_FORMS": "0",
                "imagetextrounditem-INITIAL_FORMS": "0",
                "columnsitem-TOTAL_FORMS": "0",
                "columnsitem-INITIAL_FORMS": "0",
                "peoplecontent-TOTAL_FORMS": "0",
                "peoplecontent-INITIAL_FORMS": "0",
                "pollcontent-TOTAL_FORMS": "0",
                "pollcontent-INITIAL_FORMS": "0",

                '_continue': 'Save and continue editing',
            }

            response = self.client.post(page_admin_url, data, format='multipart')

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
                "author": page.author.id,
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
                "scaledimagetextitem-TOTAL_FORMS": "0",
                "scaledimagetextitem-INITIAL_FORMS": "0",
                "imageplaintextitem-TOTAL_FORMS": "0",
                "imageplaintextitem-INITIAL_FORMS": "0",
                "textitem-TOTAL_FORMS": "0",
                "textitem-INITIAL_FORMS": "0",
                "imagetextrounditem-TOTAL_FORMS": "0",
                "imagetextrounditem-INITIAL_FORMS": "0",
                "columnsitem-TOTAL_FORMS": "0",
                "columnsitem-INITIAL_FORMS": "0",
                "peoplecontent-TOTAL_FORMS": "0",
                "peoplecontent-INITIAL_FORMS": "0",
                "pollcontent-TOTAL_FORMS": "0",
                "pollcontent-INITIAL_FORMS": "0",

                '_continue': 'Save and continue editing',
            }

            response = self.client.post(page_admin_url, data, format='multipart')

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
                "author": page.author.id,
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
                "peoplecontent-TOTAL_FORMS": "0",
                "peoplecontent-INITIAL_FORMS": "0",
                "pollcontent-TOTAL_FORMS": "0",
                "pollcontent-INITIAL_FORMS": "0",

                '_continue': 'Save and continue editing',
            }

            response = self.client.post(page_admin_url, data, format='multipart')

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Mime type &#x27;application/pdf&#x27; doesn&#x27;t match the filename extension &#x27;.html&#x27;"
        )
        self.assertEqual(page.content.contentitems.count(), 0)
        self.assertEqual(DocumentItem.objects.count(), 0)


class ContentEditorPageAdminTestCase(BluebottleAdminTestCase):
    csrf_checks = False

    def setUp(self):
        super().setUp()
        self.editor = BlueBottleUserFactory.create(is_staff=True)
        Group.objects.get(name='Content Editor').user_set.add(self.editor)
        self.client.force_login(self.editor)
        self.page = PageFactory.create()

    def test_permissions(self):
        self.assertTrue(self.editor.has_perms([
            'pages.add_page', 'pages.change_page', 'pages.delete_page', 'pages.view_page',
            'text.add_textitem', 'cms.add_person', 'fluent_contents.change_placeholder',
            'looker.access_looker_embeds',
        ]))
        self.assertFalse(self.editor.has_perm('members.view_member'))
        self.assertFalse(self.editor.has_perm('activities.view_activity'))

    def test_page_list_and_add(self):
        response = self.client.get(reverse('admin:pages_page_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.page.title)

        response = self.client.get(reverse('admin:pages_page_add'))
        self.assertEqual(response.status_code, 200)

    def test_change_page_with_all_blocks(self):
        placeholder = Placeholder.objects.create_for_object(self.page, 'blog_contents')
        people = PeopleContent.objects.create_for_placeholder(placeholder)
        people.persons.create(name='Ada', email='ada@example.com', role='Lead')

        response = self.client.get(reverse('admin:pages_page_change', args=(self.page.id,)))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ada')
        for prefix in [
            'textitem', 'columnsitem', 'actionitem', 'imagetextitem', 'imagetextrounditem',
            'scaledimagetextitem', 'oembeditem', 'rawhtmlitem', 'pictureitem', 'documentitem',
            'peoplecontent', 'imageplaintextitem', 'pollcontent',
        ]:
            self.assertContains(response, '{}-TOTAL_FORMS'.format(prefix))

    def test_delete_page(self):
        url = reverse('admin:pages_page_delete', args=(self.page.id,))
        confirmation = self.app.get(url, user=self.editor)

        form = next(form for form in confirmation.forms.values() if 'post' in form.fields)
        form.submit(user=self.editor)

        self.assertFalse(Page.objects.filter(pk=self.page.pk).exists())

    def test_no_access_to_members(self):
        response = self.client.get(reverse('admin:members_member_changelist'))

        self.assertEqual(response.status_code, 403)

    def test_author_is_not_shown(self):
        response = self.client.get(reverse('admin:pages_page_change', args=(self.page.id,)))

        self.assertNotContains(response, 'id_author')
        self.assertNotContains(response, self.page.author.full_name)

    def test_author_is_not_shown_to_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('admin:pages_page_change', args=(self.page.id,)))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id_author')

    def test_dashboard_hides_members(self):
        BlueBottleUserFactory.create(first_name='Zebedeus', last_name='Quimby')

        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Zebedeus')

        self.client.force_login(self.superuser)
        response = self.client.get(reverse('admin:index'))
        self.assertContains(response, 'Zebedeus')

    def test_dashboard_hides_saved_member_widget(self):
        BlueBottleUserFactory.create(first_name='Zebedeus', last_name='Quimby')
        UserDashboardModule.objects.create(
            title='Recently joined users', app_label=None, user=self.editor,
            module='bluebottle.members.dashboard.RecentMembersDashboard', column=1, order=0,
        )

        response = self.client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Zebedeus')
        self.assertNotContains(response, 'Recently joined users')

    def test_menu_hides_users_initiatives_and_activities(self):
        response = self.client.get(reverse('admin:pages_page_changelist'))

        for name in ['members_member', 'initiatives_initiative', 'activities_activity']:
            self.assertNotContains(response, 'href="{}"'.format(reverse('admin:{}_changelist'.format(name))))

        self.client.force_login(self.staff_member)
        response = self.client.get(reverse('admin:pages_page_changelist'))
        for name in ['members_member', 'initiatives_initiative', 'activities_activity']:
            self.assertContains(response, 'href="{}"'.format(reverse('admin:{}_changelist'.format(name))))
