import datetime

from django.db import migrations, models
from django.utils.timezone import now


def two_days_ago():
    return now() - datetime.timedelta(days=2)


class Migration(migrations.Migration):
    dependencies = [
        ('translations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='translation',
            name='created',
            field=models.DateTimeField(
                default=two_days_ago,
                auto_now_add=True,
            ),
            preserve_default=False,
        ),
    ]
