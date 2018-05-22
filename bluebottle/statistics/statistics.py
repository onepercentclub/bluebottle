from django.db.models import Q
from django.db.models.aggregates import Sum

from memoize import memoize

from moneyed.classes import Money

from bluebottle.clients import properties
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.utils import StatusDefinition

from bluebottle.donations.models import Donation
from bluebottle.fundraisers.models import Fundraiser
from bluebottle.members.models import Member
from bluebottle.orders.models import Order
from bluebottle.projects.models import Project
from bluebottle.tasks.models import Task, TaskMember
from bluebottle.votes.models import Vote


class Statistics(object):
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end

    timeout = 3600

    @property
    @memoize(timeout=timeout)
    def people_involved(self):
        """
        The (unique) total number of people that donated, fundraised, campaigned, or was a
        task owner or  member.
        """
        donor_ids = Order.objects.filter(
            self.date_filter('confirmed'),
            user_id__isnull=False,
            status__in=(StatusDefinition.PENDING, StatusDefinition.SUCCESS)
        ).order_by(
            'user__id'
        ).distinct('user').values_list('user_id', flat=True)

        fundraiser_owner_ids = Fundraiser.objects.filter(
            self.date_filter('deadline'),
        ).order_by(
            'owner__id'
        ).distinct('owner').values_list('owner_id', flat=True)

        project_owner_ids = Project.objects.filter(
            self.date_filter('created'),
            status__slug__in=(
                'voting', 'voting-done', 'to-be-continued', 'campaign', 'done-complete', 'done-incomplete'
            )
        ).order_by(
            'owner__id'
        ).distinct('owner').values_list('owner_id', flat=True)

        task_member_ids = TaskMember.objects.filter(
            self.date_filter('task__deadline'),
            status__in=('realized', 'accepted', 'applied')
        ).order_by('member__id').distinct(
            'member'
        ).values_list('member_id', flat=True)

        task_owner_ids = Task.objects.filter(
            self.date_filter()
        ).order_by('author__id').distinct(
            'author'
        ).values_list('author_id', flat=True)

        people_count = len(
            set(donor_ids) | set(fundraiser_owner_ids) | set(project_owner_ids) |
            set(task_member_ids) | set(task_owner_ids)
        )

        # Add anonymous donations
        people_count += len(Order.objects.filter(
            self.date_filter('completed'),
            user_id=None,
            status__in=(StatusDefinition.PENDING, StatusDefinition.SUCCESS)
        ))
        # Add donations on behalve of another person
        people_count += len(Order.objects.filter(
            self.date_filter('completed'),
            user__isnull=False,
            donations__name__isnull=False,
            status__in=(StatusDefinition.PENDING, StatusDefinition.SUCCESS)
        ).order_by('donations__name').distinct('donations__name'))

        # Add "plus one"
        people_count += TaskMember.objects.filter(
            self.date_filter('task__deadline'),
            status__in=['accepted', 'realized']
        ).aggregate(
            externals=Sum('externals')
        )['externals'] or 0

        return people_count

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
    def tasks_realized(self):
        """ Total number of realized tasks """
        tasks = Task.objects.filter(
            self.date_filter('deadline'),
            status='realized'
        )
        return len(tasks)

    @property
    @memoize(timeout=timeout)
    def projects_realized(self):
        """ Total number of realized (done-complete and incomplete) projects """
        projects = Project.objects.filter(
            self.date_filter('deadline'),
            status__slug__in=['done-complete', 'done-incomplete', 'voting-done'],
        )
        return len(projects)

    @property
    @memoize(timeout=timeout)
    def projects_online(self):
        """ Total number of projects that have been in campaign mode"""
        return Project.objects.filter(self.date_filter('campaign_started'),
                                      status__slug__in=('voting', 'campaign')).count()

    @property
    @memoize(timeout=timeout)
    def donated_total(self):
        """ Total amount donated to all projects"""
        donations = Donation.objects.filter(
            self.date_filter('order__created'),
            order__status__in=['pending', 'success', 'pledged']
        )
        totals = donations.values('amount_currency').annotate(total=Sum('amount'))
        amounts = [Money(total['total'], total['amount_currency']) for total in totals]
        if totals:
            donated = sum([convert(amount, properties.DEFAULT_CURRENCY) for amount in amounts])
        else:
            donated = Money(0, properties.DEFAULT_CURRENCY)

        return donated

    @property
    @memoize(timeout=timeout)
    def votes_cast(self):
        return len(Vote.objects.filter(self.date_filter()))

    @property
    @memoize(timeout=timeout)
    def time_spent(self):
        """ Total amount of time spent on realized tasks """
        members = TaskMember.objects.filter(
            self.date_filter('task__deadline'),
            status='realized'
        )
        return members.aggregate(total_time_spent=Sum('time_spent'))['total_time_spent']

    @property
    @memoize(timeout=timeout)
    def amount_matched(self):
        """ Total amount matched on realized (done and incomplete) projects """
        totals = Project.objects.filter(
            self.date_filter('campaign_ended')
        ).filter(
            amount_extra__gt=0
        ).values('amount_extra_currency').annotate(total=Sum('amount_extra'))

        amounts = [Money(total['total'], total['amount_extra_currency']) for total in totals]
        if totals:
            return sum([convert(amount, properties.DEFAULT_CURRENCY) for amount in amounts])
        else:
            return Money(0, properties.DEFAULT_CURRENCY)

    @property
    @memoize(timeout=timeout)
    def projects_complete(self):
        """ Total number of projects with the status complete """
        projects = Project.objects.filter(
            self.date_filter('deadline'),
            status__slug='done-complete'
        )
        return len(projects)

    @property
    @memoize(timeout=timeout)
    def task_members(self):
        """ Total number of realized task members """
        members = TaskMember.objects.filter(
            self.date_filter('task__deadline'),
            status='realized'
        )
        return len(members)

    @property
    @memoize(timeout=timeout)
    def participants(self):
        """ Total numbers of participants (members that started a project, or where a realized task member) """
        project_owner_ids = Project.objects.filter(
            self.date_filter('created'),
            status__slug__in=(
                'voting', 'voting-done', 'to-be-continued', 'campaign', 'done-complete', 'done-incomplete'
            )
        ).order_by(
            'owner__id'
        ).distinct('owner').values_list('owner_id', flat=True)

        task_member_ids = TaskMember.objects.filter(
            self.date_filter('task__deadline'),
            status='realized'
        ).order_by('member__id').distinct(
            'member'
        ).values_list('member_id', flat=True)

        return len(set(task_member_ids) | set(project_owner_ids))

    @property
    @memoize(timeout=timeout)
    def pledged_total(self):
        """ Total amount of pledged donations """
        donations = Donation.objects.filter(
            self.date_filter('order__confirmed'),
            order__status='pledged'
        )
        totals = donations.values('amount_currency').annotate(total=Sum('amount'))
        amounts = [Money(total['total'], total['amount_currency']) for total in totals]
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
