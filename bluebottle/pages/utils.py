# -*- coding: utf-8 -*-
"""
Utilities for exporting and importing pages.
"""
from bluebottle.utils.content_import_export import (
    dump_content,
    import_content_items_from_data
)


def export_page_to_dict(page, request=None):
    """
    Export a page to a dictionary in the format expected by import functions.
    
    Args:
        page: Page instance
        request: Optional request object to build absolute URLs for images
        
    Returns:
        dict: Dictionary containing page export data
    """
    return {
        'model': 'Page',
        'app': 'pages',
        'properties': {
            'title': page.title,
            'slug': page.slug,
            'status': page.status,
            'language': page.language,
            'full_page': page.full_page,
            'publication_date': page.publication_date.strftime('%Y-%m-%d %H:%M') if page.publication_date else None,
            'publication_end_date': page.publication_end_date.strftime('%Y-%m-%d %H:%M') if page.publication_end_date else None,
            'show_title': getattr(page, 'show_title', True),
        },
        'data': dump_content(page.content, request=request)
    }


def import_pages_from_data(data):
    """
    Import pages from a list of page data dictionaries.
    
    Args:
        data: List of dictionaries containing page data
        
    Returns:
        dict: Dictionary with 'imported', 'updated' counts, and 'last_page' instance
    """
    result = import_content_items_from_data(
        data,
        model_name='Page',
        lookup_fields=['language', 'slug'],
        slot='blog_contents'
    )
    # Rename 'last_item' to 'last_page' for consistency
    result['last_page'] = result.pop('last_item')
    return result

