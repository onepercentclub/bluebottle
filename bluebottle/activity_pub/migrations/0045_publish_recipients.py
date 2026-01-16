from django.db import migrations, models


def populate_publish_recipients(apps, schema_editor):
    Publish = apps.get_model('activity_pub', 'Publish')
    Follow = apps.get_model('activity_pub', 'Follow')

    for publish in Publish.objects.all():
        if publish.recipients.exists():
            continue

        accepted_follows = Follow.objects.filter(
            actor_id=publish.actor_id,
            accept__isnull=False
        ).values_list('object_id', flat=True)

        if accepted_follows:
            publish.recipients.set(accepted_follows)


class Migration(migrations.Migration):

    dependencies = [
        ('activity_pub', '0044_merge_20251103_1151'),
    ]

    operations = [
        migrations.AddField(
            model_name='publish',
            name='recipients',
            field=models.ManyToManyField(
                to='activity_pub.actor',
                related_name='received_publications',
                blank=True
            ),
        ),
        migrations.RunPython(populate_publish_recipients, migrations.RunPython.noop),
    ]

