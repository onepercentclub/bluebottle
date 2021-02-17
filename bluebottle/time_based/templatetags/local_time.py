from django import template
from datetime import datetime
from django.template.defaultfilters import time, date

register = template.Library()


@register.filter(name="local_time")
def local_time(value, tz):
    if tz and isinstance(value, datetime):
        return time(value + value.astimezone(tz).utcoffset())


@register.filter(name="local_date")
def local_date(value, tz):
    if tz and isinstance(value, datetime):
        return date(value + value.astimezone(tz).utcoffset())


@register.filter(name="local_timezone")
def local_timezone(value, tz):
    if tz and isinstance(value, datetime):
        return value.astimezone(tz).strftime('%Z')
