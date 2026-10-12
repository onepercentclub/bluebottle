from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0102_alter_activity_office_location_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='remotecontributor',
            name='sync_id',
            field=models.CharField(
                blank=True,
                help_text='Remote participant id for matching Join/Leave in synced activities.',
                max_length=255,
                null=True,
                verbose_name='Sync identifier',
            ),
        ),
        migrations.AddConstraint(
            model_name='remotecontributor',
            constraint=models.UniqueConstraint(
                fields=('sync_actor', 'sync_id'),
                name='activities_remotecontributor_unique_actor_sync_id',
            ),
        ),
    ]
