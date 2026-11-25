from django.db import migrations

PERMISSION = ('looker', 'lookerembed', 'access_looker_embeds')


def split_reporting_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    app_label, model, codename = PERMISSION
    permission = Permission.objects.get(
        content_type__app_label=app_label,
        content_type__model=model,
        codename=codename,
    )

    reporting, _ = Group.objects.get_or_create(name='Reporting')
    reporting.permissions.add(permission)

    for editor in Group.objects.filter(name='Content Editor'):
        editor.permissions.remove(permission)


def merge_reporting_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    app_label, model, codename = PERMISSION
    permission = Permission.objects.get(
        content_type__app_label=app_label,
        content_type__model=model,
        codename=codename,
    )
    for editor in Group.objects.filter(name='Content Editor'):
        editor.permissions.add(permission)
    Group.objects.filter(name='Reporting').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('members', '0109_content_editor_group'),
        ('looker', '0004_auto_20201001_1419'),
    ]

    operations = [
        migrations.RunPython(split_reporting_group, merge_reporting_group),
    ]
