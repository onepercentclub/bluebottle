from django.db import connection
from django.urls import reverse

from bluebottle.files.serializers import ORIGINAL_SIZE

from ..models import Event
from .base import datetime_to_iso, get_absolute_path


class DateActivityMapper:

    def to_event(self, activity) -> Event:
        # Import here to avoid circular import
        from bluebottle.activity_pub.utils import get_platform_actor

        image_url = None
        if getattr(activity, "image", None):
            image_url = reverse("activity-image", args=(str(activity.pk), ORIGINAL_SIZE))
        elif getattr(activity, "initiative", None) and getattr(activity.initiative, "image", None):
            image_url = reverse("initiative-image", args=(str(activity.initiative.pk), ORIGINAL_SIZE))

        absolute_image = get_absolute_path(
            getattr(activity, "tenant", None) or getattr(connection, "tenant", None),
            image_url,
        )

        slots = activity.slots.all().order_by("start")

        if not slots.exists():
            return Event.objects.create(
                start_date=None,
                end_date=None,
                organizer=get_platform_actor(),
                name=activity.title,
                description=getattr(activity.description, "html", None),
                image=absolute_image,
                activity=activity,
            )

        if slots.count() == 1:
            first_slot = slots.first()
            start_date = datetime_to_iso(first_slot.start)
            end_date = None

            if hasattr(first_slot, 'end') and first_slot.end:
                end_date = datetime_to_iso(first_slot.end)
            elif hasattr(first_slot, 'duration') and first_slot.duration:
                end_date = datetime_to_iso(first_slot.start + first_slot.duration)

            return Event.objects.create(
                start_date=start_date,
                end_date=end_date,
                organizer=get_platform_actor(),
                name=activity.title,
                description=getattr(activity.description, "html", None),
                image=absolute_image,
                activity=activity,
            )
        else:
            first_slot = slots.first()
            last_slot = slots.last()

            main_start_date = datetime_to_iso(first_slot.start)
            main_end_date = None

            if hasattr(last_slot, "end") and last_slot.end:
                main_end_date = datetime_to_iso(last_slot.end)
            elif hasattr(last_slot, "duration") and last_slot.duration:
                main_end_date = datetime_to_iso(last_slot.start + last_slot.duration)

            main_event = Event.objects.create(
                start_date=main_start_date,
                end_date=main_end_date,
                organizer=get_platform_actor(),
                name=activity.title,
                description=getattr(activity.description, "html", None),
                image=absolute_image,
                activity=activity,
            )

            for slot in slots:
                slot_start_date = datetime_to_iso(slot.start)
                slot_end_date = None

                if hasattr(slot, "end") and slot.end:
                    slot_end_date = datetime_to_iso(slot.end)
                elif hasattr(slot, "duration") and slot.duration:
                    slot_end_date = datetime_to_iso(slot.start + slot.duration)

                Event.objects.create(
                    start_date=slot_start_date,
                    end_date=slot_end_date,
                    organizer=get_platform_actor(),
                    name=f"{activity.title} - Slot {slot.sequence}",
                    description=getattr(activity.description, "html", None),
                    image=absolute_image,
                    parent=main_event,
                )

            return main_event
