from django.db import transaction
from django.db.models import QuerySet
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from bluebottle.organizations.messages import (
    OrganizationMemberAddedMessage, OrganizationMemberRemovedMessage
)
from bluebottle.organizations.models import OrganizationMember


def notify(message_class, membership):
    message = message_class(membership.organization, member=membership.member)
    transaction.on_commit(message.compose_and_send, robust=True)


def is_direct_delete(origin):
    """Only mail for deleted memberships, not for cascades from a member or organisation."""
    if isinstance(origin, QuerySet):
        return origin.model is OrganizationMember
    return isinstance(origin, OrganizationMember)


@receiver(pre_save, sender=OrganizationMember)
def remember_previous_membership(sender, instance, raw=False, **kwargs):
    instance._previous_membership = None
    if instance.pk and not raw:
        instance._previous_membership = OrganizationMember.objects.select_related(
            'member', 'organization'
        ).filter(pk=instance.pk).first()


@receiver(post_save, sender=OrganizationMember)
def membership_saved(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    previous = instance._previous_membership
    if created:
        notify(OrganizationMemberAddedMessage, instance)
    elif previous and (
        previous.member_id != instance.member_id or
        previous.organization_id != instance.organization_id
    ):
        notify(OrganizationMemberRemovedMessage, previous)
        notify(OrganizationMemberAddedMessage, instance)


@receiver(post_delete, sender=OrganizationMember)
def membership_deleted(sender, instance, origin=None, **kwargs):
    if is_direct_delete(origin):
        notify(OrganizationMemberRemovedMessage, instance)
