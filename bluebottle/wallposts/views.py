from django.contrib.contenttypes.models import ContentType
from rest_framework.permissions import IsAuthenticatedOrReadOnly
import django_filters
from rest_framework import permissions

from bluebottle.bluebottle_drf2.permissions import IsAuthorOrReadOnly
from bluebottle.utils.utils import set_author_editor_ip, get_client_ip
from bluebottle.bluebottle_drf2.views import ListCreateAPIView, RetrieveUpdateDeleteAPIView, ListAPIView
from bluebottle.utils.model_dispatcher import get_project_model, get_fundraiser_model

from .models import TextWallpost, MediaWallpost, MediaWallpostPhoto
from .permissions import IsConnectedWallpostAuthorOrReadOnly
from .serializers import TextWallpostSerializer, MediaWallpostSerializer, MediaWallpostPhotoSerializer
from .models import Wallpost, Reaction
from .serializers import ReactionSerializer, WallpostSerializer

PROJECT_MODEL = get_project_model()
FUNDRAISER_MODEL = get_fundraiser_model()

class WallpostFilter(django_filters.FilterSet):
    parent_type = django_filters.CharFilter(name="content_type__name")
    parent_id = django_filters.NumberFilter(name="object_id")

    class Meta:
        model = Wallpost
        fields = ['parent_type', 'parent_id']


class WallpostList(ListAPIView):
    model = Wallpost
    serializer_class = WallpostSerializer
    paginate_by = 5

    def get_queryset(self):
        queryset = super(WallpostList, self).get_queryset()

        # Some custom filtering projects slugs.
        parent_type = self.request.QUERY_PARAMS.get('parent_type', None)
        parent_id = self.request.QUERY_PARAMS.get('parent_id', None)
        if parent_type == 'project':
            content_type = ContentType.objects.get_for_model(PROJECT_MODEL)
        else:
            white_listed_apps = ['projects', 'tasks', 'fundraisers']
            content_type = ContentType.objects.filter(app_label__in=white_listed_apps).get(name=parent_type)
        queryset = queryset.filter(content_type=content_type)

        if parent_type == 'project' and parent_id:
            try:
                project = PROJECT_MODEL.objects.get(slug=parent_id)
            except PROJECT_MODEL.DoesNotExist:
                return Wallpost.objects.none()
            queryset = queryset.filter(object_id=project.id)
        else:
            queryset = queryset.filter(object_id=parent_id)

        queryset = queryset.order_by('-created')
        return queryset


class TextWallpostList(ListCreateAPIView):
    model = TextWallpost
    serializer_class = TextWallpostSerializer
    filter_class = WallpostFilter
    paginate_by = 5
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def get_queryset(self):
        queryset = super(TextWallpostList, self).get_queryset()
        # Some custom filtering projects slugs.
        parent_type = self.request.QUERY_PARAMS.get('parent_type', None)
        parent_id = self.request.QUERY_PARAMS.get('parent_id', None)
        if parent_type == 'project' and parent_id:
            try:
                project = PROJECT_MODEL.objects.get(slug=parent_id)
            except PROJECT_MODEL.DoesNotExist:
                return Wallpost.objects.none()
            queryset = queryset.filter(object_id=project.id)

        queryset = queryset.order_by('-created')
        return queryset

    def pre_save(self, obj):
        if not obj.author:
            obj.author = self.request.user
        else:
            obj.editor = self.request.user
        obj.ip_address = get_client_ip(self.request)


class MediaWallpostList(TextWallpostList):
    model = MediaWallpost
    serializer_class = MediaWallpostSerializer
    filter_class = WallpostFilter
    paginate_by = 5


class WallpostDetail(RetrieveUpdateDeleteAPIView):
    model = Wallpost
    serializer_class = WallpostSerializer
    permission_classes = (IsAuthorOrReadOnly, )


class MediaWallpostPhotoList(ListCreateAPIView):
    model = MediaWallpostPhoto
    serializer_class = MediaWallpostPhotoSerializer
    paginate_by = 4

    def pre_save(self, obj):
        if not obj.author:
            obj.author = self.request.user
        else:
            obj.editor = self.request.user
        obj.ip_address = get_client_ip(self.request)

    def create(self, request, *args, **kwargs): #FIXME
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


class MediaWallpostPhotoDetail(RetrieveUpdateDeleteAPIView):
    model = MediaWallpostPhoto
    serializer_class = MediaWallpostPhotoSerializer
    permission_classes = (IsAuthorOrReadOnly, IsConnectedWallpostAuthorOrReadOnly)


class ReactionList(ListCreateAPIView):
    # model = Reaction
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    paginate_by = 10
    filter_fields = ('wallpost',)

    def pre_save(self, obj):
        set_author_editor_ip(self.request, obj)


class ReactionDetail(RetrieveUpdateDeleteAPIView):
    model = Reaction
    serializer_class = ReactionSerializer
    permission_classes = (IsAuthorOrReadOnly,)

    def pre_save(self, obj):
        set_author_editor_ip(self.request, obj)
