# -*- coding: utf-8 -*-
"""
Base utilities for exporting and importing content items with placeholder fields.
"""
import os
import traceback
from urllib.parse import urlparse

import requests
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.db import connection, models

from bluebottle.files.fields import ImageField as FileImageField
from bluebottle.files.models import Image
from bluebottle.members.models import Member
from bluebottle.utils.fields import ImageField as UtilImageField
from fluent_contents.extensions.model_fields import PluginImageField
from fluent_contents.models import Placeholder, ContentItem


def get_image_url(obj, field_name, request=None):
    try:
        image = getattr(obj, field_name, None)
        if image and hasattr(image, 'file'):
            if hasattr(image, 'file') and image.file:
                url = image.file.url if hasattr(image.file, 'url') else None
                if url:
                    return connection.tenant.build_absolute_url(url)
                return url
        elif image and hasattr(image, 'url'):
            url = image.url
            if url:
                if hasattr(connection, 'tenant') and connection.tenant:
                    return connection.tenant.build_absolute_url(url)
                elif not url.startswith(('http://', 'https://')):
                    return url
            return url
    except Exception:
        pass
    return None


def export_image_field(obj, field_name, request=None):
    """
    Export an image field from an object to a dictionary format.
    
    This function handles different types of image fields:
    - ForeignKey to Image model (returns {'image_url': url} or {'image_id': id})
    - FileField/ImageFieldFile (returns {'image_url': url})
    
    Args:
        obj: Model instance containing the image field
        field_name: Name of the image field
        request: Optional request object to build absolute URLs
        
    Returns:
        dict: Dictionary with 'image_url' or 'image_id' key, or None if no image
    """
    image = getattr(obj, field_name, None)
    if not image:
        return None
    
    # Try to get the image URL first
    image_url = get_image_url(obj, field_name, request=request)
    if image_url:
        return {'image_url': image_url}
    
    # Fallback: check if it's an Image model instance (has pk attribute)
    if hasattr(image, 'pk'):
        return {'image_id': image.pk}
    
    # Fallback: check if it's a FileField/ImageFieldFile (has url attribute)
    if hasattr(image, 'url'):
        url = image.url
        if url:
            # Build absolute URL
            if request:
                url = request.build_absolute_uri(url)
            elif hasattr(connection, 'tenant') and connection.tenant:
                url = connection.tenant.build_absolute_url(url)
            return {'image_url': url}
    
    return None


def download_image_from_url(image_url, base_url=None):
    """
    Download an image from a URL and return a ContentFile.

    Args:
        image_url: URL of the image to download
        base_url: Optional base URL to prepend if image_url is relative

    Returns:
        tuple: (ContentFile, filename) or (None, None) if download fails
    """
    try:
        # Handle relative URLs
        if base_url and not image_url.startswith(('http://', 'https://')):
            if not image_url.startswith('/'):
                image_url = '/' + image_url
            parsed_base = urlparse(base_url)
            image_url = f"{parsed_base.scheme}://{parsed_base.netloc}{image_url}"

        # Download the image
        response = requests.get(image_url, timeout=30, stream=True)
        response.raise_for_status()

        # Get filename from URL or Content-Disposition header
        filename = os.path.basename(urlparse(image_url).path)
        if not filename or '.' not in filename:
            # Try to get from Content-Disposition header
            content_disposition = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"\'')
            else:
                # Default filename based on content type
                content_type = response.headers.get('Content-Type', 'image/jpeg')
                ext = content_type.split('/')[-1] if '/' in content_type else 'jpg'
                filename = f"imported_image.{ext}"

        # Create ContentFile from downloaded content
        content = ContentFile(response.content)
        return content, filename
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")
        return None, None


