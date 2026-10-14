import bluebottle.time_based.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0151_merge_0150_interest_0150_registration_closed_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dateactivityslot',
            name='start',
            field=bluebottle.time_based.fields.LocalDateTimeField(
                blank=True, null=True, verbose_name='start date and time'
            ),
        ),
        migrations.AlterField(
            model_name='scheduleslot',
            name='start',
            field=bluebottle.time_based.fields.LocalDateTimeField(
                blank=True, null=True, verbose_name='start date and time'
            ),
        ),
        migrations.AlterField(
            model_name='teamscheduleslot',
            name='start',
            field=bluebottle.time_based.fields.LocalDateTimeField(
                blank=True, null=True, verbose_name='start date and time'
            ),
        ),
    ]
