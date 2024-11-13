# Generated by Django 3.2.20 on 2024-10-18 09:49

from django.db import migrations, connection

from bluebottle.activities.documents import activity
from bluebottle.initiatives.models import Initiative


def migrate_related_reactions(old_wallpost, new_update, update_model):
    for reaction in old_wallpost.reactions.all():
        update_model.objects.create(
            created=reaction.created,
            activity_id=new_update.activity_id,
            message=reaction.text,
            author=reaction.author,
            parent=new_update
        )


def migrate_initiative_wallposts(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Initiative = apps.get_model("initiatives", "Initiative")

    MediaWallpost = apps.get_model("wallposts", "MediaWallpost")
    MediaWallpostPhoto = apps.get_model("wallposts", "MediaWallpostPhoto")
    TextWallpost = apps.get_model("wallposts", "TextWallpost")
    Update = apps.get_model("updates", "Update")
    UpdateImage = apps.get_model("updates", "UpdateImage")
    Image = apps.get_model("files", "Image")

    initiative_ctype = ContentType.objects.get_for_model(Initiative)

    media_wallposts = MediaWallpost.objects.filter(
        content_type=initiative_ctype, object_id__in=Initiative.objects.all()
    )
    count = 0
    for post in media_wallposts:
        initiative = Initiative.objects.get(id=post.object_id)
        activity = initiative.activities.filter(status__in=['open', 'succeeded']).first()
        if activity:
            count += 1
            update = Update.objects.create(
                created=post.created,
                activity_id=activity.id,
                message=post.text,
                video_url=post.video_url,
                author=post.author,
                notify=post.email_followers
            )
            migrate_related_reactions(post, update, Update)

            photos = MediaWallpostPhoto.objects.filter(
                mediawallpost_id=post.pk, deleted__isnull=True
            )
            for photo in photos:
                if post.author:
                    try:
                        image = Image.objects.create(
                            file=photo.photo, owner=post.author, used=True
                        )
                        UpdateImage.objects.create(image=image, update=update)
                        print(f"created image for update: {update.pk}")
                    except FileNotFoundError:
                        pass

    text_wallposts = TextWallpost.objects.filter(
        content_type=initiative_ctype, object_id__in=Initiative.objects.all()
    )

    for post in text_wallposts:
        initiative = Initiative.objects.get(id=post.object_id)
        activity = initiative.activities.filter(status__in=['open', 'succeeded']).last()
        if not activity:
            activity = initiative.activities.last()
        if activity:
            count += 1
            update = Update.objects.create(
                created=post.created,
                activity_id=activity.id,
                message=post.text,
                author=post.author,
                notify=post.email_followers
            )
            migrate_related_reactions(post, update, Update)

    print(f'Migrated {count} wallposts')


class Migration(migrations.Migration):

    dependencies = [
        ('wallposts', '0027_auto_20240813_0922'),
    ]

    operations = [
        migrations.RunPython(
            migrate_initiative_wallposts,
            migrations.RunPython.noop,
        ),
    ]
