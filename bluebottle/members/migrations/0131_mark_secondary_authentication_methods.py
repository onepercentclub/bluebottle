from django.db import migrations

SUPPORT_ENTITY_ID = 'sso-hub'


def mark_secondary_authentication_methods(apps, schema_editor):
    MemberPlatformSettings = apps.get_model('members', 'MemberPlatformSettings')
    PasswordAuthentication = apps.get_model('members', 'PasswordAuthentication')
    SAMLAuthentication = apps.get_model('members', 'SAMLAuthentication')

    SAMLAuthentication.objects.filter(entity_id=SUPPORT_ENTITY_ID).update(secondary=True)

    member_settings = MemberPlatformSettings.objects.first()
    if not member_settings or not member_settings.closed:
        return

    has_saml = SAMLAuthentication.objects.exclude(entity_id=SUPPORT_ENTITY_ID).exists()
    if has_saml:
        PasswordAuthentication.objects.update(secondary=True)


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0130_authenticationmethod_secondary_and_more'),
    ]

    operations = [
        migrations.RunPython(mark_secondary_authentication_methods, migrations.RunPython.noop),
    ]
