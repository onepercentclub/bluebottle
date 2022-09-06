from datetime import timedelta
from django.utils.timezone import get_current_timezone


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

    for date in dates:
        slot.id = None
        slot.start = tz.localize(
            start.replace(tzinfo=None, day=date.day, month=date.month, year=date.year)
        )
        slot.status = 'open'
        slot.save()
