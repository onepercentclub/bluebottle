# -*- coding: utf-8 -*-
"""
Utilities for exporting and importing pages.
"""
from django.contrib.contenttypes.models import ContentType
from fluent_contents.models import Placeholder

from bluebottle.translations.utils import translate_text_cached
from bluebottle.utils.content_import_export import (
    dump_content,
    import_content_items_from_data,
    create_content_block
)


def export_page_to_dict(page, request=None):
    return {
        'model': 'Page',
        'app': 'pages',
        'properties': {
            'title': page.title,
            'slug': page.slug,
            'status': page.status,
            'language': page.language,
            'full_page': page.full_page,
            'show_title': getattr(page, 'show_title', True),
        },
        'data': dump_content(page.content)
    }


def import_pages_from_data(data):
    return import_content_items_from_data(
        data,
        model_name='Page',
        lookup_fields=['language', 'slug'],
        slot='blog_contents'
    )


def create_translated_page(source_page, target_language, author):
    translated_title = translate_text_cached(source_page.title, target_language)['value']

    new_page = source_page.__class__.objects.create(
        title=translated_title,
        slug=source_page.slug,
        language=target_language,
        author=author,
        status=source_page.status,
        full_page=source_page.full_page,
        show_title=source_page.show_title,
        publication_date=source_page.publication_date,
        publication_end_date=source_page.publication_end_date,
    )

    copy_and_translate_blocks(source_page, new_page, target_language)

    return new_page


def copy_and_translate_blocks(source_page, target_page, target_language):
    """Copy blocks from source page to target page and translate text fields."""
    source_content_type = ContentType.objects.get_for_model(source_page)
    try:
        Placeholder.objects.get(
            parent_id=source_page.pk,
            parent_type_id=source_content_type.pk,
            slot='blog_contents'
        )
    except Placeholder.DoesNotExist:
        target_content_type = ContentType.objects.get_for_model(target_page)
        Placeholder.objects.get_or_create(
            parent_id=target_page.pk,
            parent_type_id=target_content_type.pk,
            slot='blog_contents',
            role='m'
        )
        return

    target_content_type = ContentType.objects.get_for_model(target_page)
    target_placeholder, _ = Placeholder.objects.get_or_create(
        parent_id=target_page.pk,
        parent_type_id=target_content_type.pk,
        slot='blog_contents',
        role='m'
    )

    source_blocks = dump_content(source_page.body)

    for block_data in source_blocks:
        translated_fields = _translate_block_fields(
            block_data['fields'], target_language
        )
        block_data['fields'] = translated_fields

        if 'items' in block_data:
            for item_data in block_data['items']:
                translated_item_fields = _translate_block_fields(
                    item_data['data'], target_language
                )
                item_data['data'] = translated_item_fields

        create_content_block(block_data, target_placeholder)


def _translate_block_fields(fields, target_language):
    """Translate text fields in block data."""
    translated_fields = {}
    text_field_patterns = [
        'text', 'title', 'heading', 'subtitle', 'description',
        'content', 'caption', 'label', 'name', 'body'
    ]

    for key, value in fields.items():
        if value is None:
            translated_fields[key] = None
            continue

        if isinstance(value, dict) and 'image_url' in value:
            translated_fields[key] = value
            continue

        is_text_field = any(pattern in key.lower() for pattern in text_field_patterns)

        if is_text_field and isinstance(value, str) and value.strip():
            translated_value = translate_text_cached(value, target_language)['value']
            translated_fields[key] = translated_value
        else:
            translated_fields[key] = value

    return translated_fields
