from django.utils.translation import gettext_lazy as _

from bluebottle.activity_pub.models import Announce, Update
from bluebottle.activity_pub.utils import get_platform_actor
from bluebottle.activity_pub.adapters import adapter

from bluebottle.fsm.effects import Effect


class AnnounceAdoptionEffect(Effect):
    display = True
    template = 'admin/activity_pub/announce_adoption_effect.html'

    def post_save(self, **kwargs):
        event = self.instance.origin
        actor = get_platform_actor()
        Announce.objects.create(actor=actor, object=event)

    @property
    def is_valid(self):
        return self.instance.origin and get_platform_actor() is not None

    def __str__(self):
        return str(_('Announce that the activity has been adopted'))


class UpdateEventEffect(Effect):
    display = True
    template = 'admin/activity_pub/update_event_effect.html'

    def post_save(self, **kwargs):
        event = adapter.create_event(self.instance)

        Update.objects.create(
            object=event
        )

    @property
    def is_valid(self):
        return hasattr(self.instance, 'event') and get_platform_actor() is not None

    def __str__(self):
        return str(_('Notify subscribers of the changes'))
