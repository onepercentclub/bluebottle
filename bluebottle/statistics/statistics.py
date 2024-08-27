from builtins import object

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Count
from django.db.models.aggregates import Sum
from moneyed.classes import Money

from bluebottle.activities.models import Contributor, EffortContribution, Activity
from bluebottle.clients import properties
from bluebottle.collect.models import CollectActivity
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.funding.models import Donor, Funding
from bluebottle.funding_pledge.models import PledgePayment
from bluebottle.initiatives.models import Initiative
from bluebottle.members.models import Member
from bluebottle.time_based.models import (
    DateActivity,
    PeriodicActivity,
    DeadlineActivity,
    ScheduleActivity,
    TimeContribution
)
from bluebottle.utils.exchange_rates import convert


class Statistics(object):
    def __init__(self, start=None, end=None, subregion=None):
        self.subregion = subregion
        self.start = start
        self.end = end

    timeout = 3600

    def date_filter(self, field='created'):
        if self.start and self.end:
            filter_args = {'{}__range'.format(field): (self.start, self.end)}
        elif self.start:
            filter_args = {'{}__gte'.format(field): self.start}
        elif self.end:
            filter_args = {'{}__lte'.format(field): self.end}
        else:
            filter_args = {}

        return Q(**filter_args)

    def filter_activities(self, model, date_field, statuses):
        activities = model.objects.filter(
            self.date_filter(date_field),
            status__in=statuses
        )
        if self.subregion:
            activities = activities.filter(
                office_location__subregion=self.subregion
            )
        return activities

    @property
    def people_involved(self):
        """
        The (unique) total number of people that donated, fundraised, campaigned, or was a
        task owner or  member.
        """
        contributor_ids = Contributor.objects.filter(
            self.date_filter('contributions__start'),
            user_id__isnull=False,
            status__in=('new', 'accepted', 'active', 'succeeded')
        ).order_by(
            'user__id'
        ).distinct('user').values_list('user_id', flat=True)

        initiative_owner_ids = Initiative.objects.filter(
            self.date_filter('created'),
            status='approved'
        ).order_by(
            'owner__id'
        ).distinct('owner').values_list('owner_id', flat=True)

        activity_owner_ids = Activity .objects.filter(
            self.date_filter('created'),
            status__in=['open', 'full', 'running', 'succeeded', 'partially_funded']
        ).order_by(
            'owner__id'
        ).distinct('owner').values_list('owner_id', flat=True)

        people_count = len(set(contributor_ids) | set(initiative_owner_ids) | set(activity_owner_ids))

        # Add anonymous donations
        people_count += len(Contributor.objects.filter(
            self.date_filter('contributor_date'),
            user_id=None,
            status='succeeded'
        ))

        # Add donations on behalf of another person
        people_count += len(Donor.objects.filter(
            self.date_filter('contributor_date'),
            user_id__isnull=False,
            status='succeeded',
            name__isnull=False,
        ).order_by('name').distinct('name'))

        return people_count

    @property
    def time_activities_succeeded(self):
        """ Total number of succeeded tasks """

        activity_filters = [
            (DateActivity, 'slots__start'),
            (PeriodicActivity, 'deadline'),
            (DeadlineActivity, 'deadline'),
            (ScheduleActivity, 'deadline'),
        ]

        return sum(
            len(self.filter_activities(model, date_field, ['succeeded']))
            for model, date_field in activity_filters
        )

    @property
    def fundings_succeeded(self):
        """ Total number of succeeded tasks """
        tasks = Funding.objects.filter(
            self.date_filter('deadline'),
            status='succeeded'
        )
        return len(tasks)

    @property
    def deeds_succeeded(self):
        """ Total number of succeeded tasks """
        return len(Deed.objects.filter(
            self.date_filter('start'),
            status='succeeded'
        ))

    @property
    def time_activities_online(self):
        """ Total number of online tasks """

    @property
    def deeds_online(self):
        """ Total number of online tasks """

        return len(Deed.objects.filter(
            self.date_filter('start'),
            status__in=('open', 'full', 'running')
        ))

    @property
    def fundings_online(self):
        """ Total number of succeeded tasks """
        fundings = Funding.objects.filter(
            self.date_filter('transition_date'),
            status='open'
        )
        return len(fundings)

    @property
    def activities_succeeded(self):
        """ Total number of succeeded tasks """

        activity_filters = [
            (DateActivity, 'slots__start'),
            (PeriodicActivity, 'deadline'),
            (DeadlineActivity, 'deadline'),
            (ScheduleActivity, 'deadline'),
            (CollectActivity, 'end'),
            (Funding, 'deadline'),
            (Deed, 'end'),
        ]

        return sum(
            len(self.filter_activities(model, date_field, ['succeeded']))
            for model, date_field in activity_filters
        )

    @property
    def activities_online(self):
        """Total number of activities that have been in campaign mode"""

        activity_filters = [
            (DateActivity, 'slots__start'),
            (PeriodicActivity, 'start'),
            (DeadlineActivity, 'start'),
            (ScheduleActivity, 'start'),
            (CollectActivity, 'start'),
            (Funding, 'started'),
            (Deed, 'start'),
        ]

        return sum(
            len(self.filter_activities(model, date_field, ['open', 'full', 'running']))
            for model, date_field in activity_filters
        )

    @property
    def donated_total(self):
        """ Total amount donated to all activities"""
        donations = Donor.objects.filter(
            self.date_filter('created'),
            status='succeeded',
        )
        totals = donations.order_by('amount_currency').values('amount_currency').annotate(total=Sum('amount'))
        amounts = [Money(total['total'], total['amount_currency']) for total in totals]
        if totals:
            donated = sum([convert(amount, properties.DEFAULT_CURRENCY) for amount in amounts])
        else:
            donated = Money(0, properties.DEFAULT_CURRENCY)

        return donated

    @property
    def time_spent(self):
        """ Total amount of time spent on realized tasks """
        contributions = TimeContribution.objects.filter(
            self.date_filter('start'),
            status='succeeded'
        )
        if self.subregion:
            contributions = contributions.filter(
                contributor__user__location__subregion=self.subregion
            )

        contributions = contributions.aggregate(time_spent=Sum('value'))
        if contributions['time_spent']:
            return contributions['time_spent'].total_seconds() / 3600
        return 0

    @property
    def deeds_done(self):
        """ Total amount of time spent on realized tasks """
        efforts = EffortContribution.objects.filter(
            self.date_filter('start'),
            contributor__polymorphic_ctype=ContentType.objects.get_for_model(DeedParticipant),
            status='succeeded'
        )
        if self.subregion:
            efforts = efforts.filter(
                contributor__user__location__subregion=self.subregion
            )
        return efforts.count()

    @property
    def activity_participants(self):
        """ Total number of realized task members """
        contributions = TimeContribution.objects.filter(
            self.date_filter('start'),
            status='succeeded'
        )

        if self.subregion:
            contributions = contributions.filter(
                contributor__user__location__subregion=self.subregion
            )

        contributions = contributions.aggregate(count=Count('contributor__user', distinct=True))
        return contributions['count'] or 0

    @property
    def donations(self):
        """ Total number of realized task members """
        donations = Donor.objects.filter(
            self.date_filter('contributor_date'),
            status='succeeded'
        )

        return len(donations)

    @property
    def amount_matched(self):
        """ Total amount matched on realized (done and incomplete) activities """
        totals = Funding.objects.filter(
            self.date_filter('transition_date'),
            status__in=['succeeded', 'open', 'partial']
        ).filter(
            amount_matching__gt=0
        ).values('amount_matching_currency').annotate(total=Sum('amount_matching'))

        amounts = [Money(total['total'], total['amount_matching_currency']) for total in totals]
        if totals:
            return sum([convert(amount, properties.DEFAULT_CURRENCY) for amount in amounts])
        else:
            return Money(0, properties.DEFAULT_CURRENCY)

    @property
    def participants(self):
        """ Total numbers of participants (members that started a initiative, or where a realized task member) """
        initiative_owners = Initiative.objects.filter(
            self.date_filter('created'),
            status='approved'
        ).distinct('owner')

        if self.subregion:
            initiative_owners = initiative_owners.filter(
                owner__location__subregion=self.subregion
            )

        return initiative_owners.count() + self.activity_participants

    @property
    def pledged_total(self):
        """ Total amount of pledged donations """
        donations = PledgePayment.objects.filter(
            self.date_filter('created'),
            donation__status='succeeded'
        )
        totals = donations.values(
            'donation__amount_currency'
        ).annotate(total=Sum('donation__amount'))

        amounts = [Money(total['total'], total['donation__amount_currency']) for total in totals]
        if totals:
            donated = sum([convert(amount, properties.DEFAULT_CURRENCY) for amount in amounts])
        else:
            donated = Money(0, properties.DEFAULT_CURRENCY)

        return donated

    @property
    def members(self):
        """ Total amount of members."""
        members = Member.objects.filter(
            self.date_filter('date_joined'),
            is_active=True
        )
        if self.subregion:
            members = members.filter(location__subregion=self.subregion)
        return len(members)

    def __repr__(self):
        start = self.start.strftime('%s') if self.start else 'none'
        end = self.end.strftime('%s') if self.end else 'none'
        return 'Statistics({},{})'.format(start, end)
