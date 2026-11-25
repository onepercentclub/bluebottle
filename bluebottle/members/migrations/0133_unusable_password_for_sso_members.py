from django.contrib.auth.hashers import make_password
from django.db import migrations


def set_unusable_password_for_sso_members(apps, schema_editor):
    Member = apps.get_model('members', 'Member')

    # Members provisioned through SSO were created with an empty password, which Django
    # considers usable. Mark it unusable so these members cannot reset or set a password.
    Member.objects.filter(
        password='',
        remote_id__isnull=False,
    ).exclude(
        remote_id='',
    ).update(
        password=make_password(None)
    )


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0132_authenticationlog'),
    ]

    operations = [
        migrations.RunPython(set_unusable_password_for_sso_members, migrations.RunPython.noop),
    ]
