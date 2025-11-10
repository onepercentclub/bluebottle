# -*- coding: utf-8 -*-

from unittest import mock

from django.contrib.admin.sites import AdminSite
from django.urls import reverse
from fluent_contents.models import Placeholder

from bluebottle.pages.admin import PageAdmin, PageTranslateForm
from bluebottle.pages.models import Page, ActionItem, ColumnsItem
from bluebottle.pages.utils import copy_and_translate_blocks, _translate_block_fields
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.pages import PageFactory
from bluebottle.test.factory_models.utils import LanguageFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class TestPageTranslationUtils(BluebottleAdminTestCase):
    """Test the utility functions for translating pages."""

    def setUp(self):
        super(TestPageTranslationUtils, self).setUp()
        self.init_projects()
        # Create languages
        self.en_lang = LanguageFactory.create(code='en', language_name='English', native_name='English')
        self.nl_lang = LanguageFactory.create(code='nl', language_name='Dutch', native_name='Nederlands')

    def test_translate_block_fields_plain_text(self):
        """Test translating plain text fields."""
        fields = {
            'title': 'Hello World',
            'text': 'This is a test',
            'description': 'A description',
            'non_text_field': 123,
        }

        with mock.patch('bluebottle.pages.utils.translate_text_cached') as mock_translate:
            mock_translate.return_value = {'value': 'Hallo Wereld', 'source_language': 'en'}
            result = _translate_block_fields(fields, 'nl')

        self.assertEqual(result['title'], 'Hallo Wereld')
        self.assertEqual(result['text'], 'Hallo Wereld')
        self.assertEqual(result['description'], 'Hallo Wereld')
        self.assertEqual(result['non_text_field'], 123)  # Non-text field unchanged
        self.assertEqual(mock_translate.call_count, 3)

    def test_translate_block_fields_html_content(self):
        """Test translating HTML content."""
        fields = {
            'text': '<p>Hello <strong>World</strong></p>',
            'content': '<div>Test content</div>',
        }

        with mock.patch('bluebottle.pages.utils.translate_text_cached') as mock_translate:
            def translation_side_effect(text, lang):
                if text == '<p>Hello <strong>World</strong></p>':
                    return {'value': '<p>Hallo <strong>Wereld</strong></p>', 'source_language': 'en'}
                elif text == '<div>Test content</div>':
                    return {'value': '<div>Testinhoud</div>', 'source_language': 'en'}
                return {'value': text, 'source_language': 'en'}
            mock_translate.side_effect = translation_side_effect
            result = _translate_block_fields(fields, 'nl')

        self.assertEqual(result['text'], '<p>Hallo <strong>Wereld</strong></p>')
        self.assertEqual(result['content'], '<div>Testinhoud</div>')
        # Should translate entire HTML block as-is
        mock_translate.assert_any_call('<p>Hello <strong>World</strong></p>', 'nl')
        mock_translate.assert_any_call('<div>Test content</div>', 'nl')

    def test_translate_block_fields_skips_images(self):
        """Test that image fields are not translated."""
        fields = {
            'text': 'Hello',
            'image': {'image_url': 'http://example.com/image.jpg'},
        }

        with mock.patch('bluebottle.pages.utils.translate_text_cached') as mock_translate:
            mock_translate.return_value = {'value': 'Hallo', 'source_language': 'en'}
            result = _translate_block_fields(fields, 'nl')

        self.assertEqual(result['text'], 'Hallo')
        self.assertEqual(result['image'], {'image_url': 'http://example.com/image.jpg'})
        # Should only translate text field, not image
        self.assertEqual(mock_translate.call_count, 1)

    def test_translate_block_fields_handles_none(self):
        """Test that None values are handled correctly."""
        fields = {
            'title': 'Hello',
            'description': None,
            'text': '',
        }

        with mock.patch('bluebottle.pages.utils.translate_text_cached') as mock_translate:
            mock_translate.return_value = {'value': 'Hallo', 'source_language': 'en'}
            result = _translate_block_fields(fields, 'nl')

        self.assertEqual(result['title'], 'Hallo')
        self.assertIsNone(result['description'])
        self.assertEqual(result['text'], '')  # Empty string not translated
        self.assertEqual(mock_translate.call_count, 1)

    def test_copy_and_translate_blocks(self):
        """Test copying and translating blocks from one page to another."""
        source_page = PageFactory.create(language='en', title='Source Page')
        target_page = PageFactory.create(language='nl', title='Target Page', slug=source_page.slug)

        # Create placeholder and add content items
        source_placeholder = Placeholder.objects.create_for_object(source_page, 'blog_contents')
        action_item = ActionItem.objects.create_for_placeholder(
            source_placeholder,
            title='Click here',
            link='/test'
        )
        columns_item = ColumnsItem.objects.create_for_placeholder(
            source_placeholder,
            text1='Left column',
            text2='Right column'
        )

        with mock.patch('bluebottle.pages.utils.translate_text_cached') as mock_translate:
            def translation_side_effect(text, lang):
                translations = {
                    'Click here': 'Klik hier',
                    'Left column': 'Linker kolom',
                    'Right column': 'Rechter kolom',
                }
                return {
                    'value': translations.get(text, text),
                    'source_language': 'en'
                }
            mock_translate.side_effect = translation_side_effect

            copy_and_translate_blocks(source_page, target_page, 'nl')

        # Check that blocks were copied
        target_placeholder = Placeholder.objects.get(
            parent_id=target_page.pk,
            slot='blog_contents'
        )
        target_items = list(target_placeholder.contentitems.all())

        self.assertEqual(len(target_items), 2)
        # Check that ActionItem was translated
        action_items = [item for item in target_items if isinstance(item, ActionItem)]
        self.assertEqual(len(action_items), 1)
        self.assertEqual(action_items[0].title, 'Klik hier')
        self.assertEqual(action_items[0].link, '/test')  # Non-text field unchanged

        # Check that ColumnsItem was translated
        columns_items = [item for item in target_items if isinstance(item, ColumnsItem)]
        self.assertEqual(len(columns_items), 1)
        self.assertEqual(columns_items[0].text1, 'Linker kolom')
        self.assertEqual(columns_items[0].text2, 'Rechter kolom')

    def test_copy_and_translate_blocks_no_source_placeholder(self):
        """Test copying blocks when source page has no placeholder."""
        source_page = PageFactory.create(language='en')
        target_page = PageFactory.create(language='nl', slug=source_page.slug)

        # Don't create placeholder for source page
        copy_and_translate_blocks(source_page, target_page, 'nl')

        # Target placeholder should be created but empty
        target_placeholder = Placeholder.objects.get(
            parent_id=target_page.pk,
            slot='blog_contents'
        )
        self.assertEqual(target_placeholder.contentitems.count(), 0)

    def test_copy_and_translate_blocks_empty_source(self):
        """Test copying blocks from page with empty placeholder."""
        source_page = PageFactory.create(language='en')
        target_page = PageFactory.create(language='nl', slug=source_page.slug)

        # Create empty placeholder
        Placeholder.objects.create_for_object(source_page, 'blog_contents')

        copy_and_translate_blocks(source_page, target_page, 'nl')

        # Target should have placeholder but no items
        target_placeholder = Placeholder.objects.get(
            parent_id=target_page.pk,
            slot='blog_contents'
        )
        self.assertEqual(target_placeholder.contentitems.count(), 0)


