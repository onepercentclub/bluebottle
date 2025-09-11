
from django.utils.translation import gettext_lazy as _

from bluebottle.activity_pub.models import Event, Publish
from bluebottle.activity_pub.adapters import adapter
from bluebottle.fsm.effects import Effect


class PublishEffect(Effect):
    display = True
    template = 'admin/activity_pub/publish_effect.html'

    def post_save(self, **kwargs):
        event = Event.objects.from_model(self.instance)

        publish = Publish.objects.create(actor=event.organizer, object=event)

        adapter.publish(publish)

    def __str__(self):
        return str(_('Publish activity to followers'))
