
from django.utils.translation import gettext_lazy as _

from bluebottle.activity_pub.models import Event, Publish, Person, Announce
from bluebottle.activity_pub.adapters import adapter
from bluebottle.fsm.effects import Effect


class PublishEffect(Effect):
    display = True
    template = 'admin/activity_pub/publish_effect.html'

    def post_save(self, **kwargs):
        event = Event.objects.from_model(self.instance)
        publish = Publish.objects.create(actor=event.organizer, object=event)
        adapter.publish(publish)

    def get_person(self):
        try:
            return self.instance.owner.person
        except Person.DoesNotExist:
            return None

    @property
    def is_valid(self):
        event = Event.objects.filter(activity=self.instance).first()
        if event:
            return False
        return self.get_person() is not None

    def __str__(self):
        return str(_('Publish activity to followers'))


class AnnounceAdoptionEffect(Effect):
    display = True
    template = 'admin/activity_pub/announce_adoption_effect.html'

    def post_save(self, **kwargs):
        event = self.instance.event
        publish = Announce.objects.create(actor=event.actor, object=event)
        adapter.publish(publish)

    def get_person(self):
        try:
            return self.instance.owner.person
        except Person.DoesNotExist:
            return None

    @property
    def is_valid(self):
        event = Event.objects.filter(activity=self.instance).first()
        if not event:
            return False
        return self.get_person() is not None

    def __str__(self):
        return str(_('Announce that the activity has been adopted'))
