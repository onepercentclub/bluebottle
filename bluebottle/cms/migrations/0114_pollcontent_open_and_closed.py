import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0113_remove_pollcontent_sub_title_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pollcontent',
            name='poll',
            field=models.ForeignKey(
                limit_choices_to={'status__in': ['open', 'closed']},
                on_delete=django.db.models.deletion.CASCADE,
                to='voting.poll',
                verbose_name='Poll',
            ),
        ),
    ]
