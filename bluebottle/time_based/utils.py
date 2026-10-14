from datetime import timedelta

from django.utils.timezone import get_current_timezone, localtime, make_aware
from pytz import timezone

from bluebottle.members.models import Member
from bluebottle.time_based.fields import (
    get_local_time_caption,
    resolve_slot_timezone,
)
from bluebottle.time_based.models import DateActivitySlot, DateParticipant, DateRegistration
from bluebottle.utils.widgets import get_time_factors


def get_slot_local_datetimes(slot):
    """
    Return (start, end, is_local) in the venue timezone when the slot is
    on-site with a location; otherwise platform TZ.
    is_local is True when venue offset differs from the platform.
    """
    if not slot or not slot.start:
        return None, None, False

    tz, has_venue = resolve_slot_timezone(
        getattr(slot, 'is_online', False),
        getattr(slot, 'location', None),
    )
    start = slot.start.astimezone(tz)
    end = slot.end.astimezone(tz) if slot.end else None
    if has_venue:
        platform_start = slot.start.astimezone(get_current_timezone())
        is_local = start.utcoffset() != platform_start.utcoffset()
        return start, end, is_local

    return localtime(slot.start), localtime(slot.end) if slot.end else None, False


def get_local_time_help_text(obj):
    """Plain-text caption for tests / legacy help_text injection."""
    caption = get_local_time_caption(obj)
    if not caption:
        return None
    return str(caption).replace('<br/>', ' ')


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


def duration_to_hours(value):
    days, hours, minutes, seconds = get_time_factors(value)
    total_hours = days * 24 + hours + (minutes / 60) + (seconds / 3600)

    return round(total_hours)
