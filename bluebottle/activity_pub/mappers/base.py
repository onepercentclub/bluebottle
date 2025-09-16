from datetime import datetime, date
from io import BytesIO

import requests
from django.core.files import File
from django.utils import timezone

from bluebottle.files.models import Image


class ActivityMapper:
    def to_event(self, activity):
        raise NotImplemented()

    def to_activity(self, event, user=None):
        raise NotImplemented()

    def get_image(self, event, user):
        if event.image:
            try:
                response = requests.get(event.image, timeout=30)
                response.raise_for_status()

                image = Image(owner=user)

                import time

                filename = f"event_{event.pk}_{int(time.time())}.jpg"

                image.file.save(filename, File(BytesIO(response.content)))
                return image
            except Exception as e:
                pass


def get_absolute_path(tenant, path):
    return tenant.build_absolute_url(path) if (tenant and path) else None

def datetime_to_iso(dt):
    if not dt:
        return None

    if isinstance(dt, date):
        dt = datetime.combine(dt, datetime.min.time())
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


def duration_from_iso(iso):
    if not iso:
        return None
    return duration_parse(iso).total_seconds()