class TestPageTranslationAdmin(BluebottleAdminTestCase):
    """Test the admin view for translating pages."""

    def setUp(self):
        super(TestPageTranslationAdmin, self).setUp()
        self.client.force_login(self.superuser)
        self.init_projects()
        self.site = AdminSite()
        self.page_admin = PageAdmin(Page, self.site)

        # Create languages
        self.en_lang = LanguageFactory.create(code='en', language_name='English', native_name='English')
        self.nl_lang = LanguageFactory.create(code='nl', language_name='Dutch', native_name='Nederlands')
        self.fr_lang = LanguageFactory.create(code='fr', language_name='French', native_name='Français')

    def test_translate_form_excludes_current_language(self):
        """Test that translate form excludes the current page language."""
        page = PageFactory.create(language='en')
        form = PageTranslateForm(current_language='en')

        # Should only have nl and fr, not en
        choices = [choice[0] for choice in form.fields['target_language'].choices]
        self.assertIn('nl', choices)
        self.assertIn('fr', choices)
        self.assertNotIn('en', choices)

    def test_translate_page_get(self):
        """Test GET request to translate page view."""
        page = PageFactory.create(language='en', title='Test Page')
        url = reverse('admin:pages_page_translate', args=(page.pk,))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Page')
        self.assertContains(response, 'target_language')

    def test_translate_page_post_success(self):
        """Test successful page translation."""
        page = PageFactory.create(language='en', title='Test Page', slug='test-page')
        # Create placeholder with content
        placeholder = Placeholder.objects.create_for_object(page, 'blog_contents')
        ActionItem.objects.create_for_placeholder(
            placeholder,
            title='Click here',
            link='/test'
        )

        url = reverse('admin:pages_page_translate', args=(page.pk,))
        response = self.client.post(url, {
            'target_language': 'nl'
        })

        # Should redirect to new page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/change/'))

        # Check that new page was created
        new_page = Page.objects.get(slug='test-page', language='nl')
        self.assertIsNotNone(new_page)
        self.assertNotEqual(new_page.pk, page.pk)

    def test_translate_page_post_duplicate_slug(self):
        """Test translation fails when page with same slug/language exists."""
        page = PageFactory.create(language='en', slug='test-page')
        # Create existing page with same slug but different language
        PageFactory.create(language='nl', slug='test-page')

        url = reverse('admin:pages_page_translate', args=(page.pk,))
        response = self.client.post(url, {
            'target_language': 'nl'
        })

        # Should redirect back to original page with error
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(f'/change/'))

        # Verify no new page was created (should still be only 1 nl page)
        nl_pages = Page.objects.filter(slug='test-page', language='nl')
        self.assertEqual(nl_pages.count(), 1)  # Only the existing one

    def test_translate_page_post_invalid_form(self):
        """Test translation with invalid form data."""
        page = PageFactory.create(language='en')
        url = reverse('admin:pages_page_translate', args=(page.pk,))
        response = self.client.post(url, {
            'target_language': 'invalid'
        })

        # Should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')

    def test_translate_page_translates_title(self):
        """Test that page title is translated."""
        page = PageFactory.create(language='en', title='Hello World')

        with mock.patch('bluebottle.pages.admin.translate_text_cached') as mock_translate:
            mock_translate.return_value = {'value': 'Hallo Wereld', 'source_language': 'en'}

            url = reverse('admin:pages_page_translate', args=(page.pk,))
            self.client.post(url, {'target_language': 'nl'})

            # Check that title was translated
            mock_translate.assert_any_call('Hello World', 'nl')
            new_page = Page.objects.get(slug=page.slug, language='nl')
            self.assertEqual(new_page.title, 'Hallo Wereld')

    def test_translate_page_copies_page_properties(self):
        """Test that page properties are copied correctly."""
        from django.utils.timezone import now, timedelta
        page = PageFactory.create(
            language='en',
            status=Page.PageStatus.draft,
            full_page=True,
            show_title=False,
            publication_date=now() - timedelta(days=1),
            publication_end_date=now() + timedelta(days=1),
        )

        with mock.patch('bluebottle.pages.admin.translate_text_cached') as mock_translate:
            mock_translate.return_value = {'value': 'Translated', 'source_language': 'en'}

            url = reverse('admin:pages_page_translate', args=(page.pk,))
            self.client.post(url, {'target_language': 'nl'})

            new_page = Page.objects.get(slug=page.slug, language='nl')
            self.assertEqual(new_page.status, Page.PageStatus.draft)
            self.assertEqual(new_page.full_page, True)
            self.assertEqual(new_page.show_title, False)
            self.assertEqual(new_page.publication_date, page.publication_date)
            self.assertEqual(new_page.publication_end_date, page.publication_end_date)
            self.assertEqual(new_page.author, self.superuser)

    def test_translate_page_copies_and_translates_blocks(self):
        """Test that blocks are copied and translated."""
        page = PageFactory.create(language='en')
        placeholder = Placeholder.objects.create_for_object(page, 'blog_contents')
        ActionItem.objects.create_for_placeholder(
            placeholder,
            title='Original Title',
            link='/original'
        )

        with mock.patch('bluebottle.pages.utils.translate_text_cached') as mock_translate:
            def translation_side_effect(text, lang):
                if text == 'Original Title':
                    return {'value': 'Translated Title', 'source_language': 'en'}
                return {'value': text, 'source_language': 'en'}
            mock_translate.side_effect = translation_side_effect

            url = reverse('admin:pages_page_translate', args=(page.pk,))
            self.client.post(url, {'target_language': 'nl'})

            new_page = Page.objects.get(slug=page.slug, language='nl')
            new_placeholder = Placeholder.objects.get(
                parent_id=new_page.pk,
                slot='blog_contents'
            )
            new_items = list(new_placeholder.contentitems.all())
            self.assertEqual(len(new_items), 1)
            self.assertIsInstance(new_items[0], ActionItem)
            self.assertEqual(new_items[0].title, 'Translated Title')
            self.assertEqual(new_items[0].link, '/original')  # Non-text field unchanged

    def test_translate_page_requires_superuser(self):
        """Test that only superusers can access translate view."""
        from django.contrib.auth.models import Group
        staff_user = BlueBottleUserFactory.create(is_staff=True, is_superuser=False)
        staff_group = Group.objects.get(name='Staff')
        staff_group.user_set.add(staff_user)

        self.client.logout()
        self.client.force_login(staff_user)

        page = PageFactory.create(language='en')
        url = reverse('admin:pages_page_translate', args=(page.pk,))
        response = self.client.get(url)

        # Should be forbidden or redirect
        self.assertIn(response.status_code, [302, 403])

