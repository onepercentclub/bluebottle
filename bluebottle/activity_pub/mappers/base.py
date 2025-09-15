from datetime import datetime, date
from typing import Protocol

from django.utils import timezone


class ActivityMapper(Protocol):
    def to_event(self, activity):
        return activity


def get_absolute_path(tenant, path):
    return tenant.build_absolute_url(path) if (tenant and path) else None


def datetime_to_iso(dt):
    if not dt:
        return None

    if isinstance(dt, date):
        dt = datetime.combine(dt, datetime.min.time())
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
