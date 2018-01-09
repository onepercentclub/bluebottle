from datetime import datetime
from datetime import timedelta

import pendulum
from admin_tools.dashboard.models import DashboardModule
from admin_tools.dashboard.modules import LinkList
from django.core.urlresolvers import reverse_lazy, reverse
from django.db.models import F, Count
from django.db.models.aggregates import Sum
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from fluent_dashboard.dashboard import FluentIndexDashboard
from moneyed import Money

from bluebottle.bb_tasks.dashboard import RecentTasks
from bluebottle.clients import properties
from bluebottle.donations.models import Donation
from bluebottle.members.models import Member
from bluebottle.projects.dashboard import Analytics
from bluebottle.projects.dashboard import SubmittedPlans, EndedProjects, StartedCampaigns
from bluebottle.projects.models import Project
from bluebottle.statistics.participation import Statistics
from bluebottle.suggestions.models import Suggestion
from bluebottle.tasks.models import Task, TaskMember
from bluebottle.utils.exchange_rates import convert


class Metrics:
    task_member_allowed_statuses = ['accepted', 'realized']

    def __init__(self):
        self.today = datetime.today()
        self.this_year = datetime.now().year
        self.next_year = self.this_year + 1
        self.last_year = self.this_year - 1

    def calculate_partner_metrics(self):
        """
        Calculate the metrics for partners. 1) Calculate number of
        partners, 2) calculate time spent for each partner
        """
        partners = dict()
        partners[self.this_year] = 0
        partner_hours = dict()
        partner_hours[self.this_year] = 0

        task_members = TaskMember.objects.filter(task__deadline__year=self.this_year,
                                                 status__in=self.task_member_allowed_statuses)

        for task_member in task_members:
            partners[self.this_year] += task_member.externals
            partner_hours[self.this_year] += (task_member.externals * task_member.time_spent)
        return partners, partner_hours

    def calculate_taskmember_metrics(self):
        """ Calculate the metrics for task members."""
        taskmembers = dict()
        taskmembers[self.this_year] = 0

        task_members = TaskMember.objects.filter(status__in=self.task_member_allowed_statuses)

        taskmember_hours = TaskMember.objects.filter(status='realized').aggregate(sum=Sum('time_spent'))['sum']
        return task_members, taskmember_hours

    def calculate_suggestion_metrics(self):
        """
        Calculate suggestion metrics. Expired content is not
        excluded in totals!
        """
        suggestion_metrics = dict()

        # the explicit project_isnull check is a bit redundant - a submitted
        # suggestion always (?) has a project.
        suggestion_metrics['expired'] = Suggestion.objects.filter(deadline__lt=self.today).count()

        for status in ('unconfirmed',
                       'draft',
                       'accepted',
                       'rejected',
                       'submitted',
                       'in_progress'):
            suggestion_metrics[status] = Suggestion.objects.filter(status=status).count()

        return suggestion_metrics

    @staticmethod
    def calculate_supporters():
        """ Return the number of unique people who did a successfull donation """
        return Donation.objects.filter(order__status__in=['success', 'pending']).\
            order_by('order__user').distinct('order__user').count()

    @staticmethod
    def calculate_total_raised():
        """ Calculate the total amount raised by projects """
        totals = Donation.objects.filter(
            order__status__in=['success', 'pending']
        ).values(
            'amount_currency'
        ).annotate(total=Sum('amount')).order_by('-amount')
        amounts = [Money(total['total'], total['amount_currency']) for total in totals]
        amounts = [convert(amount, properties.DEFAULT_CURRENCY) for amount in amounts]
        return sum(amounts) or Money(0, properties.DEFAULT_CURRENCY)

    @staticmethod
    def calculate_initiators():
        """ Return number of unique users that started a project, which now has a valid status """
        project_statuses = [6, 8, 9]  # Campaign, Done-Complete, Done-Incomplete
        return Project.objects.filter(status__sequence__in=project_statuses).\
            order_by('owner').distinct('owner').count()

    @staticmethod
    def calculate_realized_tasks_unconfirmed_taskmembers():
        """ Return unique number of realzied tasks where there no task members with status realized """
        return Task.objects.filter(status='realized').\
            exclude(members__status__in=['realized', 'rejected', 'stopped']).distinct().count()

    @staticmethod
    def calculate_tasks_realized_taskmembers():
        """ Return number of unique tasks that have a taskmember with status realized """
        return TaskMember.objects.filter(status='realized').\
            aggregate(Count('task', distinct=True))['task__count']

    def calculate_participants(self):
        participants = {}
        years = [self.last_year, self.this_year, self.next_year]
        allowed_statuses = ['applied', 'accepted', 'realized']
        project_statuses = [6, 8, 9]  # Campaign, Done-Complete, Done-Incomplete
        for year in years:
            task_members = TaskMember.objects.\
                filter(task__deadline__year=year, status__in=allowed_statuses).\
                order_by('member').distinct('member')
            project_owners = Project.objects.values('owner').\
                filter(created__year=year, status__sequence__in=project_statuses).\
                order_by('owner').distinct('owner')
            doubles = task_members.filter(member__in=project_owners)
            participants[year] = task_members.count() + project_owners.count() - doubles.count()
        return participants


