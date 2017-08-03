import itertools

import pendulum
from django.db.models import Q, F
from memoize import memoize

from bluebottle.projects.models import Project, ProjectPhaseLog
from bluebottle.tasks.models import Task, TaskMember, TaskStatusLog, TaskMemberStatusLog


class Statistics(object):
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end

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

    def end_date_filter(self, field='created'):
        if self.end:
            filter_args = {'{}__lte'.format(field): self.end}
        else:
            filter_args = {}

        return Q(**filter_args)

    @property
    @memoize(timeout=60 * 60)
    def participants_count(self):
        """ Total numbers of participants (members that started a project, or realized task member,
        or inititated a task)"""
        return len(self.participant_details())

    def participant_details(self):
        """Participants are defined as project initiators of a project (running, done or realised),
        task members (that applied for, got accepted for, or realised a task) or task initiators.
        If a member is one of the three (e.g. a project initiator or a task member or a task initiator),
        they are counted as one participant."""

        # NOTE: Queries just for reference.
        project_owners = Project.objects\
            .filter(self.date_filter('created'),
                    status__slug__in=('voting', 'voting-done', 'campaign', 'done-complete', 'done-incomplete'))\
            .values('owner_id', 'owner__email', 'created')\
            .annotate(id=F('owner_id'))\
            .annotate(email=F('owner__email'))\
            .annotate(action_date=F('created'))

        task_members = TaskMember.objects\
            .filter(self.date_filter('task__created'), status__in=('applied', 'accepted', 'realized'))\
            .values('member_id', 'member__email', 'task__created')\
            .annotate(id=F('member_id'))\
            .annotate(email=F('member__email'))\
            .annotate(action_date=F('task__created'))

        task_authors = Task.objects\
            .filter(self.date_filter('created'), status__in=('open', 'in progress', 'realized', 'full', 'closed'))\
            .values('author_id', 'author__email', 'created')\
            .annotate(id=F('author_id'))\
            .annotate(email=F('author__email'))\
            .annotate(action_date=F('created'))

        participants = dict()

        for member in itertools.chain(task_members, project_owners, task_authors):
            if participants.get(member['id']):
                if member['action_date'] < participants[member['id']]['action_date']:
                    participants[member['id']]['action_date'] = member['action_date']
            else:
                participants[member['id']] = member

        return sorted(participants.values(), key=lambda k: k['action_date'])

    # NOTE: Temporary Stats to count a special case of impact of considering only task members with status realised
    # on the
    # participation number
    @property
    @memoize(timeout=60 * 60)
    def participants_count_with_only_task_members_realized(self):
        """ Total numbers of participants (members that started a project, or realized task member,
        or inititated a task)"""
        return len(self.participant_details_with_only_task_members_realized())

    def participant_details_with_only_task_members_realized(self):
        """Participants are defined as project initiators of a project (running, done or realised),
        task members (that applied for, got accepted for, or realised a task) or task initiators.
        If a member is one of the three (e.g. a project initiator or a task member or a task initiator),
        they are counted as one participant."""

        project_owners = Project.objects\
            .filter(self.date_filter('created'),
                    status__slug__in=('voting', 'voting-done', 'campaign', 'done-complete', 'done-incomplete'))\
            .values('owner_id', 'owner__email', 'created')\
            .annotate(id=F('owner_id'))\
            .annotate(email=F('owner__email'))\
            .annotate(action_date=F('created'))

        task_members = TaskMember.objects\
            .filter(self.date_filter('task__created'), status='realized')\
            .values('member_id', 'member__email', 'task__created')\
            .annotate(id=F('member_id'))\
            .annotate(email=F('member__email'))\
            .annotate(action_date=F('task__created'))

        task_authors = Task.objects\
            .filter(self.date_filter('created'), status__in=('open', 'in progress', 'realized', 'full', 'closed'))\
            .values('author_id', 'author__email', 'created')\
            .annotate(id=F('author_id'))\
            .annotate(email=F('author__email'))\
            .annotate(action_date=F('created'))

        participants = dict()

        for member in itertools.chain(task_members, project_owners, task_authors):
            if participants.get(member['id']):
                if member['action_date'] < participants[member['id']]['action_date']:
                    participants[member['id']]['action_date'] = member['action_date']
            else:
                participants[member['id']] = member

        return sorted(participants.values(), key=lambda k: k['action_date'])

    # Projects Statistics
    @property
    @memoize(timeout=60 * 60)
    def projects_total(self):
        return Project.objects.filter(created__lte=self.end).count()

    @memoize(timeout=60 * 60)
    def get_projects_count_by_theme(self, theme):
        projects_count = Project.objects\
            .filter(created__lte=self.end, theme__slug=theme)\
            .count()

        return projects_count

    @memoize(timeout=60 * 60)
    def get_projects_count_by_last_status(self, statuses):
        logs = ProjectPhaseLog.objects\
            .filter(self.end_date_filter('start'), project__created__lte=self.end)\
            .distinct('project__id')\
            .order_by('-project__id', '-start')

        count = 0
        for log in logs:
            if log.status.slug in statuses:
                count += 1
        return count

    @memoize(timeout=60 * 60)
    def get_projects_status_count_by_location_group(self, location_group, statuses):
        logs = ProjectPhaseLog.objects\
            .filter(self.end_date_filter('start'),
                    project__location__group__name=location_group,
                    project__created__lte=self.end)\
            .distinct('project__id')\
            .order_by('-project__id', '-start')

        count = 0
        for log in logs:
            if log.status.slug in statuses:
                count += 1
        return count

    @memoize(timeout=60 * 60)
    def get_projects_status_count_by_theme(self, theme, statuses):
        logs = ProjectPhaseLog.objects\
            .filter(self.end_date_filter('start'),
                    project__theme__slug=theme,
                    project__created__lte=self.end)\
            .distinct('project__id')\
            .order_by('-project__id', '-start')

        count = 0
        for log in logs:
            if log.status.slug in statuses:
                count += 1
        return count

    @memoize(timeout=60 * 60)
    def get_projects_by_location_group(self, location_group):
        logs = ProjectPhaseLog.objects\
            .filter(self.end_date_filter('start'), project__location__group__name=location_group)\
            .distinct('project__id')\
            .order_by('-project__id', '-start')
        return logs

    @property
    @memoize(timeout=60 * 60)
    def projects_successful(self):
        """ Total number of successful (done-complete, incomplete and voting done) projects """
        return self.get_projects_count_by_last_status(['done-complete', 'done-incomplete', 'voting-done'])

    @property
    @memoize(timeout=60 * 60)
    def projects_running(self):
        """ Total number of running (voting, campaign) projects """
        return self.get_projects_count_by_last_status(['voting', 'campaign'])

    @property
    @memoize(timeout=300)
    def projects_complete(self):
        """ Total number of complete (done-complete, voting-done) projects"""
        return self.get_projects_count_by_last_status(['done-complete', 'voting-done'])

    @property
    @memoize(timeout=60 * 60)
    def projects_online(self):
        """ Total number of projects that have been in campaign mode"""
        return Project.objects.filter(self.date_filter('campaign_started'),
                                      status__slug__in=('voting', 'campaign')).count()

    # Tasks Statistics
    @property
    @memoize(timeout=60 * 60)
    def tasks_total(self):
        return Task.objects.filter(created__lte=self.end).count()

    @memoize(timeout=60 * 60)
    def get_tasks_count_by_last_status(self, statuses):
        logs = TaskStatusLog.objects\
            .filter(self.end_date_filter('start'), task__created__lte=self.end)\
            .distinct('task__id')\
            .order_by('-task__id', '-start')

        count = 0
        for log in logs:
            if log.status in statuses:
                count += 1
        return count

    @memoize(timeout=60 * 60)
    def get_tasks_status_count_by_location_group(self, location_group, statuses):
        logs = TaskStatusLog.objects\
            .filter(self.end_date_filter('start'),
                    task__project__location__group__name=location_group,
                    task__created__lte=self.end)\
            .distinct('task__id')\
            .order_by('-task__id', '-start')

        count = 0
        for log in logs:
            if log.status in statuses:
                count += 1
        return count

    @memoize(timeout=60 * 60)
    def get_tasks_status_count_by_theme(self, theme, statuses):
        logs = TaskStatusLog.objects\
            .filter(self.end_date_filter('start'),
                    task__project__theme__slug=theme,
                    task__created__lte=self.end)\
            .distinct('task__id')\
            .order_by('-task__id', '-start')

        count = 0
        for log in logs:
            if log.status in statuses:
                count += 1
        return count

    # Task Member Statistics
    @property
    @memoize(timeout=60 * 60)
    def task_members_total(self):
        return TaskMember.objects.filter(created__lte=self.end).count()

    @memoize(timeout=60 * 60)
    def get_task_members_count_by_last_status(self, statuses):
        logs = TaskMemberStatusLog.objects\
            .filter(self.end_date_filter('start'), task_member__created__lte=self.end)\
            .distinct('task_member__id')\
            .order_by('-task_member__id', '-start')

        count = 0
        for log in logs:
            if log.status in statuses:
                count += 1
        return count

    @property
    @memoize(timeout=60 * 60)
    def task_members(self):
        """ Total number of realized task members """
        logs = TaskMemberStatusLog.objects \
            .filter(self.end_date_filter('start'), task_member__task__created__lte=self.end) \
            .distinct('task_member__id') \
            .order_by('-task_member__id', '-start')

        count = 0
        for log in logs:
            if log.status == 'realized':
                count += 1
        return count

    @property
    @memoize(timeout=60 * 60)
    def unconfirmed_task_members(self):
        """ Total number of unconfirmed task members """
        now = pendulum.now()
        if self.end <= now.subtract(days=10):
            logs = TaskMemberStatusLog.objects \
                .filter(self.end_date_filter('start'), task_member__task__deadline__lte=self.end.subtract(days=10)) \
                .distinct('task_member__id') \
                .order_by('-task_member__id', '-start')
        else:
            logs = TaskMemberStatusLog.objects \
                .filter(start__lte=now, task_member__task__deadline__lte=now.subtract(days=10)) \
                .distinct('task_member__id') \
                .order_by('-task_member__id', '-start')

        count = 0
        for log in logs:
            if log.status == 'accepted':
                count += 1
        return count

    @property
    @memoize(timeout=60 * 60)
    def unconfirmed_task_members_task_count(self):
        """ Total number of task belonging to unconfirmed task members """
        now = pendulum.now()
        if self.end <= now.subtract(days=10):
            logs = TaskMemberStatusLog.objects \
                .filter(self.end_date_filter('start'), task_member__task__deadline__lte=self.end.subtract(days=10)) \
                .distinct('task_member__id') \
                .order_by('-task_member__id', '-start')
        else:
            logs = TaskMemberStatusLog.objects \
                .filter(start__lte=now, task_member__task__deadline__lte=now.subtract(days=10)) \
                .distinct('task_member__id') \
                .order_by('-task_member__id', '-start')

        task_ids = set()

        for log in logs:
            if log.status == 'accepted':
                task_ids.add(log.task_member.task.id)

        return len(task_ids)

    @property
    @memoize(timeout=60 * 60)
    def time_spent(self):
        """ Total amount of time spent on realized tasks """
        logs = TaskMemberStatusLog.objects\
            .filter(self.end_date_filter('start'), task_member__task__created__lte=self.end) \
            .distinct('task_member__id') \
            .order_by('-task_member__id', '-start') \

        count = 0
        for log in logs:
            if log.status == 'realized':
                count += log.task_member.time_spent

        return count

    def __repr__(self):
        start = self.start.strftime('%s') if self.start else 'none'
        end = self.end.strftime('%s') if self.end else 'none'
        return 'Statistics({},{})'.format(start, end)
