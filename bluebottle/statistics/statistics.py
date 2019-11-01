from django.db.models import Q
from django.db.models.aggregates import Sum

from memoize import memoize

from moneyed.classes import Money

from bluebottle.clients import properties
from bluebottle.utils.exchange_rates import convert

from bluebottle.initiatives.models import Initiative
from bluebottle.activities.models import Contribution, Activity
from bluebottle.members.models import Member
from bluebottle.events.models import Event, Participant
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.funding.models import Donation, Funding
from bluebottle.funding_pledge.models import PledgePayment
from bluebottle.votes.models import Vote


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
        contributor_ids = Contribution.objects.filter(
            self.date_filter('transition_date'),
            user_id__isnull=False,
            status__in=('new', 'accepted', 'succeeded')
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
            review_status='approved'
        ).order_by(
            'owner__id'
        ).distinct('owner').values_list('owner_id', flat=True)

        people_count = len(set(contributor_ids) | set(initiative_owner_ids) | set(activity_owner_ids))

        # Add anonymous donations
        people_count += len(Contribution.objects.filter(
            self.date_filter('transition_date'),
            user_id=None,
            status='succeeded'
        ))

        # Add donations on behalve of another person
        people_count += len(Donation.objects.filter(
            self.date_filter('transition_date'),
            user_id__isnull=False,
            status='succeeded',
            name__isnull=False,
        ).order_by('name').distinct('name'))

        return people_count

    @property
    @memoize(timeout=timeout)
    def assignments_succeeded(self):
        """ Total number of succeeded tasks """
        tasks = Assignment.objects.filter(
            self.date_filter('transition_date'),
            status='succeeded'
        )
        return len(tasks)

    @property
    @memoize(timeout=timeout)
    def events_succeeded(self):
        """ Total number of succeeded tasks """
        tasks = Event.objects.filter(
            self.date_filter('transition_date'),
            status='succeeded'
        )
        return len(tasks)

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
    def assignments_online(self):
        """ Total number of online tasks """
        tasks = Assignment.objects.filter(
            self.date_filter('transition_date'),
            status__in=('open', 'full', 'running')
        )
        return len(tasks)

    @property
    @memoize(timeout=timeout)
    def events_online(self):
        """ Total number of succeeded tasks """
        events = Event.objects.filter(
            self.date_filter('transition_date'),
            status__in=('open', 'full', 'running')
        )
        return len(events)

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
        tasks = Activity.objects.filter(
            self.date_filter('transition_date'),
            status='succeeded'
        )
        return len(tasks)

    @property
    @memoize(timeout=timeout)
    def activities_online(self):
        """ Total number of projects that have been in campaign mode"""
        return Activity.objects.filter(
            self.date_filter('transition_date'),
            status__in=('open', 'full', 'running', )
        ).count()

    @property
    @memoize(timeout=timeout)
    def donated_total(self):
        """ Total amount donated to all projects"""
        donations = Donation.objects.filter(
            self.date_filter('transition_date'),
            status='succeeded'
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
        participants = Participant.objects.filter(
            self.date_filter('transition_date'),
            status='succeeded'
        ).aggregate(total_time_spent=Sum('time_spent'))['total_time_spent'] or 0

        applicants = Applicant.objects.filter(
            self.date_filter('transition_date'),
            status='succeeded'
        ).aggregate(total_time_spent=Sum('time_spent'))['total_time_spent'] or 0

        return participants + applicants

    @property
    @memoize(timeout=timeout)
    def votes_cast(self):
        return len(Vote.objects.filter(self.date_filter()))

    @property
    @memoize(timeout=timeout)
    def event_members(self):
        """ Total number of realized task members """
        participants = Participant.objects.filter(
            self.date_filter('transition_date'),
            status='succeeded'
        )

        return len(participants)

    @property
    @memoize(timeout=timeout)
    def assignment_members(self):
        """ Total number of realized task members """
        applicants = Applicant.objects.filter(
            self.date_filter('transition_date'),
            status='succeeded'
        )

        return len(applicants)

    @property
    @memoize(timeout=timeout)
    def donations(self):
        """ Total number of realized task members """
        donations = Donation.objects.filter(
            self.date_filter('transition_date'),
            status='succeeded'
        )

        return len(donations)

    @property
    @memoize(timeout=timeout)
    def amount_matched(self):
        """ Total amount matched on realized (done and incomplete) projects """
        totals = Funding.objects.filter(
            self.date_filter('transition_date'),
            status='succeeded'
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
        """ Total numbers of participants (members that started a project, or where a realized task member) """
        project_owner_count = len(
            Initiative.objects.filter(
                self.date_filter('created'),
                status='approved'
            ).order_by(
                'owner__id'
            ).distinct('owner').values_list('owner_id', flat=True)
        )

        return project_owner_count + self.task_members

    @property
    @memoize(timeout=timeout)
    def pledged_total(self):
        """ Total amount of pledged donations """
        donations = PledgePayment.objects.filter(
            self.date_filter('donation__transition_date'),
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
            self.date_filter('created'),
            is_active=True
        )
        return len(members)

    def __repr__(self):
        start = self.start.strftime('%s') if self.start else 'none'
        end = self.end.strftime('%s') if self.end else 'none'
        return 'Statistics({},{})'.format(start, end)