class ParticipationMetricsModule(DashboardModule):
    title = _('ParticipationMetrics')
    template = 'admin_tools/dashboard/metrics_module.html'

    def __init__(self, **kwargs):
        self.children = []

        today = pendulum.now()
        year_start_date = pendulum.create(today.year, 1, 1, 0, 0, 0)
        year_end_date = pendulum.create(today.year, 12, 31, 23, 59, 59)
        time_period = pendulum.period(year_start_date, year_end_date)

        for week_nr, period in enumerate(time_period.range('weeks'), start=1):

            # Curtail the last week of the year to end with the end of the year
            # E.g. The end day of the last week of the year could lie in the next year, in this case we just
            # use the last day of the year as the end day of the week
            end_of_week = period.end_of('week')
            statistics_end_date = end_of_week if end_of_week < year_end_date else year_end_date

            if statistics_end_date <= today.add(weeks=1):
                statistics = Statistics(start=year_start_date, end=statistics_end_date)
                self.children.insert(0, {
                    'title': _('Week Nr. {}'.format(week_nr)),
                    'value': statistics.participants_count
                })
        self.children.insert(0, {
            'title': _('Request Complete Participation Metrics'),
            'url': reverse('participation-metrics')
        })
        super(ParticipationMetricsModule, self).__init__(**kwargs)


