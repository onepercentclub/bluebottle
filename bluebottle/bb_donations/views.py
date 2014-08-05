from django.http.response import Http404
import logging
from bluebottle.bb_donations.serializers import ManageDonationSerializer
from django.contrib.auth.models import AnonymousUser
from rest_framework import generics
from bluebottle.utils.utils import get_project_model, get_model_class, get_serializer_class

PROJECT_MODEL = get_project_model()
DONATION_MODEL = get_model_class('DONATIONS_DONATION_MODEL')

logger = logging.getLogger(__name__)


class DonationList(generics.ListAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL', 'preview')
    # FIXME: Filter on donations that are viewable (pending & paid)


class DonationDetail(generics.RetrieveAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL', 'preview')
    # FIXME: Filter on donations that are viewable (pending & paid)


class ManageDonationList(generics.ListCreateAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL', 'manage')
    # FIXME: Add permission for OrderOwner

    def get_queryset(self, queryset=None):
        queryset = super(ManageDonationList, self).get_queryset(queryset)

        filter_kwargs = {}

        project_slug = self.request.QUERY_PARAMS.get('project', None)
        if project_slug:
            try:
                project = PROJECT_MODEL.objects.get(slug=project_slug)
            except PROJECT_MODEL.DoesNotExist:
                raise Http404(u"No project found matching the query")

            filter_kwargs['project'] = project

        user_id = self.request.QUERY_PARAMS.get('owner', None)
        if user_id:
            filter_kwargs['owner__pk'] = user_id

        return queryset.filter(**filter_kwargs).order_by('-created')


class ManageDonationDetail(generics.RetrieveUpdateDestroyAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL', 'manage')
    # FIXME: Add permission for OrderOwner


