import json
import requests

from rest_framework import generics

from bluebottle.activity_pub.models import (
    Person, Inbox, Outbox, PublicKey, Follow
)
from bluebottle.activity_pub.serializers import (
    PersonSerializer, InboxSerializer, OutboxSerializer, PublicKeySerializer, FollowSerializer,
    FollowJSONAPISerializer
)

from bluebottle.utils.views import (
    JsonApiViewMixin,
    ListCreateAPIView
)


class ActivityPubView(generics.RetrieveAPIView):
    def get_queryset(self):
        return self.queryset.filter(url__isnull=True)


class PersonView(ActivityPubView):
    serializer_class = PersonSerializer
    queryset = Person.objects.all()


class InboxView(generics.CreateAPIView, ActivityPubView):
    serializer_class = InboxSerializer
    create_serializer_class = FollowSerializer
    queryset = Inbox.objects.all()

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return self.create_serializer_class
        else:
            return self.serializer_class


class OutBoxView(ActivityPubView):
    serializer_class = OutboxSerializer
    queryset = Outbox.objects.all()


class PublicKeyView(ActivityPubView):
    serializer_class = PublicKeySerializer
    queryset = PublicKey.objects.all()


class FollowView(ActivityPubView):
    serializer_class = FollowSerializer
    queryset = Follow.objects.all()


class FollowCreateView(JsonApiViewMixin, ListCreateAPIView):
    permission_classes = []
    serializer_class = FollowJSONAPISerializer
    queryset = Follow.objects.all()

    def perform_create(self, serializer):
        actor = Person.objects.from_model(self.request.user)

        response = requests.get(serializer.data['url'])
        serializer = PersonSerializer(data=response.json())
        serializer.is_valid()

        object = serializer.save()

        follow = Follow.objects.create(
            actor=actor,
            object=object

        )

        url = follow.object.inbox.url
        data = FollowSerializer(context={'request': self.request}).to_representation(follow)

        response = requests.post(
            url, data=json.dumps(data), headers={'Content-Type': 'application/json'}
        )
