import logging

from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.models import Group
from django.db import connection
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from hijack.signals import hijack_ended, hijack_started

from bluebottle.members.models import Member
from bluebottle.utils.utils import get_client_ip

logger = logging.getLogger(__name__)


def log_impersonation(request, hijacker, hijacked, message):
    LogEntry.objects.log_actions(
        user_id=hijacker.pk,
        queryset=Member.objects.filter(pk=hijacked.pk),
        action_flag=CHANGE,
        change_message=message,
        single_object=True,
    )
    logger.info(
        '%s: hijacker=%s hijacked=%s tenant=%s ip=%s',
        message,
        hijacker.pk,
        hijacked.pk,
        getattr(connection.tenant, 'schema_name', None),
        get_client_ip(request),
    )


@receiver(hijack_started)
def hijack_started_log(sender, request, hijacker, hijacked, **kwargs):
    log_impersonation(request, hijacker, hijacked, 'Started impersonating')


@receiver(hijack_ended)
def hijack_ended_log(sender, request, hijacker, hijacked, **kwargs):
    log_impersonation(request, hijacker, hijacked, 'Stopped impersonating')


@receiver(post_save)
def member_created_groups(sender, instance, created, **kwargs):
    from django.contrib.auth import get_user_model

    USER_MODEL = get_user_model()
    if isinstance(instance, USER_MODEL) and created:
        try:
            group = Group.objects.get(name='Authenticated')
            group.user_set.add(instance)
        except Group.DoesNotExist:
            logger.error('Group \'{}\' could not be found'.format('Authenticated'))


@receiver(m2m_changed, sender=Member.segments.through)
def segments_changed(sender, instance, action, pk_set, *args, **kwargs):
    """
    When a segment is added or removed from a user, update all *open* activities
    and also add or remove the segment from there.
    All closed or succeeded activities remain untouched, so that historical data
    will stay accurate.
    """
    open_statuses = ('draft', 'needs_work', 'submitted', 'open', 'running', 'full',)
    if action == 'post_add':
        for activity in instance.activities.filter(
            status__in=open_statuses
        ):
            for segment in instance.segments.filter(segment_type__inherit=True):
                activity.segments.add(segment)

    if action == 'post_remove':
        for activity in instance.activities.filter(
            status__in=open_statuses
        ):
            for segment in activity.segments.filter(segment_type__inherit=True, pk__in=pk_set):
                activity.segments.remove(segment)
