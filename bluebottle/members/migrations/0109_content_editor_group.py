from django.contrib.auth.management import create_permissions
from django.db import migrations

CONTENT_MODELS = [
    ('pages', 'page'),
    ('pages', 'actionitem'),
    ('pages', 'columnsitem'),
    ('pages', 'documentitem'),
    ('pages', 'imagetextitem'),
    ('pages', 'imagetextrounditem'),
    ('pages', 'scaledimagetextitem'),
    ('cms', 'imageplaintextitem'),
    ('cms', 'peoplecontent'),
    ('cms', 'person'),
    ('cms', 'pollcontent'),
    ('contentplugins', 'pictureitem'),
    ('text', 'textitem'),
    ('oembeditem', 'oembeditem'),
    ('rawhtml', 'rawhtmlitem'),
    ('fluent_contents', 'placeholder'),
    ('fluent_contents', 'contentitem'),
]

PERMISSIONS = [
    (app_label, model, '{}_{}'.format(action, model))
    for app_label, model in CONTENT_MODELS
    for action in ('add', 'change', 'delete', 'view')
] + [
    ('looker', 'lookerembed', 'access_looker_embeds'),
]


def add_content_editor_group(apps, schema_editor):
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    group, _ = Group.objects.get_or_create(name='Content Editor')
    for app_label, model, codename in PERMISSIONS:
        permission = Permission.objects.filter(
            content_type__app_label=app_label,
            content_type__model=model,
            codename=codename,
        ).first()
        if permission is None:
            raise Exception('Could not add permission {}.{}: not found'.format(app_label, codename))
        group.permissions.add(permission)


class Migration(migrations.Migration):
    dependencies = [
        ('members', '0108_member_office_manager'),
        ('pages', '0021_merge_20251126_1506'),
        ('cms', '0119_remove_description_tint_stops'),
        ('contentplugins', '0005_auto_20170818_1441'),
        ('looker', '0004_auto_20201001_1419'),
        ('text', '0002_textitem_text_final'),
        ('oembeditem', '0001_initial'),
        ('rawhtml', '0001_initial'),
        ('fluent_contents', '0002_poll'),
    ]

    operations = [
        migrations.RunPython(add_content_editor_group, migrations.RunPython.noop),
    ]
