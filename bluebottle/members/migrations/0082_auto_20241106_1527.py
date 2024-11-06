# Generated by Django 3.2.20 on 2024-11-06 14:27

from django.db import migrations


def migrate_avatar_image(apps, schema_editor):
    Member = apps.get_model('members', 'Member')
    Image = apps.get_model('files', 'Image')
    for member in Member.objects.filter(picture__isnull=False):
        member.avatar = Image.objects.create(
            file=member.picture, owner=member, used=True
        )

        member.save()


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0081_auto_20241106_1359'),
    ]

    operations = [
        migrations.RunPython(migrate_avatar_image, migrations.RunPython.noop),
    ]
