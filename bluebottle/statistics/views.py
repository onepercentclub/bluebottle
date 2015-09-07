import itertools

from rest_framework import generics

from django.db import connection
from django.db.models.aggregates import Sum
from django.core.cache import cache

from bluebottle.utils.utils import StatusDefinition

from .serializers import StatisticSerializer


class Statistics(object):
    def _get_cached(self, key):
        tenant_name = connection.tenant.client_name
        tenant_key = '-'.join([tenant_name, key])

        return cache.get(tenant_key)

    def _set_cached(self, key, value, timeout=300):
        tenant_name = connection.tenant.client_name
        tenant_key = '-'.join([tenant_name, key])

        return cache.set(tenant_key, value, timeout)

    def clear_cached(self):
        tenant_name = connection.tenant.client_name

        for key in ['people-involved-total', 'projects-realized-total',
                    'projects-online-total', 'donations-total',
                    'tasks-realized-total']:
            tenant_key = '-'.join([tenant_name, key])
            cache.set(tenant_key, None, 0)

    @property
    def people_involved(self):
        from bluebottle.tasks.models import TaskMember, Task
        from bluebottle.orders.models import Order
        from bluebottle.projects.models import Project
        from bluebottle.fundraisers.models import Fundraiser

        """
        Count all people who donated, fundraised, campaigned or was
        a task member. People should be unique across all categories.
        """
        if False and self._get_cached('people-involved-total'):
            return self._get_cached('people-involved-total')

        donator_ids = Order.objects.filter(status__in=(
            StatusDefinition.PENDING, StatusDefinition.SUCCESS)).order_by(
            'user__id').distinct('user').values_list('user_id', flat=True)
        fundraiser_owner_ids = Fundraiser.objects.order_by(
            'owner__id').distinct('owner').values_list('owner_id', flat=True)
        project_owner_ids = Project.objects.filter(status__slug__in=(
            'campaign', 'done-complete', 'done-incomplete',)).order_by(
            'owner__id').distinct('owner').values_list('owner_id', flat=True)
        task_member_ids = TaskMember.objects.order_by('member__id').distinct(
            'member').values_list('member_id', flat=True)
        task_owner_ids = Task.objects.order_by('author__id').distinct(
            'author').values_list('author_id', flat=True)

        items = [donator_ids, fundraiser_owner_ids, project_owner_ids,
                 task_member_ids, task_owner_ids]

        # get count of unique member ids
        seen = set()
        seen_add = seen.add
        people_count = len([item for item in list(itertools.chain(*items)) if
                            item and not (item in seen or seen_add(item))])

        # Add anonymous donators
        people_count += Order.objects.filter(user_id=None, status__in=(
            StatusDefinition.PENDING, StatusDefinition.SUCCESS)).count()

        # Add "plus one"
        people_count += \
            TaskMember.objects.all().aggregate(externals=Sum('externals'))[
                'externals'] or 0

        self._set_cached('people-involved-total', people_count)

        return people_count

    @property
    def tasks_realized(self):
        from bluebottle.tasks.models import Task

        """ Count all realized tasks (status == realized) """
        if self._get_cached('tasks-realized-total'):
            return self._get_cached('tasks-realized-total')
        task_count = Task.objects.filter(status='realized').count()
        self._set_cached('tasks-realized-total', task_count)

        return task_count

    @property
    def projects_realized(self):
        from bluebottle.projects.models import Project

        """ Count all realized projects (status in done-complete or done-incomplete) """
        if self._get_cached('projects-realized-total'):
            return self._get_cached('projects-realized-total')
        project_count = Project.objects.filter(
            status__slug__in=('done-complete', 'done-incomplete',)).count()
        self._set_cached('projects-realized-total', project_count)

        return project_count

    @property
    def projects_online(self):
        from bluebottle.projects.models import Project

        """ Count all running projects (status == campaign) """
        if self._get_cached('projects-online-total'):
            return self._get_cached('projects-online-total')
        project_count = Project.objects.filter(status__slug='campaign').count()
        self._set_cached('projects-online-total', project_count)

        return project_count

    @property
    def donated(self):
        from bluebottle.donations.models import Donation

        """ Add all donation amounts for all donations ever """
        if self._get_cached('donations-total'):
            return self._get_cached('donations-total')
        donations = Donation.objects.filter(order__status__in=(
            StatusDefinition.PENDING, StatusDefinition.SUCCESS))
        donated = donations.aggregate(sum=Sum('amount'))['sum'] or '000'
        self._set_cached('donations-total', donated)

        return donated


# API views

class StatisticDetail(generics.RetrieveAPIView):
    serializer_class = StatisticSerializer

    def get_object(self, queryset=None):
        return Statistics()
