# Generated by Django 3.2.20 on 2024-03-27 10:20

from django.db import migrations

from bluebottle.time_based.models import PeriodActivity


def migrate_deadline_wallposts(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    DeadlineActivity = apps.get_model("time_based", "DeadlineActivity")
    PeriodActivity = apps.get_model("time_based", "PeriodActivity")

    MediaWallpost = apps.get_model("wallposts", "MediaWallpost")
    SystemWallpost = apps.get_model("wallposts", "SystemWallpost")
    TextWallpost = apps.get_model("wallposts", "TextWallpost")

    deadline_activity_ctype = ContentType.objects.get_for_model(DeadlineActivity)
    period_activity_ctype = ContentType.objects.get_for_model(PeriodActivity)

    media_wallposts = MediaWallpost.objects.filter(
        content_type=period_activity_ctype, object_id__in=DeadlineActivity.objects.all()
    )
    media_wallposts.update(content_type_id=deadline_activity_ctype)

    text_wallposts = TextWallpost.objects.filter(
        content_type=period_activity_ctype, object_id__in=DeadlineActivity.objects.all()
    )
    text_wallposts.update(content_type_id=deadline_activity_ctype)

    system_wallposts = SystemWallpost.objects.filter(
        content_type=period_activity_ctype, object_id__in=DeadlineActivity.objects.all()
    )
    system_wallposts.update(content_type_id=deadline_activity_ctype)


class Migration(migrations.Migration):

    dependencies = [
        ("wallposts", "0023_auto_20221213_1132"),
        ("time_based", "0099_auto_20240304_1341"),
    ]

    operations = [
        migrations.RunPython(migrate_deadline_wallposts, migrations.RunPython.noop)
    ]
