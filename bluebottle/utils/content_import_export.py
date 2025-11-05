# -*- coding: utf-8 -*-
"""
Base utilities for exporting and importing content items with placeholder fields.
"""
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from fluent_contents.models import Placeholder, ContentItem


def get_block_fields(block):
    """
    Extract serializable fields from a block, excluding internal Django fields.
    
    Args:
        block: Content block instance
        
    Returns:
        dict: Dictionary of serializable field values
    """
    fields = block.__dict__.copy()
    skip_fields = [
        'id', '_state', 'parent_type_id', 'parent_id',
        'polymorphic_ctype_id', 'contentitem_ptr_id',
        'placeholder_id', 'block_id', 'order_field',
        'order_field_name', '_block_cache', '_django_version']
    for field in skip_fields:
        if field in fields:
            del fields[field]
    return fields


def dump_content(placeholder_field):
    """
    Dump all content blocks and items from a placeholder field.
    
    Args:
        placeholder_field: PlaceholderField instance (e.g., page.content or news_item.contents)
        
    Returns:
        list: List of dictionaries containing block data
    """
    data = []
    for block in placeholder_field.get_content_items():
        items = []
        if hasattr(block, 'items'):
            for item in block.items.all():
                items.append({
                    'model': item.__class__.__name__,
                    'app': item.__class__._meta.app_label,
                    'data': get_block_fields(item)
                })
        fields = get_block_fields(block)
        data.append({
            'model': block.__class__.__name__,
            'app': block.__class__._meta.app_label,
            'fields': fields,
            'items': items
        })
    return data


def create_content_block(block_data, placeholder):
    """
    Create a content block from imported data.
    
    Args:
        block_data: Dictionary containing block data
        placeholder: Placeholder instance
    """
    model = apps.get_model(block_data['app'], block_data['model'])
    content_type = ContentType.objects.get_for_model(model)

    content_block = model.objects.create_for_placeholder(
        placeholder,
        polymorphic_ctype=content_type,
        **block_data['fields']
    )

    if 'items' in block_data:
        for item_data in block_data['items']:
            item_model = apps.get_model(item_data['app'], item_data['model'])
            item_model.objects.create(
                block=content_block,
                **item_data['data']
            )


def import_content_item_from_data(item_data, lookup_fields, slot='blog_contents'):
    """
    Import a single content item from data dictionary.
    
    Args:
        item_data: Dictionary containing item data
        lookup_fields: List of fields to use for get_or_create lookup
        slot: Placeholder slot name (default: 'blog_contents')
        
    Returns:
        tuple: (item, created) - Item instance and whether it was created
    """
    from bluebottle.utils.models import Language
    
    model = apps.get_model(item_data['app'], item_data['model'])
    language = Language.objects.get(code=item_data['properties']['language'])
    
    # Make publication_date tz aware (same as loadpages.py)
    if item_data['properties'].get('publication_date'):
        item_data['properties']['publication_date'] += '+00:00'
    
    # Build lookup kwargs
    lookup_kwargs = {}
    for field in lookup_fields:
        lookup_kwargs[field] = item_data['properties'][field]
    
    # Create or update item
    item, created = model.objects.get_or_create(
        **lookup_kwargs,
        defaults=item_data['properties']
    )
    
    # Update existing items with new properties
    if not created:
        for key, value in item_data['properties'].items():
            setattr(item, key, value)
        item.save()
    
    item_type = ContentType.objects.get_for_model(item)
    
    (placeholder, _created) = Placeholder.objects.get_or_create(
        parent_id=item.pk,
        parent_type_id=item_type.pk,
        slot=slot,
        role='m'
    )
    
    # Delete existing content items
    for content_item in ContentItem.objects.filter(parent_id=item.pk, parent_type=item_type):
        content_item.delete()
    
    # Create new content blocks
    for block_data in item_data['data']:
        create_content_block(block_data, placeholder)
    
    return item, created


def import_content_items_from_data(data, model_name, lookup_fields, slot='blog_contents'):
    """
    Import content items from a list of data dictionaries.
    
    Args:
        data: List of dictionaries containing item data
        model_name: Name of the model to import (e.g., 'Page', 'NewsItem')
        lookup_fields: List of fields to use for get_or_create lookup
        slot: Placeholder slot name (default: 'blog_contents')
        
    Returns:
        dict: Dictionary with 'imported', 'updated' counts, and 'last_item' instance
    """
    imported_count = 0
    updated_count = 0
    last_item = None
    
    for item_data in data:
        if item_data['model'] == model_name:
            item, created = import_content_item_from_data(
                item_data, lookup_fields, slot
            )
            last_item = item  # Keep track of the last processed item
            if created:
                imported_count += 1
            else:
                updated_count += 1
    
    return {
        'imported': imported_count,
        'updated': updated_count,
        'last_item': last_item
    }

