import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0123_authenticationmethod_uuid_pk'),
        ('segments', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='samlsegmentmapping',
            name='segment',
        ),
        migrations.AddField(
            model_name='samlsegmentmapping',
            name='segment_type',
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                to='segments.segmenttype',
            ),
            preserve_default=False,
        ),
    ]
