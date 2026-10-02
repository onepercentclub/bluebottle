from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0118_remove_action_tint_stops'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='siteplatformsettings',
            name='description_on_tint_100_color',
        ),
        migrations.RemoveField(
            model_name='siteplatformsettings',
            name='description_on_tint_300_color',
        ),
    ]
