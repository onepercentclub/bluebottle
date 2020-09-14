from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import Effect
from bluebottle.activities.models import Organizer


class CreateOrganizer(Effect):
    "Create an organizer for the activity"

    def post_save(self, **kwargs):
        Organizer.objects.get_or_create(
            activity=self.instance,
            defaults={'user': self.instance.owner}
        )

    def __unicode__(self):
        return unicode(_('Create organizer'))
