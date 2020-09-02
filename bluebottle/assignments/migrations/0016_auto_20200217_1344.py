

import datetime

from django.db import migrations
from django.utils.timezone import get_current_timezone


def set_date(apps, schema_editor):
    Assignment = apps.get_model('assignments', 'Assignment')

    for assignment in Assignment.objects.all():
        if assignment.end_date:
            if assignment.start_time:
                assignment.date = get_current_timezone().localize(
                    datetime.datetime.combine(
                        assignment.end_date,
                        assignment.start_time
                    )
                )
            else:
                assignment.date = assignment.end_date

            assignment.save()


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0015_auto_20200217_1344'),
    ]

    operations = [
        migrations.RunPython(set_date)
    ]
