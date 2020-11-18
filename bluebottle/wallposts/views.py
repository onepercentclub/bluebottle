import django_filters
from builtins import object
from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q
from rest_framework.generics import RetrieveDestroyAPIView

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, RelatedResourceOwnerPermission, ResourceOwnerPermission
)
from bluebottle.utils.utils import get_client_ip
from bluebottle.utils.views import (
    ListCreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView, OwnerListViewMixin,
    CreateAPIView)
from bluebottle.wallposts.permissions import RelatedManagementOrReadOnlyPermission
from .models import TextWallpost, MediaWallpost, MediaWallpostPhoto, Wallpost, Reaction
from .permissions import DonationOwnerPermission
from .serializers import (TextWallpostSerializer, MediaWallpostSerializer,
                          MediaWallpostPhotoSerializer, ReactionSerializer,
                          WallpostSerializer)


class WallpostFilter(django_filters.FilterSet):
    parent_type = django_filters.CharFilter(name="content_type__name")
    parent_id = django_filters.NumberFilter(name="object_id")

    class Meta(object):
        model = Wallpost
        fields = ['parent_type', 'parent_id']


class SetAuthorMixin(object):
    def perform_create(self, serializer):
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(author=self.request.user, **serializer.validated_data)
        )

        serializer.save(author=self.request.user, ip_address=get_client_ip(self.request))

    def perform_update(self, serializer):
        serializer.save(editor=self.request.user, ip_address=get_client_ip(self.request))


class WallpostOwnerFilterMixin(object):
    def get_queryset(self):
        qs = super(WallpostOwnerFilterMixin, self).get_queryset()
        permission = '{}.api_read_{}'.format(
            self.model._meta.app_label, self.model._meta.model_name
        )

        if not self.request.user.has_perm(permission):
            user = self.request.user if self.request.user.is_authenticated else None
            qs = qs.filter(
                Q(activity_wallposts__owner=user) |
                Q(initiative_wallposts__owner=user)
            )
        return qs


class ParentTypeFilterMixin(object):

    content_type_mapping = {
        'activities/time-based/date': 'dateactivity',
        'activities/time-based/period': 'periodactivity',
    }

    def get_queryset(self):
        queryset = super(ParentTypeFilterMixin, self).get_queryset()
        parent_type = self.request.query_params.get('parent_type', None)
        parent_id = self.request.query_params.get('parent_id', None)
        white_listed_apps = ['initiatives', 'assignments', 'events', 'funding', 'time_based']
        try:
            parent_type = self.content_type_mapping[parent_type]
        except KeyError:
            pass
        content_type = ContentType.objects.filter(app_label__in=white_listed_apps).get(model=parent_type)

        queryset = queryset.filter(content_type=content_type)
        queryset = queryset.filter(object_id=parent_id)
        queryset = queryset.order_by('-pinned', '-created')
        return queryset


class WallpostList(WallpostOwnerFilterMixin, ParentTypeFilterMixin, ListAPIView):
    queryset = Wallpost.objects.all()
    serializer_class = WallpostSerializer
    pagination_class = BluebottlePagination
    permission_classes = (
        OneOf(ResourcePermission, RelatedResourceOwnerPermission),
        DonationOwnerPermission,
        RelatedManagementOrReadOnlyPermission
    )


class WallpostPagination(BluebottlePagination):
    page_size = 5


class TextWallpostList(WallpostOwnerFilterMixin, ParentTypeFilterMixin, SetAuthorMixin, ListCreateAPIView):
    queryset = TextWallpost.objects.all()
    serializer_class = TextWallpostSerializer
    filter_class = WallpostFilter
    pagination_class = WallpostPagination

    permission_classes = (
        OneOf(ResourcePermission, RelatedResourceOwnerPermission),
        RelatedManagementOrReadOnlyPermission,
        DonationOwnerPermission,
    )

    def perform_create(self, serializer):
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(author=self.request.user, **serializer.validated_data)
        )
        return super(TextWallpostList, self).perform_create(serializer)


class TextWallpostDetail(RetrieveUpdateDestroyAPIView, SetAuthorMixin):
    queryset = TextWallpost.objects.all()
    serializer_class = TextWallpostSerializer
    permission_classes = (OneOf(ResourcePermission, ResourceOwnerPermission), )


class MediaWallpostList(TextWallpostList):
    queryset = MediaWallpost.objects.all()
    serializer_class = MediaWallpostSerializer
    filter_class = WallpostFilter
    pagination_class = WallpostPagination

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
        RelatedManagementOrReadOnlyPermission
    )

    def perform_create(self, serializer):
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(author=self.request.user, **serializer.validated_data)
        )
        return super(MediaWallpostList, self).perform_create(serializer)


class MediaWallpostDetail(TextWallpostDetail):
    queryset = MediaWallpost.objects.all()
    serializer_class = MediaWallpostSerializer


class WallpostDetail(RetrieveDestroyAPIView, SetAuthorMixin):
    queryset = Wallpost.objects.all()
    serializer_class = WallpostSerializer
    permission_classes = (
        OneOf(
            ResourcePermission,
            ResourceOwnerPermission,
            RelatedManagementOrReadOnlyPermission
        ),
    )


class MediaWallpostPhotoPagination(BluebottlePagination):
    page_size = 4


class MediaWallpostPhotoList(OwnerListViewMixin, SetAuthorMixin, ListCreateAPIView):
    queryset = MediaWallpostPhoto.objects.all()
    serializer_class = MediaWallpostPhotoSerializer
    pagination_class = MediaWallpostPhotoPagination
    permission_classes = (OneOf(ResourcePermission, ResourceOwnerPermission), )

    owner_filter_field = 'author'

    def create(self, request, *args, **kwargs):  # FIXME
        """
        Work around browser issues.

        Adding photos to a wallpost works correctly in Chrome. Firefox (at least
        FF 24) sends the ```mediawallpost``` value to Django with the value
        'null', which is then interpreted as a string in Django. This is
        incorrect behaviour, as ```mediawallpost``` is a relation.

        Eventually, this leads to HTTP400 errors, effectively breaking photo
        uploads in FF.

        The quick fix is detecting this incorrect 'null' string in ```request.POST```
        and setting it to an empty string. ```request.POST``` is mutable because
        of the multipart nature.

        NOTE: This is something that should be fixed in the Ember app or maybe even
        Ember itself.
        """
        post = request.POST.get('mediawallpost', False)
        if post and post == u'null':
            request.POST['mediawallpost'] = u''
        return super(MediaWallpostPhotoList, self).create(request, *args, **kwargs)


class MediaWallpostPhotoDetail(RetrieveUpdateDestroyAPIView):
    queryset = MediaWallpostPhoto.objects.all()
    serializer_class = MediaWallpostPhotoSerializer

    permission_classes = (OneOf(ResourcePermission, ResourceOwnerPermission), )


class ReactionList(OwnerListViewMixin, SetAuthorMixin, CreateAPIView):
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer

    permission_classes = (
        OneOf(
            ResourcePermission,
            ResourceOwnerPermission,
        ),
    )
    pagination_class = BluebottlePagination
    filter_fields = ('wallpost',)

    owner_filter_field = 'author'


class ReactionDetail(SetAuthorMixin, RetrieveUpdateDestroyAPIView):
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer
    permission_classes = (
        OneOf(
            ResourcePermission,
            ResourceOwnerPermission,
            RelatedManagementOrReadOnlyPermission
        ),
    )
