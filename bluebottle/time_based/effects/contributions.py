from datetime import datetime

from django.db.models import F
from django.utils.timezone import get_current_timezone, make_aware, now

from bluebottle.fsm.effects import Effect


class RescheduleActivityDurationsEffect(Effect):
    display = False

    def post_save(self, **kwargs):
        tz = get_current_timezone()

        if self.instance.start:
            start = make_aware(
                datetime.combine(self.instance.start, datetime.min.time()),
                tz
            )
        else:
            start = F('start')

        if self.instance.deadline:
            end = make_aware(
                datetime.combine(self.instance.deadline, datetime.min.time()),
                tz
            )
        else:
            end = None

        self.instance.durations.update(
            start=start,
            end=end,
            value=self.instance.duration
        )


class RescheduleRelatedTimeContributionsEffect(Effect):
    display = False

    def post_save(self, **kwargs):

        self.instance.durations.update(
            start=self.instance.start or now(),
            value=self.instance.duration
        )
