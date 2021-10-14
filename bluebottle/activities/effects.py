from django.utils.timezone import now

from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.effects import Effect
from bluebottle.activities.models import Organizer, EffortContribution


class CreateOrganizer(Effect):
    "Create an organizer for the activity"

    display = False

    def post_save(self, **kwargs):
        Organizer.objects.get_or_create(
            activity=self.instance,
            defaults={'user': self.instance.owner}
        )

    def __str__(self):
        return str(_('Create organizer'))


class CreateOrganizerContribution(Effect):
    "Create an effort contribution for the organizer or participant of the activity"

    display = False

    def pre_save(self, effects):
        self.contribution = EffortContribution(
            contributor=self.instance,
            contribution_type=EffortContribution.ContributionTypeChoices.organizer
        )
        effects.extend(self.contribution.execute_triggers())

    def post_save(self, **kwargs):
        self.contribution.contributor_id = self.contribution.contributor.pk
        self.contribution.save()

    def __str__(self):
        return str(_('Create effort contribution'))


class SetContributionDateEffect(Effect):
    "Set the contribution date"

    conditions = []
    display = False

    def pre_save(self, **kwargs):
        if self.instance.contribution_type == 'organizer':
            self.instance.start = now()

    def __str__(self):
        return _('Set the contribution date.')
