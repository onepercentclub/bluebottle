# -*- coding: utf-8 -*-
"""
Utilities for exporting and importing news items.
"""
from bluebottle.utils.content_import_export import (
    dump_content,
    import_content_items_from_data
)


def export_news_item_to_dict(news_item):
    """
    Export a news item to a dictionary in the format expected by import functions.
    
    Args:
        news_item: NewsItem instance
        
    Returns:
        dict: Dictionary containing news item export data
    """
    return {
        'model': 'NewsItem',
        'app': 'news',
        'properties': {
            'title': news_item.title,
            'slug': news_item.slug,
            'status': news_item.status,
            'language': news_item.language,
            'main_image': str(news_item.main_image) if news_item.main_image else None,
            'allow_comments': getattr(news_item, 'allow_comments', True),
            'publication_date': news_item.publication_date.strftime('%Y-%m-%d %H:%M') if news_item.publication_date else None,
            'publication_end_date': news_item.publication_end_date.strftime('%Y-%m-%d %H:%M') if news_item.publication_end_date else None,
        },
        'data': dump_content(news_item.contents)
    }


def import_news_items_from_data(data):
    """
    Import news items from a list of news data dictionaries.
    
    Args:
        data: List of dictionaries containing news item data
        
    Returns:
        dict: Dictionary with 'imported', 'updated' counts, and 'last_item' instance
    """
    return import_content_items_from_data(
        data,
        model_name='NewsItem',
        lookup_fields=['language', 'slug'],
        slot='blog_contents'
    )

