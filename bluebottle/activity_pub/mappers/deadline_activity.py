import json

from django.db import connection
from django.urls import reverse

from bluebottle.files.serializers import ORIGINAL_SIZE
from .base import get_absolute_path, datetime_to_iso, ActivityMapper
from ..models import Event
from ...time_based.models import DeadlineActivity


class DeadlineActivityMapper(ActivityMapper):
    def to_event(self, activity):
        from bluebottle.activity_pub.utils import get_platform_actor

        image_url = None
        if getattr(activity, "image", None):
            image_url = reverse("activity-image", args=(str(activity.pk), ORIGINAL_SIZE))
        elif getattr(activity, "initiative", None) and getattr(activity.initiative, "image", None):
            image_url = reverse("initiative-image", args=(str(activity.initiative.pk), ORIGINAL_SIZE))

        absolute_image = get_absolute_path(
            getattr(activity, "tenant", None) or getattr(connection, "tenant", None),
            image_url
        )

        start_date = datetime_to_iso(activity.start) if hasattr(activity, 'start') else None
        end_date = datetime_to_iso(activity.deadline) if hasattr(activity, 'deadline') else None

        return Event.objects.create(
            start_date=start_date,
            end_date=end_date,
            organizer=get_platform_actor(),
            name=activity.title,
            duration=activity.duration,
            description=getattr(activity.description, "html", None),
            image=absolute_image,
            activity=activity,
        )

    def to_activity(self, event, user):
        activity = DeadlineActivity.objects.create(
            owner=user,
            title=event.name,
            description=json.dumps({"html": event.description, "delta": ""}),
            start=event.start_date,
            deadline=event.end_date,
            duration=event.duration,
            status="draft",
        )
        activity.image = self.get_image(event, user)
        activity.save()
        return activity
