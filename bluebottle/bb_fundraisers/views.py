from django.db.models.aggregates import Max
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from rest_framework import permissions

from bluebottle.bluebottle_drf2.views import (
    RetrieveUpdateDeleteAPIView,
    ListCreateAPIView
)
from bluebottle.fundraisers.models import Fundraiser
from bluebottle.fundraisers.serializers import BaseFundraiserSerializer
from bluebottle.projects.models import Project
from bluebottle.utils.permissions import TenantConditionalOpenClose


class FundraiserListView(ListCreateAPIView):
    queryset = Fundraiser.objects.all()
    serializer_class = BaseFundraiserSerializer
    permission_classes = (TenantConditionalOpenClose,
                          permissions.IsAuthenticatedOrReadOnly,)

    # because we overwrite get_queryset, this is ignored
    # TODO: Write cleaner code that takes this argument into account.
    # ordering = ('-created', )

    def get_queryset(self, queryset=None):
        queryset = super(FundraiserListView, self).get_queryset(queryset)

        filter_kwargs = {}

        project_slug = self.request.query_params.get('project', None)
        if project_slug:
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                raise Http404(
                    _(u"No %(verbose_name)s found matching the query") %
                    {'verbose_name': Project._meta.verbose_name})

            filter_kwargs['project'] = project

        user_id = self.request.query_params.get('owner', None)
        if user_id:
            filter_kwargs['owner__pk'] = user_id

        queryset = queryset.filter(**filter_kwargs)
        queryset = queryset.annotate(
            latest_donation=Max('donation__order__confirmed')).order_by(
            '-latest_donation')
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FundraiserDetailView(RetrieveUpdateDeleteAPIView):
    queryset = Fundraiser.objects.all()
    serializer_class = BaseFundraiserSerializer
    permission_classes = (TenantConditionalOpenClose,
                          permissions.IsAuthenticatedOrReadOnly,)