def get_block_fields(block, request=None):
    """
    Extract serializable fields from a block, excluding internal Django fields.
    Handles image fields by exporting their URLs.

    Args:
        block: Content block instance
        request: Optional request object to build absolute URLs

    Returns:
        dict: Dictionary of serializable field values
    """
    fields = block.__dict__.copy()
    skip_fields = [
        'id', '_state', 'parent_type_id', 'parent_id',
        'polymorphic_ctype_id', 'contentitem_ptr_id',
        'placeholder_id', 'block_id', 'order_field',
        'order_field_name', '_block_cache', '_django_version']

    # Get the model's field definitions to check field types
    model_fields = {f.name: f for f in block._meta.get_fields()}

    # Check for image fields and export URLs
    for field_name in list(fields.keys()):
        if field_name in skip_fields:
            del fields[field_name]
            continue

        # Check if this field is an image field by looking at the model field definition
        is_image_field = False
        field_value = fields[field_name]

        if field_name in model_fields:
            field = model_fields[field_name]
            # Check if it's an ImageField (ForeignKey to Image) or ImageFieldFile
            if isinstance(field, (FileImageField, UtilImageField, PluginImageField)):
                is_image_field = True
        elif field_value and hasattr(field_value, '__class__'):
            # Fallback: check the value itself
            class_name = field_value.__class__.__name__
            if 'Image' in class_name or (hasattr(field_value, 'file') or hasattr(field_value, 'url')):
                is_image_field = True

        if is_image_field:
            # Get the actual field value using getattr to ensure we get the related object
            actual_value = getattr(block, field_name, None)

            if actual_value:
                # Export the image field using the shared function
                image_data = export_image_field(block, field_name, request=request)
                if image_data:
                    # If we got image_id, store it as field_name_id for consistency
                    if 'image_id' in image_data:
                        fields[field_name + '_id'] = image_data['image_id']
                        del fields[field_name]
                    else:
                        fields[field_name] = image_data
                else:
                    # No image data could be extracted, remove from export
                    del fields[field_name]
            else:
                # No image set, remove from export
                del fields[field_name]

    return fields


