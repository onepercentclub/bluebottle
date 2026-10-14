from datetime import timedelta

from django.template import defaultfilters
from django.utils.timezone import get_current_timezone, localtime, make_aware
from django.utils.translation import gettext_lazy as _
from pytz import timezone

from bluebottle.members.models import Member
from bluebottle.time_based.models import DateActivitySlot, DateParticipant, DateRegistration
from bluebottle.utils.widgets import get_time_factors


def get_slot_local_datetimes(slot):
    """
    Return (start, end, is_local) in the venue timezone when the slot is
    on-site in a different timezone than the platform; otherwise platform TZ.
    """
    if not slot or not slot.start:
        return None, None, False

    if not slot.is_online and slot.location and slot.location.timezone:
        local_tz = timezone(slot.location.timezone)
        start = slot.start.astimezone(local_tz)
        end = slot.end.astimezone(local_tz) if slot.end else None
        platform_start = slot.start.astimezone(get_current_timezone())
        is_local = start.utcoffset() != platform_start.utcoffset()
        return start, end, is_local

    return (
        localtime(slot.start),
        localtime(slot.end) if slot.end else None,
        False,
    )


def _timezone_name(tz):
    return getattr(tz, 'key', None) or getattr(tz, 'zone', None) or str(tz)


def get_local_time_help_text(obj):
    """
    When a slot has an on-site location in another timezone, explain the
    local start time for the start field.
    """
    start, _end, is_local = get_slot_local_datetimes(obj)
    if not start or not is_local or not obj.location:
        return None

    platform_start = obj.start.astimezone(get_current_timezone())
    offset = start.utcoffset() - platform_start.utcoffset()
    offset_hours = abs(offset.total_seconds() / 3600.0)

    return _(
        'Local time in "{location}" is {local_time}. '
        'This is {offset} hours {relation} compared to the '
        'standard platform timezone ({current_timezone}).'
    ).format(
        location=obj.location,
        local_time=defaultfilters.time(start),
        offset='{:g}'.format(offset_hours),
        relation=_('later') if offset.total_seconds() > 0 else _('earlier'),
        current_timezone=_timezone_name(get_current_timezone()),
    )


def add_local_time_help_texts(obj, kwargs):
    help_text = get_local_time_help_text(obj)
    if help_text:
        kwargs = dict(kwargs)
        kwargs['help_texts'] = {'start': help_text}
    return kwargs


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
