from django.db import connection, migrations, models

from bluebottle.clients.models import Client
import bluebottle.mails.models


def replace_email_senders(apps, schema_editor):
    if connection.tenant.schema_name == 'public':
        return

    MailPlatformSettings = apps.get_model('mails', 'MailPlatformSettings')
    tenant = Client.objects.get(schema_name=connection.tenant.schema_name)
    settings = MailPlatformSettings.objects.first()
    if not settings:
        return

    sender = (settings.sender or '').strip()
    if '@' in sender:
        settings.sender = tenant.name
        settings.save(update_fields=['sender'])


class Migration(migrations.Migration):
    dependencies = [
        ('mails', '0004_auto_20241125_1526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailplatformsettings',
            name='address',
            field=models.CharField(
                blank=True,
                help_text='Email address used as the From address for platform emails.',
                max_length=80,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='mailplatformsettings',
            name='footer',
            field=models.TextField(
                blank=True,
                help_text='Optional text added at the bottom of platform emails.',
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='mailplatformsettings',
            name='reply_to',
            field=models.CharField(
                blank=True,
                help_text='Email address used when recipients reply to a platform email.',
                max_length=80,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='mailplatformsettings',
            name='sender',
            field=models.CharField(
                blank=True,
                help_text=(
                    'Name shown next to the From address, such as the platform name. '
                    'Do not use an email address.'
                ),
                max_length=80,
                null=True,
                validators=[bluebottle.mails.models.validate_sender_is_not_email],
            ),
        ),
        migrations.RunPython(replace_email_senders, migrations.RunPython.noop),
    ]
