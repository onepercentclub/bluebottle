# Generated by Django 3.2.20 on 2023-08-18 10:12

from django.db import migrations, IntegrityError


def migrate_related_reactions(old_wallpost, new_update, update_model):
    for reaction in old_wallpost.reactions.all():
        update_model.objects.create(
            created=reaction.created,
            activity_id=new_update.activity_id,
            message=reaction.text,
            author=reaction.author,
            parent=new_update
        )

def migrate_deed_wallposts(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Deed = apps.get_model('deeds', 'Deed')

    SystemWallpost = apps.get_model('wallposts', 'SystemWallpost')
    TextWallpost = apps.get_model('wallposts', 'TextWallpost')
    MediaWallpost = apps.get_model('wallposts', 'MediaWallpost')
    MediaWallpostPhoto = apps.get_model('wallposts', 'MediaWallpostPhoto')
    Reaction = apps.get_model('wallposts', 'Reaction')

    Update = apps.get_model('updates', 'Update')
    UpdateImage = apps.get_model('updates', 'UpdateImage')
    Image = apps.get_model('files', 'Image')
    deed_content_type = ContentType.objects.get_for_model(Deed)

    for wallpost in MediaWallpost.objects.filter(content_type=deed_content_type):
        update = Update.objects.create(
            created=wallpost.created,
            activity_id=wallpost.object_id,
            message=wallpost.text,
            video_url=wallpost.video_url,
            author=wallpost.author,
            notify=wallpost.email_followers
        )
        migrate_related_reactions(wallpost, update, Update)

        photos = MediaWallpostPhoto.objects.filter(mediawallpost_id=wallpost.pk, deleted__isnull=True)
        for photo in photos:
            try:
                image = Image.objects.create(
                    file=photo.photo,
                    owner=wallpost.author,
                    used=True
                )
                UpdateImage.objects.create(
                    image=image,
                    update=update
                )
                print(f'created image for update: {update.pk}')
            except (FileNotFoundError, IntegrityError):
                pass

    for wallpost in TextWallpost.objects.filter(content_type=deed_content_type):
        update = Update.objects.create(
            created=wallpost.created,
            activity_id=wallpost.object_id,
            message=wallpost.text,
            author=wallpost.author,
            notify=wallpost.email_followers
        )
        migrate_related_reactions(wallpost, update, Update)

    for wallpost in SystemWallpost.objects.filter(content_type=deed_content_type):
        update = Update.objects.create(
            created=wallpost.created,
            activity_id=wallpost.object_id,
            message=wallpost.text,
            author=wallpost.author,
            notify=wallpost.email_followers
        )
        migrate_related_reactions(wallpost, update, Update)


class Migration(migrations.Migration):

    dependencies = [
        ('updates', '0010_auto_20230812_0804'),
    ]

    operations = [
        migrations.RunPython(migrate_deed_wallposts, migrations.RunPython.noop)
    ]
