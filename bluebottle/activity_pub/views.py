from django.db import connection
from django.urls import reverse, resolve
from django.core.paginator import EmptyPage
from rest_framework import generics, pagination, response

from bluebottle.activity_pub.authentication import HTTPSignatureAuthentication
from bluebottle.activity_pub.models import (
    Person, Inbox, Outbox, PublicKey, Follow, Accept, Publish, Announce, Organization,
    GoodDeed, Image, CrowdFunding, Place, Address, Activity
)
from bluebottle.activity_pub.parsers import JSONLDParser
from bluebottle.activity_pub.permissions import (
    ActivityPubPermission, InboxPermission, OutboxPermission
)
from bluebottle.activity_pub.renderers import JSONLDRenderer
from bluebottle.activity_pub.serializers.json_ld import (
    PersonSerializer, InboxSerializer, OutboxSerializer, PublicKeySerializer, FollowSerializer,
    AcceptSerializer, ActivitySerializer, PublishSerializer, AnnounceSerializer,
    OrganizationSerializer, GoodDeedSerializer, ImageSerializer,
    CrowdFundingSerializer, PlaceSerializer, AddressSerializer
)

class CollectionPagination(pagination.PageNumberPagination):
    page_size = 3
    url_name = None

    def get_page_number(self, request, paginator):
        return resolve(request.path).kwargs.get('page', 1)

    def paginate_queryset(self, queryset, request, view=None):
        self.view_kwargs = view.kwargs

        return super().paginate_queryset(queryset, request, view)

    def get_link(self, page):
        kwargs = dict(**self.view_kwargs)
        kwargs['page'] = page

        return connection.tenant.build_absolute_url(
            reverse(self.url_name, kwargs=kwargs)
        )

    def get_paginated_response(self, data):
        paginated_data = {
            'totalItems': self.page.paginator.count,
            'type': 'OrderedCollectionPage',
            'items': data,
            'first': self.get_link(1),
            'last': self.get_link(self.page.paginator.num_pages),
        }

        try:
            paginated_data['prev'] = self.get_link(self.page.previous_page_number())
        except EmptyPage:
            pass

        try:
            paginated_data['next'] = self.get_link(self.page.next_page_number())
        except EmptyPage:
            pass

        return response.Response(paginated_data)


class ActivityPubMixin:
    parser_classes = [JSONLDParser]
    renderer_classes = [JSONLDRenderer]
    authentication_classes = [HTTPSignatureAuthentication]

    permission_classes = [ActivityPubPermission]
    pagination_class = CollectionPagination

    def get_queryset(self):
        return self.queryset.filter(iri__isnull=True)


class ActivityPubView(ActivityPubMixin, generics.RetrieveAPIView):
    def get_queryset(self):
        return self.queryset.filter(iri__isnull=True)


class PersonView(ActivityPubView):
    serializer_class = PersonSerializer
    queryset = Person.objects.all()


class OrganizationView(ActivityPubView):
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()


class InboxView(generics.CreateAPIView, ActivityPubView):
    serializer_class = InboxSerializer
    queryset = Inbox.objects.all()

    permission_classes = [InboxPermission]

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return ActivitySerializer
        else:
            return self.serializer_class


class OutboxPagination(CollectionPagination):
    url_name = 'activity_pub:outbox-page'


class OutboxPageView(ActivityPubMixin, generics.ListAPIView):
    pagination_class = OutboxPagination
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [OutboxPermission]

    def get_queryset(self):
        outbox = Outbox.objects.get(pk=self.kwargs['pk'])

        to = [self.request.auth.iri, outbox.actor.followers.pub_url]

        return super().get_queryset().filter(
            to__overlap=to
        )


class OutboxView(ActivityPubView):
    pagination_class = OutboxPagination
    serializer_class = OutboxSerializer
    queryset = Outbox.objects.all()
    permission_classes = [OutboxPermission]

    page_view = OutboxPageView


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


class FollowersView(ActivityPubView):
    def retrieve(self, request):
        return response.Response()