class MetricsModule(DashboardModule):
    """
    Metrics module for the django admin tools dashboard.
    Since this is only meant to be here for a short while so lot's of simple hacks.
    """
    # FIXME: Replace with a decent metrics solution.
    title = _('Metrics')
    template = 'admin_tools/dashboard/metrics_module.html'

    def __init__(self, **kwargs):
        member_url = '/admin/members/member/'
        project_url = '/admin/projects/project/'
        task_url = '/admin/tasks/task/'
        task_member_url = '/admin/tasks/taskmember/'
        suggestion_url = '/admin/suggestions/suggestion/'

        week_ago = now() + timedelta(days=-7)
        total_updated_count = Member.objects.filter(updated__gt=F('date_joined') + timedelta(minutes=1)).count()

        this_year = datetime.now().year
        last_year = this_year - 1

        allowed_statuses = ['applied', 'accepted', 'realized']

        metrics = Metrics()
        participants = metrics.calculate_participants()
        partners, partner_hours = metrics.calculate_partner_metrics()
        suggestion_metrics = metrics.calculate_suggestion_metrics()
        __, taskmember_hours = metrics.calculate_taskmember_metrics()
        supporters = metrics.calculate_supporters()
        total_raised = metrics.calculate_total_raised()
        initiators = metrics.calculate_initiators()
        realized_unconfirmed_tms = metrics.calculate_realized_tasks_unconfirmed_taskmembers()
        tasks_realized_tms = metrics.calculate_tasks_realized_taskmembers()

        self.children = (
            {'title': _('Platform Members'),
             'value': Member.objects.count(),
             'url': member_url},
            {'title': _('Members - new (last week)'),
             'value': Member.objects.filter(date_joined__gte=week_ago).count(),
             'url': member_url},
            {'title': _('Members - updated (last week)'),
             'value': Member.objects.filter(updated__gte=week_ago).count(),
             'url': member_url},
            {'title': _('Members - updated (total)'),
             'value': total_updated_count,
             'url': member_url},

            {'title': '---'},

            {'title': _('Projects'),
             'value': Project.objects.count(),
             'url': project_url},
            {'title': _('Projects - new'),
             'value': Project.objects.filter(status__slug='plan-new').count(),
             'url': project_url + '?status__exact=1'},
            {'title': _('Projects - submitted'),
             'value': Project.objects.filter(status__slug='plan-submitted').count(),
             'url': project_url + '?status__exact=2'},
            {'title': _('Projects - needs work'),
             'value': Project.objects.filter(status__slug='plan-needs-work').count(),
             'url': project_url + '?status__exact=3'},
            {'title': _('Voting - Running'),
             'value': Project.objects.filter(status__slug='voting').count(),
             'url': project_url + '?status__exact=11'},
            {'title': _('Voting - Done'),
             'value': Project.objects.filter(status__slug='voting-done').count(),
             'url': project_url + '?status__exact=12'},
            {'title': _('Projects - running'),
             'value': Project.objects.filter(status__slug='campaign').count(),
             'url': project_url + '?status__exact=4'},
            {'title': _('Projects - realised'),
             'value': Project.objects.filter(status__slug='done-complete').count(),
             'url': project_url + '?status__exact=5'},
            {'title': _('Projects - expired'),
             'value': Project.objects.filter(status__slug='done-incomplete').count(),
             'url': project_url + '?status__exact=5'},
            {'title': _('Projects - cancelled'),
             'value': Project.objects.filter(status__slug='closed').count(),
             'url': project_url + '?status__exact=6'},
            {'title': _('Project Initiators'),
             'value': initiators},
            {'title': _('Supporters'),
             'value': supporters},
            {'title': _('Total amount raised'),
             'value': total_raised},

            {'title': '---'},

            {'title': _('Tasks'),
             'value': Task.objects.count(),
             'url': task_url},
            {'title': _('Tasks - open'),
             'value': Task.objects.filter(status='open').count(),
             'url': task_url + '?status__exact=open'},
            {'title': _('Tasks - in progress'),
             'value': Task.objects.filter(status='in progress').count(),
             'url': task_url + '?status__exact=in+progress'},
            {'title': _('Tasks - realised'),
             'value': Task.objects.filter(status='realized').count(),
             'url': task_url + '?status__exact=realized'},
            {'title': _('Tasks - closed'),
             'value': Task.objects.filter(status='closed').count(),
             'url': task_url + '?status__exact=closed'},

            {'title': '---'},
            {'title': _('Task Members'),
             'value': TaskMember.objects.all().count(),
             'url': task_member_url},

            {'title': _('Task members - applied'),
             'value': TaskMember.objects.filter(status='applied').count(),
             'url': task_member_url + '?status__exact=applied'},
            {'title': _('Task members - accepted'),
             'value': TaskMember.objects.filter(status='accepted').count(),
             'url': task_member_url + '?status__exact=accepted'},
            {'title': _('Task members - rejected'),
             'value': TaskMember.objects.filter(status='rejected').count(),
             'url': task_member_url + '?status__exact=rejected'},
            {'title': _('Task members - withdrew'),
             'value': TaskMember.objects.filter(status='stopped').count(),
             'url': task_member_url + '?status__exact=stopped'},
            {'title': _('Task members - realised'),
             'value': TaskMember.objects.filter(status='realized').count(),
             'url': task_member_url + '?status__exact=realized'},

            {'title': '---'},

            {'title': _('Task members (realised) - hours spent'),
             'value': taskmember_hours,
             'url': task_member_url + '?status__exact=realized'},
            {'title': _('Task members (unique)'),
             'value': TaskMember.objects.filter(status__in=allowed_statuses).distinct('member').count(),
             'url': task_member_url},
            {'title': _('Task members {} (unique)').format(last_year),
             'value': TaskMember.objects.
                filter(task__deadline__year=last_year, status__in=allowed_statuses).
                distinct('member').count(),
             'url': task_member_url + '?task__deadline__year={}'.format(last_year)},
            {'title': _('Task members {} (unique)').format(this_year),
             'value': TaskMember.objects.
                filter(task__deadline__year=this_year, status__in=allowed_statuses).
                distinct('member').count(),
             'url': task_member_url + '?task__deadline__year={}'.format(this_year)},

            {'title': _('Realised tasks with unconfirmed task members'),
             'value': realized_unconfirmed_tms,
             'url': task_url + '?status__exact=realized'},
            {'title': _('Tasks with a realised task member'),
             'value': tasks_realized_tms,
             'url': task_url + '?status__exact=realized'},

            {'title': '---'},

            {'title': _('Participants {0}').format(last_year),
             'value': participants[last_year]},
            {'title': _('Participants {0}').format(this_year),
             'value': participants[this_year]},
            {'title': _('Partners {0}').format(metrics.this_year),
             'value': partners[metrics.this_year]},
            {'title': _('Partners {0} hours spent ').format(metrics.this_year),
             'value': partner_hours[metrics.this_year]},

            {'title': '---'},
            {'title': _('Suggestions'),
             'value': Suggestion.objects.count(),
             'url': suggestion_url},
            {'title': _('Suggestions - unconfirmed'),
             'value': suggestion_metrics.get('unconfirmed', 0),
             'url': suggestion_url + "?status__exact=unconfirmed"},
            {'title': _('Suggestions - draft'),
             'value': suggestion_metrics.get('draft', 0),
             'url': suggestion_url + "?status__exact=draft"},
            {'title': _('Suggestions - accepted'),
             'value': suggestion_metrics.get('accepted', 0),
             'url': suggestion_url + "?status__exact=accepted"},
            {'title': _('Suggestions - submitted'),
             'value': suggestion_metrics.get('submitted', 0),
             'url': suggestion_url + "?status__exact=submitted"},
            {'title': _('Suggestions - in progress'),
             'value': suggestion_metrics.get('in_progress', 0),
             'url': suggestion_url + "?status__exact=in_progress"},
            {'title': _('Suggestions - rejected'),
             'value': suggestion_metrics.get('rejected', 0),
             'url': suggestion_url + "?status__exact=rejected"},
            {'title': _('Suggestions - expired'),
             'value': suggestion_metrics.get('expired', 0),
             'url': suggestion_url + "?isexpired=expired"},
        )
        super(MetricsModule, self).__init__(**kwargs)


