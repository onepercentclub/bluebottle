# -*- coding: utf-8 -*-
"""
Utilities for exporting and importing news items.
"""
from bluebottle.utils.content_import_export import (
    dump_content,
    import_content_items_from_data
)


def export_news_item_to_dict(news_item, request=None):
    """
    Export a news item to a dictionary in the format expected by import functions.
    
    Args:
        news_item: NewsItem instance
        request: Optional request object to build absolute URLs for images
        
    Returns:
        dict: Dictionary containing news item export data
    """
    from bluebottle.utils.content_import_export import get_image_url
    
    # Handle main_image export
    main_image_data = None
    main_image = getattr(news_item, 'main_image', None)
    
    # Try to get the image URL first
    image_url = get_image_url(news_item, 'main_image', request=request)
    if image_url:
        main_image_data = {'_image_url': image_url}
    elif main_image:
        # Check if main_image is actually an Image model instance (has pk attribute)
        if hasattr(main_image, 'pk'):
            # Fallback to ID if URL couldn't be determined
            main_image_data = {'_image_id': main_image.pk}
        elif hasattr(main_image, 'url'):
            # It's a FileField/ImageFieldFile, get URL and make absolute
            from django.db import connection
            url = main_image.url
            if url:
                if request:
                    url = request.build_absolute_uri(url)
                elif hasattr(connection, 'tenant') and connection.tenant:
                    url = connection.tenant.build_absolute_url(url)
                main_image_data = {'_image_url': url}
    
    return {
        'model': 'NewsItem',
        'app': 'news',
        'properties': {
            'title': news_item.title,
            'slug': news_item.slug,
            'status': news_item.status,
            'language': news_item.language,
            'main_image': main_image_data,
            'allow_comments': getattr(news_item, 'allow_comments', True),
            'publication_date': news_item.publication_date.strftime('%Y-%m-%d %H:%M') if news_item.publication_date else None,
            'publication_end_date': news_item.publication_end_date.strftime('%Y-%m-%d %H:%M') if news_item.publication_end_date else None,
        },
        'data': dump_content(news_item.contents, request=request)
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

