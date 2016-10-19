from django.db import models
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property
from django.core.exceptions import ObjectDoesNotExist

from bluebottle.bb_accounts.models import BlueBottleBaseUser
from bluebottle.projects.models import Project
from bluebottle.fundraisers.models import Fundraiser
from bluebottle.tasks.models import TaskMember
from bluebottle.utils.utils import StatusDefinition


GROUP_PERMS = {
    'Staff': {
        'perms': (
            'add_member', 'change_member', 'delete_member',
        )
    }
}


class Member(BlueBottleBaseUser):
    verified = models.BooleanField(default=False, blank=True)
    remote_id = models.CharField(_('remote_id'),
                                 max_length=75,
                                 blank=True,
                                 null=True)

    def __init__(self, *args, **kwargs):
        super(Member, self).__init__(*args, **kwargs)

        try:
            self._previous_last_seen = self.last_seen
        except ObjectDoesNotExist:
            self._previous_last_seen = None

    class Analytics:
        type = 'member'
        tags = {}
        fields = {
            'user_id': 'id'
        }

        def extra_tags(self, obj, created):
            if created:
                return {'event': 'signup'}
            else:
                # The skip method below is being used to ensure analytics are only
                # triggered if the last_seen field has changed.
                return {'event': 'seen'}

        def skip(self, obj, created):
            # Currently only the signup (created) event is being recorded
            # and when the last_seen changes.
            return False if created or obj.last_seen != obj._previous_last_seen else True

    def get_tasks_qs(self):
        return TaskMember.objects.filter(
            member=self, status__in=['applied', 'accepted', 'realized'])

    @property
    def time_spent(self):
        """ Returns the number of donations a user has made """
        return self.get_tasks_qs().aggregate(Sum('time_spent'))[
            'time_spent__sum']

    @property
    def is_volunteer(self):
        return self.time_spent > 0

    @cached_property
    def sourcing(self):
        return self.get_tasks_qs().distinct('task__project').count()

    @property
    def fundraiser_count(self):
        return Fundraiser.objects.filter(owner=self).count()

    @property
    def project_count(self):
        """ Return the number of projects a user started / is owner of """
        return Project.objects.filter(
            owner=self,
            status__slug__in=['campaign', 'done-complete', 'done-incomplete', 'voting', 'voting-done']
        ).count()

    @property
    def is_initiator(self):
        return self.project_count > 0

    @property
    def has_projects(self):
        """ Return the number of projects a user started / is owner of """
        return Project.objects.filter(owner=self).count() > 0

    @property
    def amount_donated(self):
        return self.order_set.filter(
            status=StatusDefinition.SUCCESS
        ).aggregate(
            amount_donated=models.Sum('total')
        )['amount_donated']

    @property
    def is_supporter(self):
        return self.amount_donated > 0
