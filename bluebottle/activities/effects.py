from django.utils.timezone import now

from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import Effect
from bluebottle.activities.models import Organizer, OrganizerContribution


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
    "Create an contribution for the organizer of the activity"

    display = False

    def post_save(self, **kwargs):
        OrganizerContribution.objects.get_or_create(
            contributor=self.instance
        )

    def __str__(self):
        return str(_('Create organizer contribution'))


class SetContributionDateEffect(Effect):
    "Set the contribution date"

    conditions = []
    display = False

    def pre_save(self, **kwargs):
        self.instance.start = now()

    def __str__(self):
        return _('Set the contribution date.')
