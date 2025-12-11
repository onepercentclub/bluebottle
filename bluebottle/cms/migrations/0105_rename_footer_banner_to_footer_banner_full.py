from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0104_siteplatformsettings_footer_banner_color_logo'),
    ]

    operations = [
        migrations.RenameField(
            model_name='siteplatformsettings',
            old_name='footer_banner',
            new_name='footer_banner_full',
        ),
    ]
