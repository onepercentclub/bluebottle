from datetime import datetime, date, timedelta

from django.utils.timezone import get_current_timezone, now
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.models import EffortContribution
from bluebottle.fsm.effects import Effect


class CreateEffortContribution(Effect):
    "Create an effort contribution for the organizer or participant of the activity"

    display = False

    def pre_save(self, effects):
        contribution_date = now()
        tz = get_current_timezone()
        if self.instance.activity.start and self.instance.activity.start > contribution_date.date():
            contribution_date = tz.localize(
                datetime.combine(
                    self.instance.activity.start, datetime.min.replace(hour=12).time()
                )
            )
        elif self.instance.activity.end and self.instance.activity.end < contribution_date.date():
            contribution_date = tz.localize(
                datetime.combine(
                    self.instance.activity.end, datetime.min.replace(hour=12).time()
                )
            )
        self.contribution = EffortContribution(
            contributor=self.instance,
            contribution_type=EffortContribution.ContributionTypeChoices.deed,
            start=contribution_date,
        )
        effects.extend(self.contribution.execute_triggers())

    def post_save(self, **kwargs):
        self.contribution.contributor_id = self.contribution.contributor.pk
        self.contribution.save()

    def __str__(self):
        return str(_('Create effort contribution'))


class RescheduleEffortsEffect(Effect):
    display = False

    def post_save(self, **kwargs):
        tz = get_current_timezone()

        if self.instance.start and self.instance.start > now().date():
            start = tz.localize(
                datetime.combine(
                    self.instance.start, datetime.min.replace(hour=12).time()
                )
            )
            self.instance.efforts.update(
                start=start,
            )


class SetEndDateEffect(Effect):
    title = _('Set end date, if no deadline is specified')
    template = 'admin/set_end_date.html'

    def is_valid(self):
        return not self.instance.end

    def pre_save(self, **kwargs):
        self.instance.end = date.today() - timedelta(days=1)
