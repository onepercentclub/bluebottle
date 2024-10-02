import json

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant

from bluebottle.activities.models import Activity

from bluebottle.initiatives.models import Theme
from bluebottle.segments.models import Segment

TENANT = 'nlcares'


def run(*args):
    tenant = Client.objects.get(schema_name=TENANT)
    with LocalTenant(tenant):
        mapping = [
            {'theme': 2, 'segment': 67},
            {'theme': 3, 'segment': 69},
            {'theme': 1, 'segment': 68},
            {'theme': 6, 'segment': 70},

        ]
        for item in mapping:
            theme = Theme.objects.get(id=item['theme'])
            segment = Segment.objects.get(id=item['segment'])

            for activity in Activity.objects.filter(
                initiative__theme=theme
            ):
                if segment not in activity.segments.all():
                    print(segment, theme)
                    activity.segments.add(segment)
                    activity.save()
