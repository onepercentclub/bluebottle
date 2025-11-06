# -*- coding: utf-8 -*-
"""
Utilities for exporting and importing pages.
"""
from bluebottle.utils.content_import_export import (
    dump_content,
    import_content_items_from_data
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
