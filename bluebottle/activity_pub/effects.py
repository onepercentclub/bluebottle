from django.utils.translation import gettext_lazy as _

from bluebottle.activity_pub.models import Event, Publish, Announce
from bluebottle.activity_pub.utils import get_platform_actor
from bluebottle.fsm.effects import Effect



class PublishEffect(Effect):
    display = True
    template = 'admin/activity_pub/publish_effect.html'

    def post_save(self, **kwargs):
        from bluebottle.activity_pub.serializers.federated_activities import FederatedDeedSerializer
        from bluebottle.activity_pub.serializers.json_ld import GoodDeedSerializer
        federated_serializer = FederatedDeedSerializer(self.instance)

        serializer = GoodDeedSerializer(data=federated_serializer.data)

        serializer.is_valid()
        event = serializer.save()

        Publish.objects.create(actor=get_platform_actor(), object=event)

    @property
    def is_valid(self):
        event = Event.objects.filter(activity=self.instance).first()
        if event:
            return False
        return get_platform_actor() is not None

    def __str__(self):
        return str(_('Publish activity to followers'))


class AnnounceAdoptionEffect(Effect):
    display = True
    template = 'admin/activity_pub/announce_adoption_effect.html'

    def post_save(self, **kwargs):
        event = self.instance.event
        actor = get_platform_actor()
        Announce.objects.create(actor=actor, object=event)

    @property
    def is_valid(self):
        event = Event.objects.filter(activity=self.instance).first()
        if not event:
            return False
        return get_platform_actor() is not None

    def __str__(self):
        return str(_('Announce that the activity has been adopted'))
