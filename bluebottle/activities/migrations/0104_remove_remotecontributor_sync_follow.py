from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0103_remotecontributor_sync_follow_sync_id_unique'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='remotecontributor',
            name='sync_follow',
        ),
    ]
