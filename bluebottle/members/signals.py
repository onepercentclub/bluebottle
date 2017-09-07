import logging

from django.db.models.signals import post_save
from django.contrib.auth.models import Group
from django.dispatch import receiver


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
