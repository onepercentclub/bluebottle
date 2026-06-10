import json

from django.contrib.auth.models import Permission
from django.urls import reverse

from bluebottle.content.models import ContentBlock, ContentPage
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


class ContentPageAPITestCase(BluebottleTestCase):

    def setUp(self):
        super(ContentPageAPITestCase, self).setUp()
        self.init_projects()
        self.page = ContentPage.objects.create(
            language='en',
            slug='about',
            title='About us',
            status='published',
        )
        self.editor = BlueBottleUserFactory.create()
        perm = Permission.objects.filter(codename='api_change_page').first()
        if perm:
            self.editor.user_permissions.add(perm)
        self.text_block = ContentBlock.objects.create(
            page=self.page,
            block_type=ContentBlock.BlockType.text,
            sort_order=1,
            text='<p>Original text</p>',
        )

    def _post_block(self, url, payload, token=None):
        kwargs = {
            'format': None,
            'content_type': 'application/vnd.api+json',
        }
        if token:
            kwargs['token'] = token
        return self.client.post(url, json.dumps(payload), **kwargs)

    def test_title_block_serializer_resource_type(self):
        block = ContentBlock.objects.create(
            page=self.page,
            block_type=ContentBlock.BlockType.title,
            sort_order=2,
            title_text='Hello',
            title_level=2,
        )
        from bluebottle.content.serializers import serialize_content_block
        data = serialize_content_block(block)
        self.assertEqual(data['type'], 'content/blocks/title')
        self.assertEqual(data['attributes']['title-text'], 'Hello')

    def test_page_list_requires_editor_permission(self):
        url = reverse('content-page-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.get(
            url,
            token='JWT {}'.format(self.editor.get_jwt_token()),
            HTTP_X_APPLICATION_LANGUAGE='en'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['attributes']['title'], 'About us')
        self.assertIn('full-page', data[0]['attributes'])
        self.assertIn('show-title', data[0]['attributes'])
        self.assertTrue(data[0]['meta']['permissions']['PATCH'])

    def test_page_detail_includes_permissions(self):
        url = reverse('content-page-detail', args=(self.page.slug,))
        response = self.client.get(
            url,
            token='JWT {}'.format(self.editor.get_jwt_token()),
            HTTP_ACCEPT_LANGUAGE='en'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['data']['meta']['permissions']['PATCH'])
        self.assertIn('/admin/content/contentpage/', response.json()['data']['meta']['admin-url'])

    def test_page_detail_includes_block_attributes(self):
        ContentBlock.objects.create(
            page=self.page,
            block_type=ContentBlock.BlockType.title,
            sort_order=2,
            title_text='Section title',
            title_level=2,
        )
        url = reverse('content-page-detail', args=(self.page.slug,))
        response = self.client.get(
            url,
            token='JWT {}'.format(self.editor.get_jwt_token()),
            HTTP_ACCEPT_LANGUAGE='en'
        )
        self.assertEqual(response.status_code, 200)
        included = response.json().get('included', [])
        title_blocks = [
            item for item in included
            if item['type'] == 'content/blocks/title'
        ]
        self.assertEqual(len(title_blocks), 1)
        self.assertEqual(title_blocks[0]['attributes']['title-text'], 'Section title')
        self.assertEqual(title_blocks[0]['attributes']['title-level'], 2)

    def test_create_all_block_types(self):
        url = reverse('content-block-create', args=(self.page.slug,))
        token = 'JWT {}'.format(self.editor.get_jwt_token())
        block_types = [
            ('content/blocks/title', {'title_text': 'Hello', 'title_level': 2}),
            ('content/blocks/text', {'text': '<p>Text</p>'}),
            ('content/blocks/image', {'align': 'center'}),
            ('content/blocks/text-image', {'text': '<p>Mix</p>', 'align': 'left', 'ratio': 6}),
            ('content/blocks/video', {'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'}),
            ('content/blocks/button', {'button_label': 'Click', 'button_url': 'https://example.com'}),
            ('content/blocks/spacer', {'spacer_size': 'large'}),
        ]
        for resource_type, attributes in block_types:
            response = self._post_block(
                url,
                {'data': {'type': resource_type, 'attributes': attributes}},
                token=token,
            )
            self.assertEqual(
                response.status_code,
                201,
                msg='Failed for {}: {}'.format(resource_type, response.content)
            )
            data = response.json()['data']
            self.assertEqual(data['type'], resource_type)
            self.assertIsInstance(data['id'], str)
            self.assertIn('attributes', data)

    def test_patch_text_block(self):
        url = reverse('content-block-detail', args=(self.text_block.pk,))
        response = self.client.patch(
            url,
            json.dumps({
                'data': {
                    'type': 'content/blocks/text',
                    'id': str(self.text_block.pk),
                    'attributes': {
                        'text': '<p>Updated text</p>'
                    }
                }
            }),
            format=None,
            content_type='application/vnd.api+json',
            token='JWT {}'.format(self.editor.get_jwt_token())
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['type'], 'content/blocks/text')
        self.assertIsInstance(data['id'], str)
        self.assertEqual(
            data['attributes']['text'],
            '<p>Updated text</p>'
        )

    def test_delete_text_block(self):
        url = reverse('content-block-detail', args=(self.text_block.pk,))
        response = self.client.delete(
            url,
            token='JWT {}'.format(self.editor.get_jwt_token())
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ContentBlock.objects.filter(pk=self.text_block.pk).exists())

    def test_create_block_insert_after(self):
        second_block = ContentBlock.objects.create(
            page=self.page,
            block_type=ContentBlock.BlockType.text,
            sort_order=2,
            text='<p>Second</p>',
        )
        url = reverse('content-block-create', args=(self.page.slug,))
        response = self._post_block(
            url,
            {
                'data': {
                    'type': 'content/blocks/text',
                    'attributes': {'text': '<p>Inserted</p>'},
                    'meta': {'insert-after': str(self.text_block.pk)},
                }
            },
            token='JWT {}'.format(self.editor.get_jwt_token())
        )
        self.assertEqual(response.status_code, 201)
        new_block_id = response.json()['data']['id']

        page_url = reverse('content-page-detail', args=(self.page.slug,))
        page_response = self.client.get(
            page_url,
            token='JWT {}'.format(self.editor.get_jwt_token()),
            HTTP_ACCEPT_LANGUAGE='en'
        )
        block_ids = [
            item['id']
            for item in page_response.json()['data']['relationships']['blocks']['data']
        ]
        self.assertEqual(
            block_ids,
            [str(self.text_block.pk), new_block_id, str(second_block.pk)]
        )

    def test_create_page(self):
        url = reverse('content-page-list')
        response = self.client.post(
            url,
            json.dumps({
                'data': {
                    'type': 'content/pages',
                    'attributes': {
                        'title': 'New page',
                        'slug': 'new-page',
                        'status': 'draft',
                        'show_title': True,
                        'full_page': False,
                    },
                }
            }),
            format=None,
            content_type='application/vnd.api+json',
            token='JWT {}'.format(self.editor.get_jwt_token()),
            HTTP_X_APPLICATION_LANGUAGE='en',
        )
        self.assertEqual(
            response.status_code,
            201,
            msg=response.content.decode(),
        )
        data = response.json()['data']
        self.assertEqual(data['type'], 'content/pages')
        self.assertEqual(data['id'], 'new-page')
        self.assertEqual(data['attributes']['title'], 'New page')
        self.assertTrue(
            ContentPage.objects.filter(slug='new-page', language='en').exists()
        )

    def test_create_page_with_language(self):
        url = reverse('content-page-list')
        response = self.client.post(
            url,
            json.dumps({
                'data': {
                    'type': 'content/pages',
                    'attributes': {
                        'title': 'Dutch page',
                        'slug': 'dutch-page',
                        'language': 'nl',
                        'status': 'draft',
                    },
                }
            }),
            format=None,
            content_type='application/vnd.api+json',
            token='JWT {}'.format(self.editor.get_jwt_token()),
            HTTP_X_APPLICATION_LANGUAGE='en',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['data']['attributes']['language'], 'nl')

    def test_patch_page_settings(self):
        url = reverse('content-page-detail', args=(self.page.slug,))
        response = self.client.patch(
            url,
            json.dumps({
                'data': {
                    'type': 'content/pages',
                    'id': self.page.slug,
                    'attributes': {
                        'title': 'Renamed page',
                        'status': 'published',
                    },
                }
            }),
            format=None,
            content_type='application/vnd.api+json',
            token='JWT {}'.format(self.editor.get_jwt_token()),
            HTTP_ACCEPT_LANGUAGE='en',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['data']['attributes']['title'],
            'Renamed page',
        )
        self.page.refresh_from_db()
        self.assertEqual(self.page.title, 'Renamed page')
        self.assertEqual(self.page.status, 'published')

    def test_create_block_forbidden_for_anonymous(self):
        self.client.credentials()
        url = reverse('content-block-create', args=(self.page.slug,))
        response = self._post_block(
            url,
            {
                'data': {
                    'type': 'content/blocks/text',
                    'attributes': {'text': '<p>New</p>'}
                }
            },
        )
        self.assertEqual(response.status_code, 401)
