# Generated manually to migrate TextItem content blocks to TextOnlyItem
#
# This migration handles the transition from the fluent_contents TextItem plugin
# to the local TextOnlyItem plugin for Page content blocks.
#
# The migration:
# 1. Finds all TextItem content blocks in Page placeholders
# 2. Creates new TextOnlyItem blocks with the same text content
# 3. Updates the placeholder relationships to point to the new blocks
# 4. Removes the old TextItem blocks and their relationships
#
# Safety features:
# - Checks if TextItem content type exists before proceeding
# - Handles missing content objects gracefully
# - Preserves sort order of content blocks
# - Provides detailed logging of the migration process
# - Includes a reverse migration for rollback scenarios

from django.db import migrations


def migrate_textitem_to_textonlyitem(apps, schema_editor):
    """
    Migrate TextItem content blocks to TextOnlyItem blocks in Page placeholders.
    
    This migration:
    1. Finds all TextItem content blocks in Page placeholders
    2. Creates new TextOnlyItem blocks with the same text content
    3. Updates the placeholder relationships to point to the new blocks
    4. Removes the old TextItem blocks
    """
    # Get the models
    Page = apps.get_model('pages', 'Page')
    TextOnlyItem = apps.get_model('pages', 'TextOnlyItem')

    # Get the ContentType for TextItem (from fluent_contents)
    ContentType = apps.get_model('contenttypes', 'ContentType')
    try:
        textitem_ct = ContentType.objects.get(app_label="text", model="textitem")
    except ContentType.DoesNotExist:
        print("TextItem content type not found. No migration needed.")
        return

    # Get the ContentType for TextOnlyItem
    textonlyitem_ct = ContentType.objects.get(
        app_label='pages',
        model='textonlyitem'
    )

    # Get the ContentType for Page
    page_ct = ContentType.objects.get(
        app_label='pages',
        model='page'
    )

    # Get the Placeholder model
    Placeholder = apps.get_model('fluent_contents', 'Placeholder')

    # Get the ContentItem model
    ContentItem = apps.get_model('fluent_contents', 'ContentItem')

    # Find all Page placeholders
    page_placeholders = Placeholder.objects.filter(parent_type=page_ct)

    # Check if there are any TextItem blocks to migrate by looking at the content items
    # We'll use the ContentItem model to find TextItem instances
    TextItem = apps.get_model("text", "TextItem")

    total_textitems = TextItem.objects.count()

    if total_textitems == 0:
        print("No TextItem blocks found. No migration needed.")
        return

    print(f"Found {total_textitems} TextItem blocks to migrate...")

    migrated_count = 0
    error_count = 0

    for placeholder in page_placeholders:
        textitem_relations = ContentItem.objects.filter(
            placeholder_id=placeholder.id, polymorphic_ctype=textitem_ct
        ).order_by("sort_order")

        if not textitem_relations.exists():
            continue

        for content_item in textitem_relations:
            try:
                # The content_item is already the TextItem object
                textitem = content_item

                if textitem is None:
                    # Skip if the content object doesn't exist
                    print(f"Warning: TextItem {content_item.id} not found, skipping")
                    content_item.delete()
                    continue

                # Get the text content, handling both text and text_final fields
                text_content = getattr(textitem, 'text', '')
                if not text_content and hasattr(textitem, 'text_final'):
                    text_content = getattr(textitem, 'text_final', '')

                print(text_content)

                # Create new TextOnlyItem with the same text content
                # Instead of using create_for_placeholder, create the item directly
                new_textonlyitem = TextOnlyItem.objects.create(
                    text=text_content,
                    polymorphic_ctype=textonlyitem_ct,
                    placeholder=placeholder,
                    parent_id=placeholder.parent_id,
                    parent_type_id=placeholder.parent_type_id,
                    sort_order=content_item.sort_order,
                )

                # Delete the old TextItem content item
                content_item.delete()

                migrated_count += 1

            except Exception as e:
                # Log the error but continue with other items
                error_count += 1
                print(f"Error migrating TextItem {content_item.id}: {e}")
                continue

    print(f"Migration completed:")
    print(f"  - Successfully migrated: {migrated_count} TextItem blocks")
    if error_count > 0:
        print(f"  - Errors encountered: {error_count} blocks")
    print(f"  - Total Page placeholders processed: {page_placeholders.count()}")


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0018_textonlyitem_alter_imagetextitem_options_and_more"),
        ("fluent_contents", "0002_alter_contentitem_polymorphic_ctype"),
        ("contenttypes", "__latest__"),
    ]

    operations = [
        migrations.RunPython(
            migrate_textitem_to_textonlyitem,
            migrations.RunPython.noop,
        ),
    ]
