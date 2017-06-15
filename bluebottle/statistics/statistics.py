import itertools

from django.db.models import Q, F
from django.db.models.aggregates import Sum
from memoize import memoize
from moneyed.classes import Money

from bluebottle.clients import properties
from bluebottle.donations.models import Donation
from bluebottle.fundraisers.models import Fundraiser
from bluebottle.projects.models import Project, ProjectPhaseLog
from bluebottle.tasks.models import Task, TaskMember, TaskStatusLog, TaskMemberStatusLog
from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.utils import StatusDefinition
from bluebottle.votes.models import Vote
from bluebottle.orders.models import Order


class Statistics(object):
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end

    @property
    @memoize(timeout=60 * 60)
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
    @memoize(timeout=60 * 60)
    def tasks_realized(self):
        """ Total number of realized tasks """
        """
        Reference:
        SELECT
            DISTINCT ON ("tasks_taskstatuslog"."task_id") "tasks_taskstatuslog"."id",
                         "tasks_taskstatuslog"."task_id", "tasks_taskstatuslog"."status",
                         "tasks_taskstatuslog"."start"
            FROM "tasks_taskstatuslog"
            WHERE "tasks_taskstatuslog"."start" BETWEEN '2017-01-01 00:00:00' AND '2017-12-31 23:59:59'
            ORDER BY "tasks_taskstatuslog"."task_id" DESC, "tasks_taskstatuslog"."start" DESC
        """
        logs = TaskStatusLog.objects\
            .filter(self.date_filter('start'))\
            .distinct('task__id')\
            .order_by('-task__id', '-start')

        # TODO: Refactor to use django filters for sub-queries
        count = 0
        for log in logs:
            if log.status == 'realized':
                count += 1
        return count

    @property
    @memoize(timeout=60 * 60)
    def projects_realized(self):
        """ Total number of realized (done-complete and incomplete) projects """
        """
        Reference:
        SELECT DISTINCT ON ("projects_projectphaselog"."project_id") "projects_projectphaselog"."id",
        "projects_projectphaselog"."project_id",
        "projects_projectphaselog"."status_id", "projects_projectphaselog"."start"
        FROM "projects_projectphaselog"
        WHERE "projects_projectphaselog"."start" BETWEEN '2017-01-01 00:00:00' AND '2017-12-31 23:59:59'
        ORDER BY "projects_projectphaselog"."project_id" DESC, "projects_projectphaselog"."start" DESC

        This will get the last status log entry for all project phase logs
        """

        phase_logs = ProjectPhaseLog.objects\
            .filter(self.date_filter('start'))\
            .distinct('project__id')\
            .order_by('-project__id', '-start')

        # TODO: Refactor to use django filters for sub-queries
        count = 0
        for log in phase_logs:
            if log.status.slug in ['done-complete', 'done-incomplete']:
                count += 1
        return count

    @property
    @memoize(timeout=60 * 60)
    def projects_online(self):
        """ Total number of projects that have been in campaign mode"""
        return Project.objects.filter(self.date_filter('campaign_started'),
                                      status__slug__in=('voting', 'campaign')).count()

    @property
    @memoize(timeout=60 * 60)
    def donated_total(self):
        """ Total amount donated to all projects"""
        donations = Donation.objects.filter(
            self.date_filter('order__confirmed'),
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
    @memoize(timeout=60 * 60)
    def votes_cast(self):
        return len(Vote.objects.filter(self.date_filter()))

    @property
    @memoize(timeout=60 * 60)
    def time_spent(self):
        """ Total amount of time spent on realized tasks """
        logs = TaskMemberStatusLog.objects\
            .filter(self.date_filter('start')) \
            .distinct('task_member__id') \
            .order_by('-task_member__id', '-start') \

        # TODO: Refactor to use django filters for sub-queries
        count = 0
        for log in logs:
            if log.status == 'realized':
                count += log.task_member.time_spent

        return count

    @property
    @memoize(timeout=60 * 60)
    def amount_matched(self):
        """ Total amount matched on realized (done and incomplete) projects """
        totals = Project.objects.values('amount_extra_currency').annotate(total=Sum('amount_extra'))

        amounts = [Money(total['total'], total['amount_extra_currency']) for total in totals]
        if totals:
            return sum([convert(amount, properties.DEFAULT_CURRENCY) for amount in amounts])
        else:
            return Money(0, properties.DEFAULT_CURRENCY)

    @property
    @memoize(timeout=300)
    def projects_complete(self):
        """ Total number of projects with the status complete """
        logs = ProjectPhaseLog.objects\
            .filter(self.date_filter('start'))\
            .distinct('project__id')\
            .order_by('-project__id', '-start')

        # TODO: Refactor to use django filters for sub-queries
        count = 0
        for log in logs:
            if log.status.slug == 'done-complete':
                count += 1
        return count

    @property
    @memoize(timeout=300)
    def task_members(self):
        """ Total number of realized task members """
        logs = TaskMemberStatusLog.objects \
            .filter(self.date_filter('start')) \
            .distinct('task_member__id') \
            .order_by('-task_member__id', '-start')

        # TODO: Refactor to use django filters for sub-queries
        count = 0
        for log in logs:
            if log.status == 'realized':
                count += 1
        return count

    def participant_details(self):
        """Participants are defined as project initiators of a project (running, done or realised),
        task members (that applied for, got accepted for, or realised a task) or task initiators.
        If a member is one of the three (e.g. a project initiator or a task member or a task initiator),
        they are counted as one participant."""

        project_owners = Project.objects\
            .filter(self.date_filter('created'),
                    status__slug__in=('voting', 'voting-done', 'campaign', 'done-complete', 'done-incomplete'))\
            .values('owner_id', 'owner__email', 'created')\
            .annotate(id=F('owner_id'))\
            .annotate(email=F('owner__email'))

        task_members = TaskMember.objects\
            .filter(self.date_filter('created'), status='applied')\
            .values('member_id', 'member__email', 'created')\
            .annotate(id=F('member_id'))\
            .annotate(email=F('member__email'))

        task_authors = Task.objects\
            .filter(self.date_filter('created'), status='realized')\
            .values('author_id', 'author__email', 'created')\
            .annotate(id=F('author_id'))\
            .annotate(email=F('author__email'))

        participants = dict()

        for member in itertools.chain(task_members, project_owners, task_authors):
            if participants.get(member['id']):
                if member['created'] < participants[member['id']]['created']:
                    participants[member['id']]['created'] = member['created']
            else:
                participants[member['id']] = member

        return sorted(participants.values(), key=lambda k: k['created'])

    @property
    @memoize(timeout=300)
    def participants(self):
        """ Total numbers of participants (members that started a project, or realized task member,
        or inititated a task)"""
        return len(self.participant_details())

    @property
    @memoize(timeout=300)
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

    def __repr__(self):
        start = self.start.strftime('%s') if self.start else 'none'
        end = self.end.strftime('%s') if self.end else 'none'
        return 'Statistics({},{})'.format(start, end)
