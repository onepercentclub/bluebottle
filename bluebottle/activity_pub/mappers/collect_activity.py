from django.db import connection
from django.urls import reverse

from bluebottle.files.serializers import ORIGINAL_SIZE
from .base import get_absolute_path, datetime_to_iso
from ..models import Event


class CollectActivityMapper:
    def to_event(self, collect_activity) -> Event:
        # Import here to avoid circular import
        from bluebottle.activity_pub.utils import get_platform_actor

        image_url = None
        if getattr(collect_activity, "image", None):
            image_url = reverse("activity-image", args=(str(collect_activity.pk), ORIGINAL_SIZE))
        elif getattr(collect_activity, "initiative", None) and getattr(collect_activity.initiative, "image", None):
            image_url = reverse("initiative-image", args=(str(collect_activity.initiative.pk), ORIGINAL_SIZE))

        absolute_image = get_absolute_path(
            getattr(collect_activity, "tenant", None) or getattr(connection, "tenant", None),
            image_url
        )

        return Event.objects.create(
            start_date=datetime_to_iso(collect_activity.start),
            end_date=datetime_to_iso(collect_activity.end),
            organizer=get_platform_actor(),
            name=collect_activity.title,
            description=getattr(collect_activity.description, "html", None),
            image=absolute_image,
            activity=collect_activity,
        )
