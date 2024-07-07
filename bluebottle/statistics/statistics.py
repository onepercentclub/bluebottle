from builtins import object

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Count
from django.db.models.aggregates import Sum
from memoize import memoize
from moneyed.classes import Money

from bluebottle.activities.models import Contributor, Activity, EffortContribution
from bluebottle.clients import properties
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
    def __init__(self, start=None, end=None):
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

    @property
    @memoize(timeout=timeout)
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

        activity_owner_ids = Activity.objects.filter(
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

        # Add donations on behalve of another person
        people_count += len(Donor.objects.filter(
            self.date_filter('contributor_date'),
            user_id__isnull=False,
            status='succeeded',
            name__isnull=False,
        ).order_by('name').distinct('name'))

        return people_count

    @property
    @memoize(timeout=timeout)
    def time_activities_succeeded(self):
        """ Total number of succeeded tasks """
        date_activities = DateActivity.objects.filter(
            self.date_filter('slots__start'),
            status='succeeded'
        )

        period_activities = PeriodicActivity.objects.filter(
            self.date_filter('deadline'),
            status='succeeded'
        )
        schedule_activities = ScheduleActivity.objects.filter(
            self.date_filter('deadline'),
            status='succeeded'
        )
        deadline_activities = DeadlineActivity.objects.filter(
            self.date_filter('deadline'),
            status='succeeded'
        )
        return len(date_activities) + len(period_activities) + len(schedule_activities) + len(deadline_activities)

    @property
    @memoize(timeout=timeout)
    def fundings_succeeded(self):
        """ Total number of succeeded tasks """
        tasks = Funding.objects.filter(
            self.date_filter('transition_date'),
            status='succeeded'
        )
        return len(tasks)

    @property
    @memoize(timeout=timeout)
    def deeds_succeeded(self):
        """ Total number of succeeded tasks """
        return len(Deed.objects.filter(
            self.date_filter('start'),
            status='succeeded'
        ))

    @property
    @memoize(timeout=timeout)
    def time_activities_online(self):
        """ Total number of online tasks """

        date_activities = DateActivity.objects.filter(
            self.date_filter('slots__start'),
            status__in=('open', 'full', 'running')
        )

        period_activities = PeriodicActivity.objects.filter(
            self.date_filter('deadline'),
            status__in=('open', 'full', 'running')
        )
        deadline_activities = DeadlineActivity.objects.filter(
            self.date_filter('deadline'),
            status__in=('open', 'full', 'running')
        )
        schedule_activities = ScheduleActivity.objects.filter(
            self.date_filter('deadline'),
            status__in=('open', 'full', 'running')
        )
        return len(date_activities) + len(period_activities) + len(deadline_activities) + len(schedule_activities)

    @property
    @memoize(timeout=timeout)
    def deeds_online(self):
        """ Total number of online tasks """

        return len(Deed.objects.filter(
            self.date_filter('start'),
            status__in=('open', 'full', 'running')
        ))

    @property
    @memoize(timeout=timeout)
    def fundings_online(self):
        """ Total number of succeeded tasks """
        fundings = Funding.objects.filter(
            self.date_filter('transition_date'),
            status='open'
        )
        return len(fundings)

    @property
    @memoize(timeout=timeout)
    def activities_succeeded(self):
        """ Total number of succeeded tasks """
        date_activities = DateActivity.objects.filter(
            self.date_filter('slots__start'),
            status='succeeded'
        )

        periodic_activities = PeriodicActivity.objects.filter(
            self.date_filter('deadline'),
            status='succeeded'
        )
        deadline_activities = DeadlineActivity.objects.filter(
            self.date_filter('deadline'),
            status='succeeded'
        )
        schedule_activities = ScheduleActivity.objects.filter(
            self.date_filter('deadline'),
            status='succeeded'
        )

        funding_activities = Funding.objects.filter(
            self.date_filter('deadline'),
            status='succeeded'
        )

        deed_activities = Deed.objects.filter(
            self.date_filter('end'),
            status='succeeded'
        )
        return (
            len(date_activities) +
            len(funding_activities) +
            len(periodic_activities) +
            len(deadline_activities) +
            len(schedule_activities) +
            len(deed_activities)
        )

    @property
    @memoize(timeout=timeout)
    def activities_online(self):
        """ Total number of activities that have been in campaign mode"""
        date_activities = DateActivity.objects.filter(
            self.date_filter('slots__start'),
            status__in=('open', 'full', 'running',)
        )

        periodic_activities = PeriodicActivity.objects.filter(
            self.date_filter('deadline'),
            status__in=('open', 'full', 'running',)
        )

        deadline_activities = DeadlineActivity.objects.filter(
            self.date_filter('deadline'),
            status__in=('open', 'full', 'running',)
        )

        schedule_activities = ScheduleActivity.objects.filter(
            self.date_filter('deadline'),
            status__in=('open', 'full', 'running',)
        )

        funding_activities = Funding.objects.filter(
            self.date_filter('deadline'),
            status__in=('open', 'full', 'running',)
        )

        deed_activities = Deed.objects.filter(
            self.date_filter('end'),
            status__in=('open', 'running',)
        )
        return (
            len(date_activities) +
            len(funding_activities) +
            len(periodic_activities) +
            len(deadline_activities) +
            len(schedule_activities) +
            len(deed_activities)
        )

    @property
    @memoize(timeout=timeout)
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
    @memoize(timeout=timeout)
    def time_spent(self):
        """ Total amount of time spent on realized tasks """
        contributions = TimeContribution.objects.filter(
            self.date_filter('start'),
            status='succeeded'
        ).aggregate(time_spent=Sum('value'))
        if contributions['time_spent']:
            return contributions['time_spent'].total_seconds() / 3600
        return 0

    @property
    @memoize(timeout=timeout)
    def deeds_done(self):
        """ Total amount of time spent on realized tasks """
        return len(EffortContribution.objects.filter(
            self.date_filter('start'),
            contributor__polymorphic_ctype=ContentType.objects.get_for_model(DeedParticipant),
            status='succeeded'
        ))

    @property
    @memoize(timeout=timeout)
    def activity_participants(self):
        """ Total number of realized task members """
        contributions = TimeContribution.objects.filter(
            self.date_filter('start'),
            status='succeeded'
        ).aggregate(count=Count('contributor__user', distinct=True))

        return contributions['count'] or 0

    @property
    @memoize(timeout=timeout)
    def donations(self):
        """ Total number of realized task members """
        donations = Donor.objects.filter(
            self.date_filter('contributor_date'),
            status='succeeded'
        )

        return len(donations)

    @property
    @memoize(timeout=timeout)
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
    @memoize(timeout=timeout)
    def participants(self):
        """ Total numbers of participants (members that started a initiative, or where a realized task member) """
        initiative_owner_count = len(
            Initiative.objects.filter(
                self.date_filter('created'),
                status='approved'
            ).order_by(
                'owner__id'
            ).distinct('owner').values_list('owner_id', flat=True)
        )

        return initiative_owner_count + self.activity_participants

    @property
    @memoize(timeout=timeout)
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
    @memoize(timeout=timeout)
    def members(self):
        """ Total amount of members."""
        members = Member.objects.filter(
            self.date_filter('date_joined'),
            is_active=True
        )
        return len(members)

    def __repr__(self):
        start = self.start.strftime('%s') if self.start else 'none'
        end = self.end.strftime('%s') if self.end else 'none'
        return 'Statistics({},{})'.format(start, end)
