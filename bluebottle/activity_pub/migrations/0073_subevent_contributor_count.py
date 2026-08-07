from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity_pub', '0072_join_leave_sub_event'),
    ]

    operations = [
        migrations.AddField(
            model_name='subevent',
            name='contributor_count',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Accepted participants for this slot (denormalized for ActivityPub sync).',
            ),
        ),
    ]
