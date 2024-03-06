from builtins import object
from datetime import timedelta

from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

from bluebottle.exports.exporter import ExportModelResource
from bluebottle.impact.models import ImpactType
from bluebottle.segments.models import SegmentType


class ImpactMixin(object):

    def get_extra_fields(self):
        return super(ImpactMixin, self).get_extra_fields() + tuple([
            ("impact:{}".format(impact.slug), impact.name)
            for impact in ImpactType.objects.filter(active=True).all()
        ])


class SegmentMixin(object):
    segment_field = None

    def get_extra_fields(self):
        return super(SegmentMixin, self).get_extra_fields() + tuple([
            ("segment:{}".format(segment.slug), segment.name)
            for segment in SegmentType.objects.filter(is_active=True).all()
        ])


class DateRangeResource(ExportModelResource):
    range_field = 'created'
    select_related = None

    def export_field(self, field, obj):
        result = super().export_field(field, obj)

        if type(result) == str:
            result = ILLEGAL_CHARACTERS_RE.sub('', result)

        return result

    def get_queryset(self):
        qs = super().get_queryset()
        if self.select_related:
            qs = qs.select_related(*self.select_related)
        frm, to = self.kwargs.get('from_date'), self.kwargs.get('to_date')
        to = to + timedelta(days=1)
        return qs.filter(**{'%s__range' % self.range_field: (frm, to)})


class UserResource(SegmentMixin, DateRangeResource):
    range_field = 'date_joined'
    select_related = ('location', 'location__group')

    def get_queryset(self):
        return super(UserResource, self).get_queryset().exclude(email='devteam+accounting@onepercentclub.com')


class InitiativeResource(DateRangeResource):
    select_related = (
        'owner', 'location', 'place',
    )


class DeadlineActivityResource(ImpactMixin, SegmentMixin, DateRangeResource):
    select_related = (
        'initiative', 'owner',
    )


class DeadlineParticipantResource(SegmentMixin, DateRangeResource):
    segment_field = 'user'
    user_field = 'user'
    select_related = (
        'activity', 'activity__initiative',
    )


class DateActivityResource(ImpactMixin, SegmentMixin, DateRangeResource):
    select_related = (
        'initiative', 'owner'
    )


class DateActivitySlotResource(DateRangeResource):
    select_related = (
        'activity__initiative', 'activity', 'location', 'location__country',
    )


class DateParticipantResource(SegmentMixin, DateRangeResource):
    segment_field = 'user'
    user_field = 'user'

    select_related = (
        'activity', 'activity__initiative',
    )


class SlotParticipantResource(SegmentMixin, DateRangeResource):
    segment_field = 'participant.user'
    user_field = 'participant.user'

    range_field = 'participant__created'
    select_related = (
        'slot', 'participant', 'participant__activity', 'participant__activity__initiative',
        'participant__user',
    )


class TimeContributionResource(SegmentMixin, DateRangeResource):
    segment_field = 'contributor.user'
    user_field = 'contributor.user'

    select_related = (
        'contributor',
        'contributor__activity',
        'contributor__user',
        'contributor__activity__initiative',
    )


class FundingResource(ImpactMixin, SegmentMixin, DateRangeResource):
    select_related = (
        'initiative', 'owner'
    )


class DonationResource(SegmentMixin, DateRangeResource):
    segment_field = 'user'
    user_field = 'user'

    select_related = (
        'activity', 'user'
    )


class DeedResource(ImpactMixin, SegmentMixin, DateRangeResource):
    select_related = (
        'initiative', 'owner'
    )


class DeedParticipantResource(SegmentMixin, DateRangeResource):
    segment_field = 'user'
    user_field = 'user'
    select_related = (
        'activity', 'user', 'activity__initiative',
    )


class EffortContributionResource(SegmentMixin, DateRangeResource):
    segment_field = 'contributor.user'
    user_field = 'contributor.user'

    select_related = (
        'contributor',
        'contributor__activity',
        'contributor__user',
        'contributor__activity__initiative',
    )


class CollectActivityResource(ImpactMixin, SegmentMixin, DateRangeResource):
    select_related = (
        'initiative', 'owner'
    )


class CollectContributorResource(SegmentMixin, DateRangeResource):
    segment_field = 'user'
    user_field = 'user'
    select_related = (
        'activity', 'user', 'activity__initiative',
    )
