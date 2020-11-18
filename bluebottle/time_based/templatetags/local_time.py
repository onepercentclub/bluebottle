from django import template
from django.template.defaultfilters import time, date

register = template.Library()


@register.filter(name="local_time")
def local_time(value, tz):
    return time(value + value.astimezone(tz).utcoffset())


@register.filter(name="local_date")
def local_date(value, tz):
    return date(value + value.astimezone(tz).utcoffset())


@register.filter(name="local_timezone")
def local_timezone(value, tz):
    print(value.astimezone(tz).strftime('%Z'))
    return value.astimezone(tz).strftime('%Z')
