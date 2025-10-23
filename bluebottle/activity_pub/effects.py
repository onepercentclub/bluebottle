from django.utils.translation import gettext_lazy as _

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import Publish, Announce
from bluebottle.activity_pub.utils import get_platform_actor
from bluebottle.fsm.effects import Effect


class CreateOrUpdateEvent(Effect):
    display = False

    def post_save(self, **kwargs):
        from bluebottle.activity_pub.serializers.federated_activities import FederatedActivitySerializer
        from bluebottle.activity_pub.serializers.json_ld import EventSerializer

        federated_serializer = FederatedActivitySerializer(self.instance)

        serializer = EventSerializer(data=federated_serializer.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(activity=self.instance)


    @property
    def is_valid(self):
        return get_platform_actor() is not None

    def __str__(self):
        return str(_('Create publish for activity'))


class CreatePublishEffect(Effect):
    display = True
    template = 'admin/activity_pub/publish_effect.html'

    def post_save(self, **kwargs):
        event = self.instance.event

        try:
            Publish.objects.get(object=event)
        except Publish.DoesNotExist:
            publish = Publish.objects.create(object=event)
            adapter.publish(publish)


    @property
    def is_valid(self):
        return get_platform_actor() is not None 

    def __str__(self):
        return str(_('Publish activity to followers'))


class AnnounceAdoptionEffect(Effect):
    display = True
    template = 'admin/activity_pub/announce_adoption_effect.html'

    def post_save(self, **kwargs):
        event = self.instance.origin
        actor = get_platform_actor()
        announce = Announce.objects.create(actor=actor, object=event)
        adapter.publish(announce)

    @property
    def is_valid(self):
        return self.instance.origin and get_platform_actor() is not None

    def __str__(self):
        return str(_('Announce that the activity has been adopted'))
