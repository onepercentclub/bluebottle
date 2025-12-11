from django.utils.translation import gettext_lazy as _

from bluebottle.activity_pub.models import Publish, Announce
from bluebottle.activity_pub.utils import get_platform_actor
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
