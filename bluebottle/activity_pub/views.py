from rest_framework import generics

from bluebottle.activity_pub.models import (
    Person, Inbox, Outbox, PublicKey, Follow, Accept, Publish, Event, Announce
)
from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.serializers import (
    PersonSerializer, InboxSerializer, OutboxSerializer, PublicKeySerializer, FollowSerializer,
    AcceptSerializer, ActivitySerializer, EventSerializer, PublishSerializer, AnnounceSerializer
)


class ActivityPubView(generics.RetrieveAPIView):
    parser_classes = [JSONLDParser]
    renderer_classes = [JSONLDRenderer]

    def get_queryset(self):
        return self.queryset.filter(url__isnull=True)


class PersonView(ActivityPubView):
    serializer_class = PersonSerializer
    queryset = Person.objects.all()


class InboxView(generics.CreateAPIView, ActivityPubView):
    serializer_class = InboxSerializer
    queryset = Inbox.objects.all()

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return ActivitySerializer
        else:
            return self.serializer_class


class OutBoxView(ActivityPubView):
    serializer_class = OutboxSerializer
    queryset = Outbox.objects.all()


class EventView(ActivityPubView):
    serializer_class = EventSerializer
    queryset = Event.objects.all()


class PublicKeyView(ActivityPubView):
    serializer_class = PublicKeySerializer
    queryset = PublicKey.objects.all()


class FollowView(ActivityPubView):
    serializer_class = FollowSerializer
    queryset = Follow.objects.all()


class AcceptView(ActivityPubView):
    serializer_class = AcceptSerializer
    queryset = Accept.objects.all()


class PublishView(ActivityPubView):
    serializer_class = PublishSerializer
    queryset = Publish.objects.all()


class AnnounceView(ActivityPubView):
    serializer_class = AnnounceSerializer
    queryset = Announce.objects.all()
