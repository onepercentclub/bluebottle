from celery import shared_task
from django.db import connection
from rest_framework import generics, status, response

from bluebottle.activity_pub.authentication import HTTPSignatureAuthentication
from bluebottle.activity_pub.models import (
    Person, Inbox, Outbox, PublicKey, Follow, Accept, Publish, Announce, Organization,
    GoodDeed, Image, CrowdFunding, Place, Address, DoGoodEvent, SubEvent
)
from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.permissions import InboxPermission, ActivityPubPermission
from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.serializers.json_ld import (
    PersonSerializer, InboxSerializer, OutboxSerializer, PublicKeySerializer, FollowSerializer,
    AcceptSerializer, ActivitySerializer, PublishSerializer, AnnounceSerializer,
    OrganizationSerializer, GoodDeedSerializer, ImageSerializer,
    CrowdFundingSerializer, PlaceSerializer, AddressSerializer,
    DoGoodEventSerializer, SubEventSerializer
)
from bluebottle.clients.utils import LocalTenant


class ActivityPubView(generics.RetrieveAPIView):
    parser_classes = [JSONLDParser]
    renderer_classes = [JSONLDRenderer]
    authentication_classes = [HTTPSignatureAuthentication]
    permission_classes = [ActivityPubPermission]

    def get_queryset(self):
        return self.queryset.filter(iri__isnull=True)


class PersonView(ActivityPubView):
    serializer_class = PersonSerializer
    queryset = Person.objects.all()


class OrganizationView(ActivityPubView):
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()


@shared_task()
def create_task(serializer, tenant):
    with LocalTenant(tenant):
        serializer.is_valid(raise_exception=True)
        serializer.save()


class PickableRequest:
    def __init__(self, request):
        self.path = request.path
        self.user = request.user
        self.headers = request.headers
        self.auth = request.auth


class InboxView(generics.CreateAPIView, ActivityPubView):
    serializer_class = InboxSerializer
    queryset = Inbox.objects.all()

    permission_classes = [InboxPermission]

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return ActivitySerializer
        else:
            return self.serializer_class

    def get_serializer_context(self):
        return {'request': PickableRequest(self.request)}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        create_task.delay(serializer, connection.tenant)
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class OutBoxView(ActivityPubView):
    serializer_class = OutboxSerializer
    queryset = Outbox.objects.all()


class ImageView(ActivityPubView):
    serializer_class = ImageSerializer
    queryset = Image.objects.all()


class PlaceView(ActivityPubView):
    serializer_class = PlaceSerializer
    queryset = Place.objects.all()


class AddressView(ActivityPubView):
    serializer_class = AddressSerializer
    queryset = Address.objects.all()


class GoodDeedView(ActivityPubView):
    serializer_class = GoodDeedSerializer
    queryset = GoodDeed.objects.all()


class CrowdFundingView(ActivityPubView):
    serializer_class = CrowdFundingSerializer
    queryset = CrowdFunding.objects.all()


class SubEventView(ActivityPubView):
    serializer_class = SubEventSerializer
    queryset = SubEvent.objects.all()


class DoGoodEventView(ActivityPubView):
    serializer_class = DoGoodEventSerializer
    queryset = DoGoodEvent.objects.all()


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
