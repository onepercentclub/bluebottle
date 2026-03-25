from django.utils.translation import gettext_lazy as _

from bluebottle.activity_links.models import LinkedActivity
from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import (
    Accept, Follow, Start, Update, Cancel, Delete, Finish, Join, Leave,
    Create, Recipient
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
        adapter.create_or_update_event(self.instance)

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


class PublishAdoptionEffect(Effect):
    """
    Announce that the activity has been adopted through GoodUp Connect.
    """
    display = True
    template = 'admin/activity_pub/publish_adoption_effect.html'

    def post_save(self, **kwargs):
        if hasattr(self.instance, 'origin'):
            event = self.instance.origin
        else:
            event = self.instance.event

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
        adapter.create_or_update_event(self.instance)
        Update.objects.create(
            object=self.instance.event
        )

    @property
    def is_valid(self):
        return hasattr(self.instance, 'event') and get_platform_actor() is not None

    def __str__(self):
        return str(_('Notify subscribers of the changes'))


class CancelEffect(Effect):
    template = 'admin/activity_pub/cancel_effect.html'

    def post_save(self, **kwargs):
        Cancel.objects.create(
            object=self.instance.event
        )

    @property
    def is_valid(self):
        return hasattr(self.instance, 'event') and get_platform_actor() is not None

    def __str__(self):
        return str(_('Notify subscribers of the cancelation'))


class StartEffect(Effect):
    template = 'admin/activity_pub/start_effect.html'

    def post_save(self, **kwargs):
        Start.objects.create(
            object=self.instance.event
        )

    @property
    def is_valid(self):
        return hasattr(self.instance, 'event') and get_platform_actor() is not None

    def __str__(self):
        return str(_('Notify subscribers of the start of an activity'))


class FinishEffect(Effect):
    template = 'admin/activity_pub/finish_effect.html'

    def post_save(self, **kwargs):
        Finish.objects.create(
            object=self.instance.event
        )

    @property
    def is_valid(self):
        return hasattr(self.instance, 'event') and get_platform_actor() is not None

    def __str__(self):
        return str(_('Notify subscribers of the end'))


class DeletedEffect(Effect):
    template = 'admin/activity_pub/delete_effect.html'

    def post_save(self, **kwargs):
        Delete.objects.create(
            object=self.instance.event
        )

    @property
    def is_valid(self):
        return hasattr(self.instance, 'event') and get_platform_actor() is not None

    def __str__(self):
        return str(_('Notify subscribers of the deletion'))


def activity_is_synced(effect):
    """Contributor's activity has an origin (synced from another platform)."""
    activity = getattr(effect.instance, 'activity', None)
    return getattr(activity, 'origin', None) is not None


def contributor_has_sync_source(effect):
    contributor = effect.instance
    return (
        getattr(contributor, 'sync_id', None) and
        getattr(contributor, 'sync_actor', None) is not None
    )


def can_send_leave(effect):
    return activity_is_synced(effect) or contributor_has_sync_source(effect)


class SendJoinEffect(Effect):
    """
    Send a Join activity to the source platform when a user joins a synced deed.
    Runs only when the activity is synced (via activity_is_synced condition).
    Includes participant name and email so the source has a full participant list.
    """
    template = 'admin/activity_pub/send_join_effect.html'
    post_save = True
    conditions = [activity_is_synced]

    def post_save(self, **kwargs):
        import uuid
        from bluebottle.deeds.models import DeedParticipant

        contributor = self.instance
        if not isinstance(contributor, DeedParticipant):
            return
        deed = contributor.activity
        if not getattr(deed, 'origin', None):
            return

        # Ensure we have a stable sync_id for this participant (for Leave matching)
        if not contributor.sync_id:
            from bluebottle.activities.models import RemoteContributor

            remote_contributor = RemoteContributor.objects.create(
                sync_id=str(uuid.uuid4()),
                display_name=contributor.display_name_or_user or '',
                email=contributor.email_or_user,
            )
            contributor.remote_contributor = remote_contributor
            contributor.save(update_fields=['remote_contributor'])

        # Name and email: from user when present, else from remote_contributor
        participant_name = contributor.display_name_or_user or None
        participant_email = contributor.email_or_user or None

        join_activity = Join.objects.create(
            actor=get_platform_actor(),
            object=deed.origin,
            participant_sync_id=contributor.sync_id,
            participant_name=participant_name,
            participant_email=participant_email,
        )
        if join_activity.recipients.count() == 0:
            create = Create.objects.filter(object=deed.origin).first()
            if create:
                Recipient.objects.get_or_create(actor=create.actor, activity=join_activity)

    @property
    def is_valid(self):
        return (
            super().is_valid and
            get_platform_actor() is not None
        )

    def __str__(self):
        return str(_('Notify source platform of join'))


class SendLeaveEffect(Effect):
    """
    Send a Leave activity to the source platform when a user leaves a synced deed.
    Runs only when the activity is synced (via activity_is_synced condition).
    Includes participant_sync_id so the source can remove the right participant.
    """
    template = 'admin/activity_pub/send_leave_effect.html'
    post_save = True
    conditions = [can_send_leave]

    def post_save(self, **kwargs):
        from bluebottle.deeds.models import DeedParticipant

        contributor = self.instance
        if not isinstance(contributor, DeedParticipant):
            return
        deed = contributor.activity
        target_event = getattr(deed, 'origin', None) or getattr(deed, 'event', None)
        if not target_event:
            return

        leave_activity = Leave.objects.create(
            actor=get_platform_actor(),
            object=target_event,
            participant_sync_id=contributor.sync_id or None,
        )
        # Always ensure we route to the right counterparty:
        # - When leaving a synced deed (follower -> source): send to source actor (Create.actor for origin).
        # - When removing/rejecting a remote participant (source -> follower): send to contributor.sync_actor.
        if getattr(deed, 'origin', None):
            create = Create.objects.filter(object=deed.origin).first()
            if create:
                Recipient.objects.get_or_create(actor=create.actor, activity=leave_activity)
        if contributor.sync_actor:
            Recipient.objects.get_or_create(actor=contributor.sync_actor, activity=leave_activity)

    @property
    def is_valid(self):
        return (
            super().is_valid and
            get_platform_actor() is not None
        )

    def __str__(self):
        return str(_('Notify source platform of leave'))
