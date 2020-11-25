from future.utils import python_2_unicode_compatible

from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import Effect
from bluebottle.activities.models import Organizer, OrganizerContribution


@python_2_unicode_compatible
class CreateOrganizer(Effect):
    "Create an organizer for the activity"

    def post_save(self, **kwargs):
        Organizer.objects.get_or_create(
            activity=self.instance,
            defaults={'user': self.instance.owner}
        )

    def __str__(self):
        return str(_('Create organizer'))


class CreateOrganizerContribution(Effect):
    "Create an contribution for the organizer of the activity"

    def post_save(self, **kwargs):
        OrganizerContribution.objects.get_or_create(
            contributor=self.instance
        )

    def __str__(self):
        return str(_('Create organizer contribution'))
