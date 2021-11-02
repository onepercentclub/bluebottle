from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

from bluebottle.fsm.effects import Effect
from bluebottle.collect.models import CollectContribution


class CreateCollectContribution(Effect):
    "Create an effort contribution for the organizer or participant of the activity"

    display = False

    def pre_save(self, effects):

        self.contribution = CollectContribution(
            contributor=self.instance,
            start=now(),
        )
        effects.extend(self.contribution.execute_triggers())

    def post_save(self, **kwargs):
        self.contribution.contributor_id = self.contribution.contributor.pk
        self.contribution.save()

    def __str__(self):
        return str(_('Create collect contribution'))
