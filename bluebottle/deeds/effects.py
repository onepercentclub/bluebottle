from datetime import datetime

from django.db.models import F
from django.utils.timezone import get_current_timezone, now
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.models import EffortContribution
from bluebottle.fsm.effects import Effect


class CreateEffortContribution(Effect):
    "Create an effort contribution for the organizer or participant of the activity"

    display = False

    def pre_save(self, effects):
        start = now()
        tz = get_current_timezone()
        if self.instance.activity.start and self.instance.activity.start > start.date():
            start = tz.localize(
                datetime.combine(
                    self.instance.activity.start, datetime.min.replace(hour=12).time()
                )
            )
        self.contribution = EffortContribution(
            contributor=self.instance,
            contribution_type=EffortContribution.ContributionTypeChoices.deed,
            start=start,
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

        if self.instance.start:
            start = tz.localize(datetime.combine(self.instance.start, datetime.min.time()))
        else:
            start = F('start')

        if self.instance.end:
            end = tz.localize(datetime.combine(self.instance.end, datetime.min.time()))
        else:
            end = None

        self.instance.efforts.update(
            start=start,
            end=end
        )
