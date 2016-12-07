from django.db.models import Q
from django.db.models.aggregates import Sum

from memoize import memoize

from moneyed.classes import Money

from bluebottle.clients import properties
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.utils import StatusDefinition

from bluebottle.donations.models import Donation
from bluebottle.fundraisers.models import Fundraiser
from bluebottle.orders.models import Order
from bluebottle.projects.models import Project
from bluebottle.tasks.models import Task, TaskMember
from bluebottle.votes.models import Vote


class Statistics(object):
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end

    @property
    @memoize(timeout=300)
    def people_involved(self):
        """
        Count all people who donated, fundraised, campaigned or was
        a task member. People should be unique across all categories.
        """
        donator_ids = Order.objects.filter(
            self.date_filter('completed'),
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
            set(donator_ids) | set(fundraiser_owner_ids) | set(project_owner_ids) |
            set(task_member_ids) | set(task_owner_ids)
        )

        # Add anonymous donations
        people_count += len(Order.objects.filter(
            self.date_filter('completed'),
            user_id=None,
            status__in=(StatusDefinition.PENDING, StatusDefinition.SUCCESS)
        ))

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
    @memoize(timeout=300)
    def tasks_realized(self):
        """ Count all realized tasks (status == realized) """
        return len(Task.objects.filter(self.date_filter('deadline'), status='realized'))

    @property
    @memoize(timeout=300)
    def projects_realized(self):
        """ Count all realized projects (status in done-complete
            or done-incomplete) """
        return len(Project.objects.filter(
            self.date_filter('campaign_ended'), status__slug__in=('done-complete', 'done-incomplete',)
        ))

    @property
    @memoize(timeout=300)
    def projects_online(self):
        """ Count all running projects (status == campaign) """
        return len(
            Project.objects.filter(self.date_filter('campaign_started'), status__slug__in=('voting', 'campaign'))
        )

    @property
    @memoize(timeout=300)
    def donated_total(self):
        """ Add all donation amounts for all donations ever """
        donations = Donation.objects.filter(
            self.date_filter('completed'),
            order__status__in=(StatusDefinition.PENDING, StatusDefinition.SUCCESS)
        )
        totals = donations.values('amount_currency').annotate(total=Sum('amount'))
        amounts = [Money(total['total'], total['amount_currency']) for total in totals]

        if totals:
            donated = int(sum([convert(amount, properties.DEFAULT_CURRENCY) for amount in amounts]).amount)
        else:
            donated = 0

        return donated

    @property
    @memoize(timeout=300)
    def votes_cast(self):
        return len(Vote.objects.filter(self.date_filter()))

    @property
    @memoize(timeout=300)
    def time_spent(self):
        return TaskMember.objects.filter(
            self.date_filter('task__deadline'),
            status='realized'
        ).aggregate(time_spent=Sum('time_spent'))['time_spent']
        return len(Vote.objects.filter(self.date_filter()))

    def __repr__(self):
        return 'Statistics'
