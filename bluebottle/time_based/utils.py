from datetime import timedelta

from django.utils.timezone import get_current_timezone, make_aware
from bluebottle.time_based.models import DateActivitySlot

from bluebottle.members.models import Member
from bluebottle.time_based.models import DateParticipant, DateRegistration


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
        start = make_aware(
            start.replace(tzinfo=None, day=date.day, month=date.month, year=date.year),
            tz
        )

        slot = DateActivitySlot(start=start, **fields)
        slot.save()

    return dates


def bulk_add_slot_participants(slot, emails):
    activity = slot.activity
    count = 0
    for email in emails:
        try:
            user = Member.objects.get(email__iexact=email.strip())
            registration, _created = DateRegistration.objects.get_or_create(
                user=user, activity=activity
            )
            participant, created = DateParticipant.objects.get_or_create(
                registration=registration,
                slot=slot
            )
            if created:
                count += 1
        except Member.DoesNotExist:
            pass
    return count
