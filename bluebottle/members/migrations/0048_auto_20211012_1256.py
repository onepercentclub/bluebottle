# Generated by Django 2.2.24 on 2021-10-12 10:56

# Generated by Django 2.2.24 on 2021-10-12 10:43

from django.db import migrations


def migrate_addresses(apps, schema_editor):
    Member = apps.get_model('members', 'Member')
    Place = apps.get_model('geo', 'Place')

    for member in Member.objects.all():
        member.place = Place.objects.filter(object_id=member.id).first()
        member.save()


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0047_auto_20211012_1255'),
    ]

    operations = [
        migrations.RunPython(
            migrate_addresses,
            migrations.RunPython.noop
        )
    ]
