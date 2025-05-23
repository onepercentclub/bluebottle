from datetime import datetime, date, timedelta

from django.utils.timezone import now, get_current_timezone, make_aware
from django.utils.translation import gettext_lazy as _

from bluebottle.collect.models import CollectContribution
from bluebottle.fsm.effects import Effect


class CreateCollectContribution(Effect):
    "Create an effort contribution for the organizer or participant of the activity"

    display = False

    def pre_save(self, effects):
        contribution_date = now()
        tz = get_current_timezone()
        if self.instance.activity.start and self.instance.activity.start > contribution_date.date():
            contribution_date = make_aware(
                datetime.combine(
                    self.instance.activity.start, datetime.min.replace(hour=12).time()
                ),
                tz
            )
        elif self.instance.activity.end and self.instance.activity.end < contribution_date.date():
            contribution_date = make_aware(
                datetime.combine(
                    self.instance.activity.end, datetime.min.replace(hour=12).time()
                ),
                tz
            )
        self.contribution = CollectContribution(
            contributor=self.instance,
            start=contribution_date,
            type=self.instance.activity.collect_type
        )
        effects.extend(self.contribution.execute_triggers())

    def post_save(self, **kwargs):
        self.contribution.contributor_id = self.contribution.contributor.pk
        self.contribution.save()

    def __str__(self):
        return str(_('Create collect contribution'))


class SetEndDateEffect(Effect):
    title = _('Set end date, if no deadline is specified')
    template = 'admin/set_end_date.html'

    def is_valid(self):
        return not self.instance.end

    def pre_save(self, **kwargs):
        self.instance.end = date.today() - timedelta(days=1)
