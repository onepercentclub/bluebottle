from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q

import django_filters
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.bluebottle_drf2.permissions import IsAuthorOrReadOnly
from bluebottle.utils.utils import get_client_ip
from bluebottle.utils.views import (
    ListCreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView, OwnerListViewMixin
)
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, RelatedResourceOwnerPermission, ResourceOwnerPermission
)
from bluebottle.projects.models import Project
from bluebottle.wallposts.permissions import RelatedManagementOrReadOnlyPermission

from .models import TextWallpost, MediaWallpost, MediaWallpostPhoto, Wallpost, Reaction
from .serializers import (TextWallpostSerializer, MediaWallpostSerializer,
                          MediaWallpostPhotoSerializer, ReactionSerializer,
                          WallpostSerializer)
from .permissions import WallpostOwnerPermission


class WallpostFilter(django_filters.FilterSet):
    parent_type = django_filters.CharFilter(name="content_type__name")
    parent_id = django_filters.NumberFilter(name="object_id")

    class Meta:
        model = Wallpost
        fields = ['parent_type', 'parent_id']


class SetAuthorMixin(object):
    def perform_create(self, serializer):
        serializer.save(author=self.request.user, ip_address=get_client_ip(self.request))

    def perform_update(self, serializer):
        serializer.save(editor=self.request.user, ip_address=get_client_ip(self.request))


class FilterQSParams(object):

    def get_qs(self, qs):
        parent_id = self.request.query_params.get('parent_id', None)
        parent_type = self.request.query_params.get('parent_type', None)
        if parent_type == 'project':
            qs = qs.filter(conten_object__slug=parent_id)
        elif parent_id:
            qs = qs.filter(conten_object__id=parent_id)

        text = self.request.query_params.get('text', None)
        if text:
            qs = qs.filter(Q(title__icontains=text) |
                           Q(description__icontains=text))

        status = self.request.query_params.get('status', None)
        if status:
            qs = qs.filter(status=status)
        return qs


class WallpostList(OwnerListViewMixin, ListAPIView):
    queryset = Wallpost.objects.all()
    serializer_class = WallpostSerializer
    pagination_class = BluebottlePagination
    permission_classes = (
        OneOf(ResourcePermission, RelatedResourceOwnerPermission),
        RelatedManagementOrReadOnlyPermission
    )

    owner_filter_field = 'content_object__owner'

    def get_queryset(self, queryset=queryset):
        queryset = super(WallpostList, self).get_queryset()

        # Some custom filtering projects slugs.
        parent_type = self.request.query_params.get('parent_type', None)
        parent_id = self.request.query_params.get('parent_id', None)
        if parent_type == 'project':
            content_type = ContentType.objects.get_for_model(Project)
        else:
            white_listed_apps = ['projects', 'tasks', 'fundraisers']
            content_type = ContentType.objects.filter(
                app_label__in=white_listed_apps).get(model=parent_type)
        queryset = queryset.filter(content_type=content_type)

        if parent_type == 'project' and parent_id:
            try:
                project = Project.objects.get(slug=parent_id)
            except Project.DoesNotExist:
                return Wallpost.objects.none()
            queryset = queryset.filter(object_id=project.id)
        else:
            queryset = queryset.filter(object_id=parent_id)

        queryset = queryset.order_by('-created')
        return queryset


class WallpostPagination(BluebottlePagination):
    page_size = 5


class TextWallpostList(OwnerListViewMixin, SetAuthorMixin, ListCreateAPIView, FilterQSParams):
    queryset = TextWallpost.objects.all()
    serializer_class = TextWallpostSerializer
    filter_class = WallpostFilter
    pagination_class = WallpostPagination

    permission_classes = (
        OneOf(ResourcePermission, RelatedResourceOwnerPermission),
        RelatedManagementOrReadOnlyPermission
    )

    owner_filter_field = 'content_object__owner'

    def get_queryset(self, queryset=None):
        queryset = self.queryset
        # Some custom filtering projects slugs.
        parent_type = self.request.query_params.get('parent_type', None)
        parent_id = self.request.query_params.get('parent_id', None)
        if parent_type == 'project' and parent_id:
            try:
                project = Project.objects.get(slug=parent_id)
            except Project.DoesNotExist:
                return Wallpost.objects.none()
            queryset = queryset.filter(object_id=project.id)
        queryset = queryset.order_by('-created')
        return queryset


class TextWallpostDetail(RetrieveUpdateDestroyAPIView, SetAuthorMixin):
    queryset = TextWallpost.objects.all()
    serializer_class = TextWallpostSerializer
    permission_classes = (OneOf(ResourcePermission, RelatedResourceOwnerPermission), )


class MediaWallpostList(TextWallpostList, SetAuthorMixin):
    queryset = MediaWallpost.objects.all()
    serializer_class = MediaWallpostSerializer
    filter_class = WallpostFilter
    pagination_class = WallpostPagination

    permission_classes = (
        OneOf(ResourcePermission, RelatedResourceOwnerPermission),
        RelatedManagementOrReadOnlyPermission
    )

    def perform_create(self, serializer):
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )
        return super(MediaWallpostList, self).perform_create(serializer)


class MediaWallpostDetail(TextWallpostDetail):
    queryset = MediaWallpost.objects.all()
    serializer_class = MediaWallpostSerializer


class WallpostDetail(RetrieveUpdateDestroyAPIView):
    queryset = Wallpost.objects.all()
    serializer_class = WallpostSerializer
    permission_classes = (
        OneOf(ResourcePermission, RelatedResourceOwnerPermission),
        WallpostOwnerPermission
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


class ReactionList(OwnerListViewMixin, SetAuthorMixin, ListCreateAPIView):
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer

    permission_classes = (OneOf(ResourcePermission, ResourceOwnerPermission), )
    pagination_class = BluebottlePagination
    filter_fields = ('wallpost',)

    owner_filter_field = 'author'


class ReactionDetail(SetAuthorMixin, RetrieveUpdateDestroyAPIView):
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer
    permission_classes = (OneOf(ResourcePermission, ResourceOwnerPermission), )
