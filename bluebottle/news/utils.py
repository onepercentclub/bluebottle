# -*- coding: utf-8 -*-
"""
Utilities for exporting and importing news items.
"""
from bluebottle.utils.content_import_export import (
    dump_content,
    export_image_field,
    import_content_items_from_data
)


def export_news_item_to_dict(news_item, request=None):
    main_image_data = export_image_field(news_item, 'main_image')

    return {
        'model': 'NewsItem',
        'app': 'news',
        'properties': {
            'title': news_item.title,
            'slug': news_item.slug,
            'status': news_item.status,
            'language': news_item.language,
            'main_image': main_image_data,
        },
        'data': dump_content(news_item.contents)
    }


def import_news_items_from_data(data):
    return import_content_items_from_data(
        data,
        model_name='NewsItem',
        lookup_fields=['language', 'slug'],
        slot='blog_contents'
    )