def dump_content(placeholder_field, request=None):
    """
    Dump all content blocks and items from a placeholder field.

    Args:
        placeholder_field: PlaceholderField instance (e.g., page.content or news_item.contents)
        request: Optional request object to build absolute URLs

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
                    'data': get_block_fields(item, request=request)
                })
        fields = get_block_fields(block, request=request)
        data.append({
            'model': block.__class__.__name__,
            'app': block.__class__._meta.app_label,
            'fields': fields,
            'items': items
        })
    return data


def create_content_block(block_data, placeholder, base_url=None):
    """
    Create a content block from imported data.

    Args:
        block_data: Dictionary containing block data
        placeholder: Placeholder instance
        base_url: Optional base URL for relative image URLs
    """

    # Handle image fields in block data
    block_fields = block_data['fields'].copy()
    image_fields = {}

    for key, value in list(block_fields.items()):
        if isinstance(value, dict) and 'image_url' in value:
            image_fields[key] = value
            del block_fields[key]

    model = apps.get_model(block_data['app'], block_data['model'])
    content_type = ContentType.objects.get_for_model(model)

    content_block = model.objects.create_for_placeholder(
        placeholder,
        polymorphic_ctype=content_type,
        **block_fields
    )

    # Handle image imports for the block
    for field_name, image_data in image_fields.items():
        handle_image_import(field_name, image_data, content_block, base_url=base_url)

    if 'items' in block_data:
        for item_data in block_data['items']:
            item_model = apps.get_model(item_data['app'], item_data['model'])
            item_fields = item_data['data'].copy()
            item_image_fields = {}

            # Separate image fields from item data
            for key, value in list(item_fields.items()):
                if isinstance(value, dict) and 'image_url' in value:
                    item_image_fields[key] = value
                    del item_fields[key]

            item = item_model.objects.create(
                block=content_block,
                **item_fields
            )

            # Handle image imports for items
            for field_name, image_data in item_image_fields.items():
                handle_image_import(field_name, image_data, item, base_url=base_url)


def handle_image_import(field_name, image_data, item, base_url=None):
    """
    Handle importing an image field from exported data.

    Args:
        field_name: Name of the image field
        image_data: Dictionary with 'image_url' key or image ID
        item: Model instance to set the image on
        base_url: Optional base URL for relative image URLs

    Returns:
        bool: True if image was successfully imported, False otherwise
    """
    if not image_data:
        return False

    # Check the field type to determine how to handle it
    field = item._meta.get_field(field_name)
    is_foreign_key_to_image = isinstance(field, FileImageField) or (
        isinstance(field, models.ForeignKey) and
        hasattr(field.remote_field, 'model') and
        field.remote_field.model == Image
    )

    # Check if it's an image URL to download
    if isinstance(image_data, dict) and 'image_url' in image_data:
        image_url = image_data['image_url']
        if not image_url:
            return False

        try:
            # Download the image
            content_file, filename = download_image_from_url(image_url, base_url=base_url)
            if not content_file:
                return False

            if is_foreign_key_to_image:
                # This is a ForeignKey to Image model - create Image instance
                # Get or create a Member for the image owner (use first superuser or first member)
                owner = Member.objects.filter(is_superuser=True).first()
                if not owner:
                    owner = Member.objects.first()

                if not owner:
                    print(f"Error importing image for {field_name}: No Member found to assign as owner")
                    return False

                # Create and save Image instance first
                image = Image(owner=owner)
                image.save()  # Save the instance first
                # Then assign the file
                image.file.save(filename, content_file, save=True)

                # Set the image field on the item and save
                setattr(item, field_name, image)
                item.save()
            else:
                # This is a FileField - assign the file directly
                # Ensure the item is saved first if it's new
                if item.pk is None:
                    item.save()
                getattr(item, field_name).save(filename, content_file, save=True)
                item.save()

            return True
        except Exception as e:
            print(f"Error importing image for {field_name}: {e}")
            traceback.print_exc()
            return False
    elif isinstance(image_data, (int, str)) and is_foreign_key_to_image:
        # Try to use existing image ID (only for ForeignKey fields)
        try:
            image = Image.objects.get(pk=image_data)
            setattr(item, field_name, image)
            item.save()
            return True
        except Image.DoesNotExist:
            return False

    return False


def import_content_item_from_data(item_data, lookup_fields, slot='blog_contents', base_url=None):
    """
    Import a single content item from data dictionary.

    Args:
        item_data: Dictionary containing item data
        lookup_fields: List of fields to use for get_or_create lookup
        slot: Placeholder slot name (default: 'blog_contents')
        base_url: Optional base URL for relative image URLs

    Returns:
        tuple: (item, created) - Item instance and whether it was created
    """
    model = apps.get_model(item_data['app'], item_data['model'])

    if item_data['properties'].get('publication_date'):
        item_data['properties']['publication_date'] += '+00:00'

    properties = item_data['properties'].copy()
    image_fields = {}

    for key, value in list(properties.items()):
        # Check if this is an image field (contains image_url or is a ForeignKey to Image)
        if isinstance(value, dict) and 'image_url' in value:
            image_fields[key] = value
            del properties[key]

    # Build lookup kwargs
    lookup_kwargs = {}
    for field in lookup_fields:
        lookup_kwargs[field] = properties[field]

    # Create or update item
    item, created = model.objects.get_or_create(
        **lookup_kwargs,
        defaults=properties
    )

    # Update existing items with new properties
    if not created:
        for key, value in properties.items():
            setattr(item, key, value)

    # Handle image imports
    for field_name, image_data in image_fields.items():
        handle_image_import(field_name, image_data, item, base_url=base_url)

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
        create_content_block(block_data, placeholder, base_url=base_url)

    return item, created


def import_content_items_from_data(data, model_name, lookup_fields, slot='blog_contents', base_url=None):
    """
    Import content items from a list of data dictionaries.

    Args:
        data: List of dictionaries containing item data
        model_name: Name of the model to import (e.g., 'Page', 'NewsItem')
        lookup_fields: List of fields to use for get_or_create lookup
        slot: Placeholder slot name (default: 'blog_contents')
        base_url: Optional base URL for relative image URLs

    Returns:
        dict: Dictionary with 'imported', 'updated' counts, and 'last_item' instance
    """
    imported_count = 0
    updated_count = 0
    last_item = None

    for item_data in data:
        if item_data['model'] == model_name:
            item, created = import_content_item_from_data(
                item_data, lookup_fields, slot, base_url=base_url
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
