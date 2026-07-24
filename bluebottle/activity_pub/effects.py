from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from bluebottle.activity_links.models import LinkedActivity
from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import (
    Accept, Follow, Lock, Start, Cancel, Delete, Finish, Leave,
    Event, Join, Reject, Create, Update
)
from bluebottle.activity_pub.utils import get_platform_actor
from bluebottle.fsm.effects import Effect


class CreateEffect(Effect):
    """
    Publish the activity to the followers of the actor through GoodUp Connect
    """

    display = True
    template = 'admin/activity_pub/create_effect.html'

    def post_save(self, **kwargs):
        adapter.sync(self.instance)

    @property
    def followers(self):
        actor = get_platform_actor()
        followers = Follow.objects.filter(publish_mode='automatic', accept__actor=actor)
        return followers

    @property
    def is_open(self):
        return not self.instance.segments.filter(closed=True).exists()

    @property
    def is_valid(self):
        return self.is_open and self.followers.exists()

    def __str__(self):
        return str(_('Publish activity to followers'))


class SyncRelatedEvent(Effect):
    """
    Publish the related activity to the followers of the actor through GoodUp Connect
    """

    display = True
    template = 'admin/activity_pub/create_effect.html'

    def post_save(self, **kwargs):
        event = adapter.sync(self.instance.activity)

        Update.objects.create(
            actor=get_platform_actor(),
            object=event
        )

    @property
    def is_valid(self):
        return hasattr(self.instance.activity, 'activity_pub_model')

    def __str__(self):
        return str(_('Publish activity to followers'))


class SyncEffect(Effect):
    """
    Publish the activity to the followers of the actor through GoodUp Connect
    """

    display = True
    template = 'admin/activity_pub/create_effect.html'

    def post_save(self, **kwargs):
        if not hasattr(self.instance, 'activity_pub_model'):
            activity = Create
        else:
            activity = Update

        adapter.sync(self.instance)

        activity.objects.create(
            actor=get_platform_actor(),
            object=self.instance.activity_pub_model
        )

    @property
    def is_valid(self):
        return hasattr(self.instance, 'activity_pub_model')

    def __str__(self):
        return str(_('Publish activity to followers'))


class SyncSlotEffect(SyncEffect):
    @property
    def is_valid(self):
        return hasattr(self.instance.activity, 'activity_pub_model')


class PublishAdoptionEffect(Effect):
    """
    Announce that the activity has been adopted through GoodUp Connect.
    """
    display = True
    template = 'admin/activity_pub/publish_adoption_effect.html'

    def post_save(self, **kwargs):
        event = self.instance.origin
        actor = get_platform_actor()

        Accept.objects.create(actor=actor, object=event)

    @property
    def is_valid(self):
        return (
            getattr(self.instance, 'origin', False) or
            isinstance(self.instance, LinkedActivity)
        ) and get_platform_actor() is not None

    def __str__(self):
        return str(_('Publish that the activity has been adopted'))


class UpdateEventEffect(Effect):
    display = True
    template = 'admin/activity_pub/update_event_effect.html'

    def post_save(self, **kwargs):
        event = Event.sync(self.instance)

        Update.objects.create(
            actor=get_platform_actor(),
            object=event
        )

    @property
    def is_valid(self):
        return (
            hasattr(self.instance, 'activity_pub_model') and
            self.instance.activity_pub_model.is_local and
            get_platform_actor() is not None
        )

    def __str__(self):
        return str(_('Notify subscribers of the changes'))


class CancelEffect(Effect):
    template = 'admin/activity_pub/cancel_effect.html'

    def post_save(self, **kwargs):
        Cancel.objects.create(
            object=self.instance.activity_pub_model
        )

    @property
    def is_valid(self):
        return (
            hasattr(self.instance, 'activity_pub_model') and
            self.instance.activity_pub_model.is_local and
            get_platform_actor() is not None
        )

    def __str__(self):
        return str(_('Notify subscribers of the cancelation'))


class StartEffect(Effect):
    template = 'admin/activity_pub/start_effect.html'

    def post_save(self, **kwargs):
        Start.objects.create(
            object=self.instance.activity_pub_model
        )

    @property
    def is_valid(self):
        return (
            hasattr(self.instance, 'activity_pub_model') and
            self.instance.activity_pub_model.is_local and
            get_platform_actor() is not None
        )

    def __str__(self):
        return str(_('Notify subscribers of the start of an activity'))


