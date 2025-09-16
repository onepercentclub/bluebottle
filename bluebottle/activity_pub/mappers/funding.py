from django.db import connection
from django.urls import reverse

from bluebottle.files.serializers import ORIGINAL_SIZE
from .base import get_absolute_path, datetime_to_iso
from ..models import Event


class DeedMapper:
    def to_event(self, deed) -> Event:
        # Import here to avoid circular import
        from bluebottle.activity_pub.utils import get_platform_actor

        image_url = None
        if getattr(deed, "image", None):
            image_url = reverse("activity-image", args=(str(deed.pk), ORIGINAL_SIZE))
        elif getattr(deed, "initiative", None) and getattr(deed.initiative, "image", None):
            image_url = reverse("initiative-image", args=(str(deed.initiative.pk), ORIGINAL_SIZE))

        absolute_image = get_absolute_path(
            getattr(deed, "tenant", None) or getattr(connection, "tenant", None),
            image_url
        )

        return Event.objects.create(
            start_date=datetime_to_iso(deed.start),
            end_date=datetime_to_iso(deed.end),
            organizer=get_platform_actor(),
            name=deed.title,
            description=getattr(deed.description, "html", None),
            image=absolute_image,
            activity=deed,
        )
