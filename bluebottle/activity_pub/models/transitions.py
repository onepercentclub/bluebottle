from django.db import models

from bluebottle.activity_pub.models.activities import Activity
from bluebottle.fsm.state import TransitionNotPossible


class Transition(Activity):
    object = models.ForeignKey('activity_pub.ActivityPubModel', on_delete=models.CASCADE)
    transitioned = models.BooleanField(default=False)

    @property
    def default_recipients(self):
        from bluebottle.activity_pub.models.events import SubEvent

        # Slots are published as part of their parent event, so they share its recipients
        obj = self.object.parent if isinstance(self.object, SubEvent) else self.object

        for create in obj.create_set.all():
            for recipient in create.recipients.all():
                yield recipient.actor

    @property
    def has_target(self):
        """Transitions should only happen when the object is adopted on the platform"""
        return bool(self.object.adopted or self.object.origin or getattr(self.object, 'link', None))

    def save(self, *args, **kwargs):
        if not self.is_local and not self.transitioned and self.has_target:
            try:
                self.transition()
                self.transitioned = True
            except TransitionNotPossible:
                pass

        super().save(*args, **kwargs)

    def transition(self):
        raise NotImplementedError()


class Delete(Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.cancel(save=True)

        if self.object.link:
            self.object.link.delete()


class Start(Transition):
    def transition(self):
        if self.object.adopted:
            if self.object.adopted.status == 'cancelled':
                self.object.adopted.states.auto_approve(save=True)
            else:
                self.object.adopted.states.publish(save=True)

        if self.object.link:
            self.object.link.states.start(save=True)


class Cancel(Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.cancel(save=True)

        if getattr(self.object, 'link', None):
            self.object.link.states.cancel(save=True)


class Finish(Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.succeed(save=True)

        if self.object.link:
            self.object.link.states.succeed(save=True)


class Lock(Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.lock(save=True)
