from django.utils.translation import gettext_lazy as _

from bluebottle.activity_links.models import LinkedActivity
from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import (
    Accept, Follow, Update, Cancel, Delete, Finish
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
