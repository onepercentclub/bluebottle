from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentblock',
            name='button_url',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
    ]
