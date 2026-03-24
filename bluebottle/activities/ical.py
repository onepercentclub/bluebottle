from datetime import datetime

import icalendar
from html import unescape

from django.utils.timezone import utc

from bluebottle.utils.utils import to_text


class ActivityIcal:
    def __init__(self, instances):
        if isinstance(instances, (tuple, list)):
            self.instances = self.instances
        else:
            self.instances = [instances]

    def instance_to_event(self, instance):
        event = icalendar.Event()

        if hasattr(instance, 'activity'):
            event.add('summary', instance.activity.title)
        else:
            event.add('summary', instance.title)

        details = unescape(
            to_text.handle(instance.details)
        )
        event.add('description', details)
        event.add('uid', instance.uid)
        event.add('url', instance.get_absolute_url())

        if isinstance(instance.start, datetime):
            event.add('dtstart', instance.start.astimezone(utc))
        else:
            event.add('dtstart', instance.start)

        if isinstance(instance.end, datetime):
            event.add('dtend', instance.end.astimezone(utc))
        else:
            event.add('dtend', instance.end)

        event['uid'] = instance.uid

        organizer = icalendar.vCalAddress('MAILTO:{}'.format(instance.owner.email))
        organizer.params['cn'] = icalendar.vText(instance.owner.full_name)

        event['organizer'] = organizer
        if hasattr(instance, 'location') and instance.location:
            location = instance.location.formatted_address
            if instance.location_hint:
                location = f'{location} ({instance.location_hint})'

            event['location'] = icalendar.vText(location)

        return event

    def to_file(self):
        calendar = icalendar.Calendar()

        for instance in self.instances:
            calendar.add_component(self.instance_to_event(instance))

        return calendar.to_ical()

    def to_attachment(self):
        return (f"event-{self.instances[0].uid}.ics", self.to_file(), 'text/calendar')
