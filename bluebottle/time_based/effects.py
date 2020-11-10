from datetime import timedelta, datetime

from django.utils.translation import ugettext as _
from django.utils.timezone import now, get_current_timezone

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.models import Duration


class CreateOnADateDurationEffect(Effect):
    template = 'admin/create_on_a_date_duration.html'

    def post_save(self, **kwargs):
        activity = self.instance.activity
        end = activity.start + activity.duration

        duration = Duration(
            contribution=self.instance,
            value=activity.duration,
            start=activity.start,
            end=end
        )
        duration.save()


class CreatePeriodDurationEffect(Effect):
    title = _('Create contribution duration')
    template = 'admin/create_period_duration.html'

    def post_save(self, **kwargs):
        tz = get_current_timezone()
        activity = self.instance.activity

        start = self.instance.current_period or activity.start or now()

        if activity.duration_period == 'overall':
            end = activity.deadline if hasattr(activity, 'deadline') else None
        else:
            end = start + timedelta(**{activity.duration_period: 1})

        self.instance.current_period = end
        self.instance.save()

        duration = Duration(
            contribution=self.instance,
            value=activity.duration,
            start=tz.localize(datetime.combine(start, datetime.min.time())),
            end=tz.localize(datetime.combine(end, datetime.max.time())) if end else None,
        )

        duration.save()

    def __str__(self):
        return _('Create contribution duration')
