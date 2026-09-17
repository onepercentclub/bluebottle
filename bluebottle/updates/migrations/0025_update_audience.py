from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('updates', '0024_updatedocument'),
    ]

    operations = [
        migrations.AddField(
            model_name='update',
            name='audience',
            field=models.CharField(
                choices=[
                    ('everyone', 'Everyone'),
                    ('contributors', 'Participants'),
                ],
                default='everyone',
                max_length=20,
                verbose_name='Audience',
            ),
        ),
    ]
