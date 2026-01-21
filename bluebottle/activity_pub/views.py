from celery import shared_task
from django.db import connection
from rest_framework import generics, status, response

from bluebottle.activity_pub.authentication import HTTPSignatureAuthentication
from bluebottle.activity_pub.models import (
    Person, Inbox, Outbox, PublicKey, Follow, Accept, Publish, Announce, Organization,
    GoodDeed, Image, CrowdFunding, Place, Address, DoGoodEvent, SubEvent, Update,
    Delete, Cancel, Finish
)
from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.permissions import InboxPermission, ActivityPubPermission
from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.resources import Resource
from bluebottle.activity_pub.serializers.json_ld import (
    PersonSerializer, InboxSerializer, OutboxSerializer, PublicKeySerializer, FollowSerializer,
    AcceptSerializer, ActivitySerializer, PublishSerializer, AnnounceSerializer,
    OrganizationSerializer, GoodDeedSerializer, ImageSerializer,
    CrowdFundingSerializer, PlaceSerializer, AddressSerializer,
    DoGoodEventSerializer, SubEventSerializer, UpdateSerializer,
    DeleteSerializer, CancelSerializer, FinishSerializer
)
from bluebottle.clients.utils import LocalTenant


class ActivityPubView:
    parser_classes = [JSONLDParser]
    renderer_classes = [JSONLDRenderer]
    authentication_classes = [HTTPSignatureAuthentication]
    permission_classes = [ActivityPubPermission]


class InboxView(generics.CreateAPIView, ActivityPubView):
    parser_classes = [JSONLDParser]
    renderer_classes = [JSONLDRenderer]
    authentication_classes = [HTTPSignatureAuthentication]
    permission_classes = [ActivityPubPermission]


    def create(self, request, *args, **kwargs):
        resource = Resource.from_document(request.data)
        resource.save()

        return response.Response(status=status.HTTP_204_NO_CONTENT)


class ResourceView(generics.RetrieveAPIView):
    parser_classes = [JSONLDParser]
    renderer_classes = [JSONLDRenderer]
    authentication_classes = [HTTPSignatureAuthentication]
    permission_classes = [ActivityPubPermission]

    def retrieve(self):
        return Resource.from_iri(self.request.url).document
