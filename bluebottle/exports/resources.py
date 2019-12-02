from datetime import timedelta

from bluebottle.members.models import CustomMemberFieldSettings
from .exporter import ExportModelResource


class DateRangeResource(ExportModelResource):
    range_field = 'created'
    select_related = None

    def get_queryset(self):
        qs = super(DateRangeResource, self).get_queryset()
        if self.select_related:
            qs = qs.select_related(*self.select_related)
        frm, to = self.kwargs.get('from_date'), self.kwargs.get('to_date')
        to = to + timedelta(days=1)
        return qs.filter(**{'%s__range' % self.range_field: (frm, to)})


class UserResource(DateRangeResource):
    range_field = 'date_joined'
    select_related = ('location', 'location__group')

    def get_extra_fields(self):
        return tuple([
            ("extra_{}".format(extra.name), extra.description) for extra in CustomMemberFieldSettings.objects.all()
        ])


class InitiativeResource(DateRangeResource):
    select_related = (
        'owner', 'location', 'place',
    )


class AssignmentResource(DateRangeResource):
    select_related = (
        'initiative', 'owner'
    )


class ApplicantResource(DateRangeResource):
    select_related = (
        'activity', 'user'
    )


class EventResource(DateRangeResource):
    select_related = (
        'initiative', 'owner'
    )


class ParticipantResource(DateRangeResource):
    select_related = (
        'activity', 'user'
    )


class FundingResource(DateRangeResource):
    select_related = (
        'initiative', 'owner'
    )


class DonationResource(DateRangeResource):
    select_related = (
        'activity', 'user'
    )
