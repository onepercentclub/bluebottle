from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0117_adjusted_brand_colours'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='siteplatformsettings',
            name='action_on_tint_100_color',
        ),
        migrations.RemoveField(
            model_name='siteplatformsettings',
            name='action_on_tint_300_color',
        ),
    ]
