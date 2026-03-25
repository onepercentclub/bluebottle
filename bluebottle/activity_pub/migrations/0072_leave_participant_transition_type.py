from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity_pub', '0071_event_contributor_count_alter_follow_adoption_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='leave',
            name='participant_transition_type',
            field=models.CharField(
                blank=True,
                choices=[('withdraw', 'withdraw'), ('remove', 'remove'), ('reject', 'reject')],
                help_text='Why the participant left (withdraw, remove, reject).',
                max_length=40,
                null=True,
                verbose_name='Participant transition type',
            ),
        ),
    ]