class FinishEffect(Effect):
    template = 'admin/activity_pub/finish_effect.html'

    def post_save(self, **kwargs):
        Finish.objects.create(
            object=self.instance.activity_pub_model
        )

    @property
    def is_valid(self):
        return (
            hasattr(self.instance, 'activity_pub_model') and
            self.instance.activity_pub_model.is_local and
            get_platform_actor() is not None
        )

    def __str__(self):
        return str(_('Notify subscribers of the end'))


class LockEffect(Effect):
    template = 'admin/activity_pub/lock_effect.html'

    def post_save(self, **kwargs):
        Lock.objects.create(
            object=self.instance.activity_pub_model
        )

    @property
    def is_valid(self):
        return (
            hasattr(self.instance, 'activity_pub_model') and
            self.instance.activity_pub_model.is_local and
            get_platform_actor() is not None
        )

    def __str__(self):
        return str(_('Notify subscribers of the lock'))


class DeletedEffect(Effect):
    template = 'admin/activity_pub/delete_effect.html'

    def post_save(self, **kwargs):
        Delete.objects.create(
            object=self.instance.activity_pub_model
        )

    @property
    def is_valid(self):
        return (
            hasattr(self.instance, 'activity_pub_model') and
            self.instance.activity_pub_model.is_local and
            get_platform_actor() is not None
        )

    def __str__(self):
        return str(_('Notify subscribers of the deletion'))


def activity_is_synced(effect):
    """Contributor's activity has an origin (synced from another platform)."""
    return getattr(effect.instance.activity, 'origin', None) is not None


def contributor_is_local(effect):
    return effect.instance.remote_user is None


def can_send_leave(effect):
    return activity_is_synced(effect)


class SendJoinEffect(Effect):
    """
    Send a Join activity to the source platform when a user joins a synced deed.
    """
    template = 'admin/activity_pub/send_join_effect.html'
    conditions = [activity_is_synced, contributor_is_local]

    def post_save(self, **kwargs):
        adapter.sync(self.instance)

    @property
    def is_valid(self):
        return super().is_valid

    def __str__(self):
        return str(_('Notify source platform of join'))


class SendJoinSlotEffect(Effect):
    """
    Send a Join activity to the source platform when a user joins a synced deed.
    """
    template = 'admin/activity_pub/send_join_effect.html'

    def post_save(self, **kwargs):
        if self.instance.slot:
            Join.objects.create(
                actor=self.instance.remote_user.origin,
                object=adapter.sync(self.instance.slot)
            )

    @property
    def is_valid(self):
        return self.instance.remote_user is not None

    def __str__(self):
        return str(_('Notify source platform of join'))


class SendLeaveEffect(Effect):
    """
    Send a Leave activity to the source platform when a user leaves an activity
    """
    template = 'admin/activity_pub/send_leave_effect.html'
    conditions = [can_send_leave]

    def post_save(self, **kwargs):
        Leave.objects.create(
            actor=self.instance.user.activity_pub_model,
            object=self.instance.activity.origin,
        )

    def __str__(self):
        return str(_('Notify source platform of leave'))


def participant_is_not_local(effect):
    return effect.instance.remote_user is not None


def remote_user_has_origin(effect):
    remote_user = effect.instance.remote_user
    if remote_user is None:
        return False
    try:
        return remote_user.origin is not None
    except ObjectDoesNotExist:
        return False
    except AttributeError:
        return False


class SendAcceptEffect(Effect):
    """
    Send a Accept activity to the consumer platform when a user is accepted.
    """
    template = 'admin/activity_pub/send_accept_effect.html'
    conditions = [participant_is_not_local, remote_user_has_origin]

    def post_save(self, **kwargs):
        join = Join.objects.filter(
            actor=self.instance.remote_user.origin,
            object=self.instance.activity.activity_pub_model
        ).latest('pk')
        Accept.objects.create(
            actor=get_platform_actor(),
            object=join
        )

    def __str__(self):
        return str(_('Notify consumer platform of acceptance'))


class SendRejectEffect(Effect):
    """
    Send a Reject activity to the consumer platform when a user is rejected.
    """
    template = 'admin/activity_pub/send_reject_effect.html'
    conditions = [participant_is_not_local, remote_user_has_origin]

    def post_save(self, **kwargs):
        join = Join.objects.filter(
            actor=self.instance.remote_user.origin,
            object=self.instance.activity.activity_pub_model
        ).latest('pk')
        Reject.objects.create(
            actor=get_platform_actor(),
            object=join
        )

    def __str__(self):
        return str(_('Notify consumer platform of rejection'))
