from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from django.utils.translation import ugettext as _
from django.utils.timezone import now, get_current_timezone

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.models import TimeContribution


class CreateDateParticipationEffect(Effect):
    title = _('Create contribution')
    template = 'admin/create_on_a_date_duration.html'

    def post_save(self, **kwargs):
        activity = self.instance.activity
        if activity.start and activity.duration:
            end = activity.start + activity.duration
            contribution = TimeContribution(
                contributor=self.instance,
                value=activity.duration,
                start=activity.start,
                end=end
            )
            contribution.save()


class CreatePeriodParticipationEffect(Effect):
    title = _('Create contribution')
    template = 'admin/create_period_duration.html'

    def post_save(self, **kwargs):
        tz = get_current_timezone()
        activity = self.instance.activity

        start = self.instance.current_period or activity.start or now()

        if activity.duration_period == 'overall':
            end = activity.deadline if hasattr(activity, 'deadline') else None
        elif activity.duration_period:
            end = start + relativedelta(**{activity.duration_period: 1})
        else:
            end = start

        self.instance.current_period = end
        self.instance.save()

        if start != end:
            contribution = TimeContribution(
                contributor=self.instance,
                value=activity.duration,
                start=tz.localize(datetime.combine(start, datetime.min.time())),
                end=tz.localize(datetime.combine(end, datetime.max.time())) if end else None,
            )

            contribution.save()

    def __str__(self):
        return _('Create contribution')


class SetEndDateEffect(Effect):
    title = _('End the activity')
    template = 'admin/set_end_date.html'

    def post_save(self, **kwargs):
        self.instance.end = date.today()
