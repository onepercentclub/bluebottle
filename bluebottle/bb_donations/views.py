from bluebottle.bb_donations.models import DonationStatuses
from django.http.response import Http404
import logging
from bluebottle.bb_donations.serializers import ManageDonationSerializer
from django.contrib.auth.models import AnonymousUser
from rest_framework import generics
from bluebottle.utils.utils import get_project_model, get_model_class, get_serializer_class

PROJECT_MODEL = get_model_class('PROJECTS_PROJECT_MODEL')
FUNDRAISER_MODEL = get_model_class('FUNDRAISERS_FUNDRAISER_MODEL')
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


class ProjectDonationList(generics.ListAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL', 'preview')
    # FIXME: Filter on donations that are viewable (pending & paid)

    def get_queryset(self):
        queryset = super(ProjectDonationList, self).get_queryset()

        filter_kwargs = {}

        project_slug = self.request.QUERY_PARAMS.get('project', None)
        fundraiser_id = self.request.QUERY_PARAMS.get('fundraiser', None)
        if fundraiser_id:
            try:
                fundraiser = FUNDRAISER_MODEL.objects.get(pk=fundraiser_id)
                filter_kwargs['fundraiser'] = fundraiser
            except FUNDRAISER_MODEL.DoesNotExist:
                raise Http404(u"No %(verbose_name)s found matching the query" %
                              {'verbose_name': FUNDRAISER_MODEL._meta.verbose_name})
        elif project_slug:
            try:
                project = PROJECT_MODEL.objects.get(slug=project_slug)
                filter_kwargs['project'] = project
            except PROJECT_MODEL.DoesNotExist:
                raise Http404(u"No %(verbose_name)s found matching the query" %
                              {'verbose_name': queryset.model._meta.verbose_name})
        else:
            raise Http404(u"No %(verbose_name)s found matching the query" %
                          {'verbose_name': PROJECT_MODEL._meta.verbose_name})


        queryset = queryset.filter(**filter_kwargs)
        queryset = queryset.order_by("-created")
        queryset = queryset.filter(status__in=[DonationStatuses.paid, DonationStatuses.pending])

        return queryset


class ProjectDonationDetail(generics.RetrieveAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL', 'preview')
    # FIXME: Filter on donations that are viewable (pending & paid)


class ManageDonationList(generics.ListCreateAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL', 'manage')
    # FIXME: Add permission for OrderOwner

    def get_queryset(self):
        queryset = super(ManageDonationList, self).get_queryset()

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

