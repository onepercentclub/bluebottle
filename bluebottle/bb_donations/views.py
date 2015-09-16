import logging
from django.http.response import Http404
from rest_framework import permissions, generics

from bluebottle.bb_orders.permissions import OrderIsNew, IsOrderCreator
from bluebottle.donations.serializers import LatestDonationSerializer
from bluebottle.utils.serializer_dispatcher import get_serializer_class
from bluebottle.utils.model_dispatcher import (get_project_model,
                                               get_donation_model,
                                               get_fundraiser_model)
from bluebottle.members.models import Member
from bluebottle.donations.models import Donation
from bluebottle.utils.utils import StatusDefinition

PROJECT_MODEL = get_project_model()
FUNDRAISER_MODEL = get_fundraiser_model()
DONATION_MODEL = get_donation_model()

logger = logging.getLogger(__name__)


class ValidDonationsMixin(object):
    """
    Filter query set on "valid" donations.
    """

    def get_queryset(self):
        queryset = super(ValidDonationsMixin, self).get_queryset()
        queryset = queryset.filter(order__status__in=[StatusDefinition.SUCCESS,
                                                      StatusDefinition.PENDING])
        return queryset


class DonationList(ValidDonationsMixin, generics.ListAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL',
                                            'preview')


class DonationDetail(ValidDonationsMixin, generics.RetrieveAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL',
                                            'preview')


class ProjectDonationList(ValidDonationsMixin, generics.ListAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL',
                                            'preview')

    paginate_by = 20

    def get_queryset(self):
        queryset = super(ProjectDonationList, self).get_queryset()

        filter_kwargs = {}

        project_slug = self.request.QUERY_PARAMS.get('project', None)
        fundraiser_id = self.request.QUERY_PARAMS.get('fundraiser', None)
        co_financing = 'co_financing' in self.request.QUERY_PARAMS

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

        filter_kwargs['order__user__is_co_financer'] = co_financing

        queryset = queryset.filter(**filter_kwargs)
        queryset = queryset.order_by("-created")
        return queryset


class ProjectDonationDetail(ValidDonationsMixin, generics.RetrieveAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL',
                                            'preview')


class MyProjectDonationList(ValidDonationsMixin, generics.ListAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL',
                                            'default')

    def get_queryset(self):
        queryset = super(MyProjectDonationList, self).get_queryset()

        filter_kwargs = {}

        project_slug = self.request.QUERY_PARAMS.get('project', None)
        try:
            project = PROJECT_MODEL.objects.get(slug=project_slug,
                                                owner=self.request.user)
        except PROJECT_MODEL.DoesNotExist:
            raise Http404(u"No project found matching the query")

        filter_kwargs['project'] = project
        queryset = queryset.filter(**filter_kwargs).order_by('-created')
        return queryset


class MyFundraiserDonationList(ValidDonationsMixin, generics.ListAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL',
                                            'default')

    def get_queryset(self):
        queryset = super(MyFundraiserDonationList, self).get_queryset()

        filter_kwargs = {}

        fundraiser_pk = self.request.QUERY_PARAMS.get('fundraiser', None)
        try:
            fundraiser = FUNDRAISER_MODEL.objects.get(pk=fundraiser_pk,
                                                      owner=self.request.user)
        except FUNDRAISER_MODEL.DoesNotExist:
            raise Http404(u"No fundraiser found matching the query")

        filter_kwargs['fundraiser'] = fundraiser
        queryset = queryset.filter(**filter_kwargs).order_by('-created')
        return queryset


class ManageDonationList(generics.ListCreateAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL',
                                            'manage')
    permission_classes = (IsOrderCreator, OrderIsNew)
    paginate_by = 10

    def get_queryset(self):
        queryset = super(ManageDonationList, self).get_queryset()

        filter_kwargs = {}
        user_id = self.request.user.id
        if user_id:
            filter_kwargs['order__user__pk'] = user_id

        status = self.request.QUERY_PARAMS.get('status', None)
        statuses = self.request.QUERY_PARAMS.getlist('status[]', None)
        if statuses:
            queryset = queryset.filter(order__status__in=statuses)
        elif status:
            filter_kwargs['order__status'] = status

        return queryset.filter(**filter_kwargs).order_by('-created',
                                                         'order__status')


class ManageDonationDetail(generics.RetrieveUpdateDestroyAPIView):
    model = DONATION_MODEL
    serializer_class = get_serializer_class('DONATIONS_DONATION_MODEL',
                                            'manage')

    permission_classes = (OrderIsNew, IsOrderCreator)


# For showing the latest donations
class LatestDonationsList(generics.ListAPIView):
    model = Donation
    serializer_class = LatestDonationSerializer
    permission_classes = (permissions.IsAdminUser,)
    paginate_by = 20

    def get_queryset(self):
        qs = super(LatestDonationsList, self).get_queryset()
        qs = qs.order_by('-created')
        return qs.filter(order__status__in=[StatusDefinition.PENDING,
                                            StatusDefinition.SUCCESS])
