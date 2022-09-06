import logging

from django.db.models.signals import post_save, m2m_changed
from django.contrib.auth.models import Group
from django.dispatch import receiver
from bluebottle.members.models import Member


logger = logging.getLogger(__name__)


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
    open_statuses = ('draft', 'needs_work', 'submitted', 'open', 'running', 'full', )
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
