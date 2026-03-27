from django.db import migrations, models
from django.db.models import Count


def dedupe_subevent_slot(apps, schema_editor):
    SubEvent = apps.get_model('activity_pub', 'SubEvent')

    duplicate_slot_ids = (
        SubEvent.objects.exclude(slot_id__isnull=True)
        .values('slot_id')
        .annotate(total=Count('id'))
        .filter(total__gt=1)
        .values_list('slot_id', flat=True)
    )

    for slot_id in duplicate_slot_ids:
        keep = (
            SubEvent.objects.filter(slot_id=slot_id)
            .order_by('-id')
            .first()
        )
        if not keep:
            continue
        SubEvent.objects.filter(slot_id=slot_id).exclude(pk=keep.pk).update(slot_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ('activity_pub', '0074_dogoodevent_subevent_capacity'),
    ]

    operations = [
        migrations.RunPython(dedupe_subevent_slot, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='subevent',
            name='slot',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                to='time_based.dateactivityslot',
            ),
        ),
    ]
