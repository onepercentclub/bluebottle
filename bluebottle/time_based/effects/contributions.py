from datetime import datetime

from django.db.models import F
from django.utils.timezone import get_current_timezone

from bluebottle.fsm.effects import Effect


class RescheduleActivityDurationsEffect(Effect):
    display = False

    def post_save(self, **kwargs):
        tz = get_current_timezone()

        if self.instance.start:
            start = tz.localize(datetime.combine(self.instance.start, datetime.min.time()))
        else:
            start = F('start')

        if self.instance.deadline:
            end = tz.localize(datetime.combine(self.instance.deadline, datetime.min.time()))
        else:
            end = None

        self.instance.durations.update(
            start=start,
            end=end,
            value=self.instance.duration
        )
