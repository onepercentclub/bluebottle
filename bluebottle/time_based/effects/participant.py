from datetime import datetime, date

from django.utils.timezone import get_current_timezone, now
from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.models import TimeContribution, ContributionTypeChoices


class CreateTimeContributionEffect(Effect):
    title = _('Create contribution')
    template = 'admin/create_deadline_time_contribution.html'

    def post_save(self, **kwargs):
        activity = self.instance.activity
        tz = get_current_timezone()
        if activity.start and activity.start > date.today():
            contribution_date = tz.localize(datetime.combine(activity.start, datetime.min.replace(hour=12).time()))
        elif activity.deadline and activity.deadline < date.today():
            contribution_date = tz.localize(datetime.combine(activity.deadline, datetime.min.replace(hour=12).time()))
        else:
            contribution_date = now()

        contribution = TimeContribution(
            contributor=self.instance,
            contribution_type=ContributionTypeChoices.period,
            value=activity.duration,
            start=contribution_date
        )

        contribution.execute_triggers(**self.options)
        contribution.save()

    def __str__(self):
        return _('Create contribution')
