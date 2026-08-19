from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('activity_pub', '0107_rename_join_instrument_to_team'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Add',
        ),
    ]
