from django.db.models import Count
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from bluebottle.bluebottle_drf2.views import RetrieveUpdateDeleteAPIView, ListCreateAPIView
from rest_framework import permissions, exceptions

from bluebottle.utils.serializer_dispatcher import get_serializer_class
from bluebottle.utils.model_dispatcher import get_project_model, get_fundraiser_model

PROJECT_MODEL = get_project_model()
FUNDRAISER_MODEL = get_fundraiser_model()

FUNDRAISER_SERIALIZER = get_serializer_class('FUNDRAISERS_FUNDRAISER_MODEL', 'default')


class FundRaiserListView(ListCreateAPIView):
    model = FUNDRAISER_MODEL
    serializer_class = FUNDRAISER_SERIALIZER
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    paginate_by = 10
    paginate_by_param = 'page_size'

    # because we overwrite get_queryset, this is ignored
    # TODO: Write cleaner code that takes this argument into account.
    # ordering = ('-created', )

    def get_queryset(self, queryset=None):
        queryset = super(FundRaiserListView, self).get_queryset(queryset)

        filter_kwargs = {}

        project_slug = self.request.QUERY_PARAMS.get('project', None)
        if project_slug:
            try:
                project = PROJECT_MODEL.objects.get(slug=project_slug)
            except PROJECT_MODEL.DoesNotExist:
                raise Http404(_(u"No %(verbose_name)s found matching the query") %
                              {'verbose_name': PROJECT_MODEL._meta.verbose_name})

            filter_kwargs['project'] = project

        user_id = self.request.QUERY_PARAMS.get('owner', None)
        if user_id:
            filter_kwargs['owner__pk'] = user_id


        # queryset.filter(**filter_kwargs).order_by('-created') # shows all not ordered per donation__created
        # queryset.filter(**filter_kwargs).order_by('-donation__created') # last donation appears more than one time some donation are not shown
        # queryset.filter(**filter_kwargs).order_by('id', '-donation__created').distinct('id')
        return queryset.filter(**filter_kwargs).order_by('-updated')

    def pre_save(self, obj):
        if not self.request.user.is_authenticated():
            raise exceptions.PermissionDenied()

        obj.owner = self.request.user


class FundRaiserDetailView(RetrieveUpdateDeleteAPIView):
    model = FUNDRAISER_MODEL
    serializer_class = FUNDRAISER_SERIALIZER
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


