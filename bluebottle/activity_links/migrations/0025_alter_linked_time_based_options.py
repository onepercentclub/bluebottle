from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('activity_links', '0024_auto_20261023_1057'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='linkeddateactivity',
            options={'verbose_name': 'Date activity', 'verbose_name_plural': 'Date activities'},
        ),
        migrations.AlterModelOptions(
            name='linkeddeadlineactivity',
            options={'verbose_name': 'Flexible activity', 'verbose_name_plural': 'Flexible activities'},
        ),
        migrations.AlterModelOptions(
            name='linkedperiodicactivity',
            options={'verbose_name': 'Recurring activity', 'verbose_name_plural': 'Recurring activities'},
        ),
        migrations.AlterModelOptions(
            name='linkedscheduleactivity',
            options={'verbose_name': 'Past date activity', 'verbose_name_plural': 'Past date activities'},
        ),
    ]
