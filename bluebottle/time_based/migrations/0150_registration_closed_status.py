# Generated manually for registration_closed status

from datetime import date

from django.db import migrations
from django.db.models import Count, Q


def migrate_deadline_locked_to_registration_closed(apps, schema_editor):
    TimeBasedActivity = apps.get_model('time_based', 'TimeBasedActivity')
    DateActivitySlot = apps.get_model('time_based', 'DateActivitySlot')
    today = date.today()

    closed_activity_ids = list(
        TimeBasedActivity.objects.filter(
            status='full',
            registration_deadline__lte=today,
        ).values_list('id', flat=True)
    )

    if closed_activity_ids:
        TimeBasedActivity.objects.filter(id__in=closed_activity_ids).update(
            status='registration_closed'
        )
        DateActivitySlot.objects.filter(
            status__in=['open', 'full'],
            activity_id__in=closed_activity_ids,
        ).update(status='registration_closed')


def reverse_migrate(apps, schema_editor):
    TimeBasedActivity = apps.get_model('time_based', 'TimeBasedActivity')
    DateActivitySlot = apps.get_model('time_based', 'DateActivitySlot')

    closed_activity_ids = list(
        TimeBasedActivity.objects.filter(
            status='registration_closed',
        ).values_list('id', flat=True)
    )

    if not closed_activity_ids:
        return

    TimeBasedActivity.objects.filter(id__in=closed_activity_ids).update(
        status='full'
    )

    slots = DateActivitySlot.objects.filter(
        status='registration_closed',
        activity_id__in=closed_activity_ids,
    ).annotate(
        participant_count=Count(
            'participants',
            filter=Q(participants__status__in=['accepted', 'succeeded']),
        )
    )

    slot_ids = []
    full_slot_ids = []
    for slot in slots:
        slot_ids.append(slot.id)
        if slot.capacity and slot.participant_count >= slot.capacity:
            full_slot_ids.append(slot.id)

    DateActivitySlot.objects.filter(id__in=full_slot_ids).update(status='full')
    DateActivitySlot.objects.filter(id__in=slot_ids).exclude(
        id__in=full_slot_ids
    ).update(status='open')


class Migration(migrations.Migration):

    dependencies = [
        ('time_based', '0149_alter_dateregistration_options_and_more'),
    ]

    operations = [
        migrations.RunPython(
            migrate_deadline_locked_to_registration_closed,
            reverse_migrate,
        ),
    ]
