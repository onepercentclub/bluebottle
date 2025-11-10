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


def copy_and_translate_blocks(source_page, target_page, target_language):
    """Copy blocks from source page to target page and translate text fields."""
    # Get source placeholder (it should exist, but handle gracefully)
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

    # Get or create target placeholder
    target_content_type = ContentType.objects.get_for_model(target_page)
    target_placeholder, _ = Placeholder.objects.get_or_create(
        parent_id=target_page.pk,
        parent_type_id=target_content_type.pk,
        slot='blog_contents',
        role='m'
    )

    # Get all content blocks from source
    source_blocks = dump_content(source_page.body)

    # Process and translate each block
    for block_data in source_blocks:
        # Translate text fields in block
        translated_fields = _translate_block_fields(
            block_data['fields'], target_language
        )
        block_data['fields'] = translated_fields

        # Translate items if they exist
        if 'items' in block_data:
            for item_data in block_data['items']:
                translated_item_fields = _translate_block_fields(
                    item_data['data'], target_language
                )
                item_data['data'] = translated_item_fields

        # Create the block in target placeholder
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

        # Skip image fields and non-text fields
        if isinstance(value, dict) and 'image_url' in value:
            translated_fields[key] = value
            continue

        # Check if this looks like a text field
        is_text_field = any(pattern in key.lower() for pattern in text_field_patterns)

        if is_text_field and isinstance(value, str) and value.strip():
            # Translate the entire block as-is (including HTML)
            translated_value = translate_text_cached(value, target_language)['value']
            translated_fields[key] = translated_value
        else:
            # Keep non-text fields as-is
            translated_fields[key] = value

    return translated_fields
