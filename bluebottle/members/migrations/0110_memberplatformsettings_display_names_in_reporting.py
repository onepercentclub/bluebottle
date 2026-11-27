from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0109_content_editor_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberplatformsettings',
            name='display_names_in_reporting',
            field=models.BooleanField(
                default=True,
                help_text='Disable this to hide all names in reporting (Looker)',
                verbose_name='Display names in reporting'
            ),
        ),
    ]
