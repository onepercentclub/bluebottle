from datetime import timedelta

from django.utils.timezone import get_current_timezone
from bluebottle.time_based.models import DateActivitySlot

from bluebottle.members.models import Member
from bluebottle.time_based.models import DateParticipant, SlotParticipant


def nth_weekday(date):
    temp = date.replace(day=1)
    adj = (date.weekday() - temp.weekday()) % 7
    temp += timedelta(days=adj)
    nth = int((date - temp).days / 7) + 1
    return nth


def duplicate_slot(slot, interval, end):
    dates = []
    tz = get_current_timezone()

    start = slot.start.astimezone(tz)
    for n in range(int((end - start.date()).days)):
        date = start + timedelta(days=n + 1)
        if interval == 'day':
            dates.append(date)
        if interval == 'week' and date.weekday() == start.weekday():
            dates.append(date)
        if interval == 'monthday' and date.day == start.day:
            dates.append(date)
        if interval == 'month' \
                and date.weekday() == start.weekday() \
                and nth_weekday(date) == nth_weekday(start):
            dates.append(date)

    fields = dict(
        (field.name, getattr(slot, field.name)) for field in slot._meta.fields
        if field.name not in ['created', 'updated', 'start', 'id', 'status']
    )

    for date in dates:
        start = tz.localize(
            start.replace(tzinfo=None, day=date.day, month=date.month, year=date.year)
        )

        slot = DateActivitySlot(start=start, **fields)
        slot.save()


def bulk_add_slot_participants(slot, emails):
    activity = slot.activity
    count = 0
    for email in emails:
        try:
            user = Member.objects.get(email__iexact=email.strip())
            participant, _created = DateParticipant.objects.get_or_create(
                user=user, activity=activity
            )
            slot_participant, created = SlotParticipant.objects.get_or_create(
                participant=participant,
                slot=slot
            )
            if created:
                count += 1
        except Member.DoesNotExist:
            pass
    return count
