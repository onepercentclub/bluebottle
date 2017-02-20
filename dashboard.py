from moneyed import Money
from datetime import timedelta
from datetime import datetime

from django.db.models.aggregates import Sum
from django.db.models import F, Count
from django.utils.timezone import now

from django.core.urlresolvers import reverse_lazy

from admin_tools.dashboard.models import DashboardModule

from bluebottle.tasks.models import Task, TaskMember

from admin_tools.dashboard import modules
from django.utils.translation import ugettext_lazy as _

from fluent_dashboard.dashboard import FluentIndexDashboard
from bluebottle.projects.dashboard import SubmittedPlans, EndedProjects, StartedCampaigns
from bluebottle.bb_tasks.dashboard import RecentTasks

from bluebottle.clients import properties
from bluebottle.suggestions.models import Suggestion
from bluebottle.members.models import Member
from bluebottle.projects.models import Project
from bluebottle.donations.models import Donation
from bluebottle.utils.exchange_rates import convert


class Metrics():
    task_member_allowed_statuses = ['accepted', 'realized']

    def __init__(self, *args, **kwargs):
        self.today = datetime.today()
        self.this_year = datetime.now().year
        self.next_year = self.this_year + 1
        self.last_year = self.this_year - 1

    def calculate_partner_metrics(self):
        """
        Calculate the metrics for partners. 1) Calculate number of
        partners, 2) calculate time spent for each partner
        """
        partners = {}
        partners[self.this_year] = 0
        partner_hours = {}
        partner_hours[self.this_year] = 0

        task_members = TaskMember.objects.filter(task__deadline__year=self.this_year,
                                                 status__in=self.task_member_allowed_statuses)

        for task_member in task_members:
            partners[self.this_year] += task_member.externals
            partner_hours[self.this_year] += (task_member.externals * task_member.time_spent)
        return partners, partner_hours

    def calculate_taskmember_metrics(self):
        """ Calculate the metrics for task members."""
        taskmembers = {}
        taskmembers[self.this_year] = 0
        taskmember_hours = 0

        task_members = TaskMember.objects.filter(status__in=self.task_member_allowed_statuses)

        taskmember_hours = TaskMember.objects.filter(status='realized').aggregate(sum=Sum('time_spent'))['sum']
        return task_members, taskmember_hours

    def calculate_suggestion_metrics(self):
        """
        Calculate suggestion metrics. Expired content is not
        excluded in totals!
        """
        suggestion_metrics = {}

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

    def calculate_supporters(self):
        """ Return the number of unique people who did a successfull donation """
        return Donation.objects.filter(order__status__in=['success', 'pending']).\
            order_by('order__user').distinct('order__user').count()

    def calculate_total_raised(self):
        """ Calculate the total amount raised by projects """
        totals = Donation.objects.filter(
            order__status__in=['success', 'pending']
        ).values(
            'amount_currency'
        ).annotate(total=Sum('amount')).order_by('-amount')
        amounts = [Money(total['total'], total['amount_currency']) for total in totals]
        amounts = [convert(amount, properties.DEFAULT_CURRENCY) for amount in amounts]
        return sum(amounts) or Money(0, properties.DEFAULT_CURRENCY)

    def calculate_initiators(self):
        """ Return number of unique users that started a project, which now has a valid status """
        project_statuses = [6, 8, 9]  # Campaign, Done-Complete, Done-Incomplete
        return Project.objects.filter(status__sequence__in=project_statuses).\
            order_by('owner').distinct('owner').count()

    def calculate_realized_tasks_unconfirmed_taskmembers(self):
        """ Return unique number of realzied tasks where there no task members with status realized """
        return Task.objects.filter(status='realized').\
            exclude(members__status__in=['realized', 'rejected', 'stopped']).distinct().count()

    def calculate_tasks_realized_taskmembers(self):
        """ Return number of unique tasks that have a taskmember with status realized """
        return TaskMember.objects.filter(status='realized').\
            aggregate(Count('task', distinct=True))['task__count']


class CustomIndexDashboard(FluentIndexDashboard):
    """
    Custom Dashboard for Bluebottle.
    """
    columns = 3

    def init_with_context(self, context):
        self.children.append(SubmittedPlans())
        self.children.append(StartedCampaigns())
        self.children.append(EndedProjects())
        self.children.append(RecentTasks())

        if context['request'].user.has_perm('sites.export'):
            self.children.append(modules.LinkList(
                _('Export Metrics'),
                children=[
                    {
                        'title': _('Export metrics'),
                        'url': reverse_lazy('exportdb_export'),
                    }
                ]
            ))


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
