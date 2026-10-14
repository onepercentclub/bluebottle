from datetime import timezone as datetime_timezone

from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime
from django.db import models
from django.template import defaultfilters
from django.utils import timezone as dj_timezone
from django.utils.html import format_html, mark_safe
from django.utils.timezone import get_current_timezone
from django.utils.translation import gettext_lazy as _
from pytz import timezone as pytz_timezone


def _timezone_name(tz):
    return getattr(tz, 'key', None) or getattr(tz, 'zone', None) or str(tz)


def resolve_slot_timezone(is_online, location):
    """
    Return (tzinfo, has_venue_timezone).
    Venue TZ when offline with a location; otherwise the platform TZ.
    """
    if (
        not is_online
        and location is not None
        and getattr(location, 'timezone', None)
    ):
        return pytz_timezone(location.timezone), True
    return get_current_timezone(), False


def slot_timezone(instance):
    """IANA timezone name for API, or None when online / no location."""
    is_online = getattr(instance, 'is_online', False)
    location = getattr(instance, 'location', None)
    if not is_online and location and getattr(location, 'timezone', None):
        return location.timezone
    return None


def localize_datetime(value, is_online, location):
    """Convert an aware UTC datetime to the slot display timezone."""
    if not value:
        return None
    tz, _has_venue = resolve_slot_timezone(is_online, location)
    if dj_timezone.is_naive(value):
        value = dj_timezone.make_aware(value, get_current_timezone())
    return value.astimezone(tz)


def wall_clock_to_utc(naive_or_aware, is_online, location):
    """
    Interpret date/time digits as wall clock in the slot TZ and return aware UTC.
    """
    if not naive_or_aware:
        return None
    tz, _has_venue = resolve_slot_timezone(is_online, location)
    if dj_timezone.is_aware(naive_or_aware):
        naive = naive_or_aware.replace(tzinfo=None)
    else:
        naive = naive_or_aware
    if hasattr(tz, 'localize'):
        aware = tz.localize(naive)
    else:
        aware = dj_timezone.make_aware(naive, tz)
    return aware.astimezone(datetime_timezone.utc)


def get_local_time_caption(obj, value=None):
    """
    Caption for admin when a venue location is set.
    Always notes local time in the location; adds platform offset when it differs.
    """
    if not obj:
        return None

    is_online = getattr(obj, 'is_online', False)
    location = getattr(obj, 'location', None)
    if is_online or not location:
        return None

    start = value if value is not None else getattr(obj, 'start', None)
    if not start:
        return format_html(
            '<em>{}</em>',
            _('Local time in {location}').format(location=location),
        )

    local_start = localize_datetime(start, is_online, location)
    platform_start = start.astimezone(get_current_timezone())
    platform_name = _timezone_name(get_current_timezone())

    first = _('Local time in {location}').format(location=location)
    offset = local_start.utcoffset() - platform_start.utcoffset()
    if offset.total_seconds() == 0:
        return first

    offset_hours = abs(offset.total_seconds() / 3600.0)
    relation = _('behind') if offset.total_seconds() > 0 else _('ahead')
    second = _(
        'Your timezone ({platform}) is {offset} hours {relation}, '
        'so there it is {platform_datetime}.'
    ).format(
        platform=platform_name,
        offset='{:g}'.format(offset_hours),
        relation=relation,
        platform_datetime='{} {}'.format(
            defaultfilters.date(platform_start),
            defaultfilters.time(platform_start),
        ),
    )
    return mark_safe('{}<br/>{}'.format(first, second))


class LocalDateTimeWidget(AdminSplitDateTime):
    """
    Split date/time that keeps wall-clock components of the given value
    (no conversion to the platform timezone on display).
    """

    def __init__(self, attrs=None, caption=None):
        self.caption = caption
        super().__init__(attrs)

    def decompress(self, value):
        if value:
            if dj_timezone.is_aware(value):
                return [value.date(), value.time().replace(microsecond=0)]
            return [value.date(), value.time()]
        return [None, None]

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        if self.caption:
            return format_html(
                '{}<div class="help local-datetime-caption">{}</div>',
                html,
                self.caption,
            )
        return html


class LocalDateTimeFormField(forms.SplitDateTimeField):
    widget = LocalDateTimeWidget

    def __init__(
        self,
        location_field='location',
        online_field='is_online',
        *args,
        **kwargs
    ):
        self.location_field = location_field
        self.online_field = online_field
        self.instance = None
        kwargs.setdefault('widget', LocalDateTimeWidget)
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if value in self.empty_values:
            return value
        if self.instance is not None:
            is_online = getattr(self.instance, self.online_field, False)
            location = getattr(self.instance, self.location_field, None)
            return localize_datetime(value, is_online, location)
        return value


class LocalDateTimeModelFormMixin:
    """Bind LocalDateTimeFormField to instance and reinterpret wall clock on save."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            if isinstance(field, LocalDateTimeFormField):
                field.instance = self.instance
                if isinstance(field.widget, LocalDateTimeWidget):
                    field.widget.caption = get_local_time_caption(self.instance)

    def clean(self):
        cleaned_data = super().clean()
        for name, field in self.fields.items():
            if not isinstance(field, LocalDateTimeFormField):
                continue
            value = cleaned_data.get(name)
            if value in field.empty_values:
                continue

            if field.location_field in cleaned_data:
                location = cleaned_data.get(field.location_field)
            else:
                location = getattr(self.instance, field.location_field, None)

            if field.online_field in cleaned_data:
                is_online = cleaned_data.get(field.online_field)
            else:
                is_online = getattr(self.instance, field.online_field, False)

            cleaned_data[name] = wall_clock_to_utc(value, is_online, location)
        return cleaned_data


class LocalDateTimeField(models.DateTimeField):
    """
    DateTime stored in UTC; admin edits wall-clock time in the location timezone.

    location_field / online_field name the related fields used to resolve the TZ.
    """

    def __init__(
        self,
        *args,
        location_field='location',
        online_field='is_online',
        **kwargs
    ):
        self.location_field = location_field
        self.online_field = online_field
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.location_field != 'location':
            kwargs['location_field'] = self.location_field
        if self.online_field != 'is_online':
            kwargs['online_field'] = self.online_field
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        defaults = dict(kwargs)
        defaults.update({
            'form_class': LocalDateTimeFormField,
            'widget': LocalDateTimeWidget,
            'location_field': self.location_field,
            'online_field': self.online_field,
        })
        return super().formfield(**defaults)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        if value is None:
            return ''
        local = localize_datetime(
            value,
            getattr(obj, self.online_field, False),
            getattr(obj, self.location_field, None),
        )
        if local is None:
            return ''
        return defaultfilters.date(local) + ' ' + defaultfilters.time(local)