class WallpostModule(DashboardModule):
    """
    Metrics module for the django admin tools dashboard.
    Since this is only meant to be here for a short while so lot's of simple hacks.
    """
    # FIXME: Replace with a decent metrics solution.
    title = _('Wallposts')
    template = 'admin_tools/dashboard/metrics_module.html'

    def __init__(self, **kwargs):
        mediawallpost_url = '/admin/wallposts/mediawallpost/'
        wallpost_url = '/admin/wallposts/wallpost/'

        self.children = (
            {'title': _('Media wallposts'), 'url': mediawallpost_url},
            {'title': _('All wallposts'), 'url': wallpost_url},

        )
        super(WallpostModule, self).__init__(**kwargs)


class CustomIndexDashboard(FluentIndexDashboard):
    """
    Custom Dashboard for Bluebottle.
    """
    columns = 3

    def init_with_context(self, context):
        self.children.append(Analytics())
        self.children.append(SubmittedPlans())
        self.children.append(StartedCampaigns())
        self.children.append(EndedProjects())
        self.children.append(RecentTasks())
        if context['request'].user.has_perm('sites.export'):
            self.children.append(LinkList(
                _('Export Metrics'),
                children=[
                    {
                        'title': _('Export metrics'),
                        'url': reverse_lazy('exportdb_export'),
                    },
                    {
                        'title': _('Download report'),
                        'url': reverse_lazy('report-export'),
                    }
                ]
            ))
        if properties.ANALYTICS_BACKOFFICE_ENABLED:
            self.children.append(MetricsModule(title=_("Metrics"),))
        if properties.PARTICIPATION_BACKOFFICE_ENABLED:
            self.children.append(ParticipationMetricsModule(title=_("Participation Metrics"), ))
