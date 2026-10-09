from django.db import models

from bluebottle.activity_pub.models.activities import Activity
from bluebottle.fsm.state import TransitionNotPossible


class Transition(Activity):
    object = models.ForeignKey('activity_pub.ActivityPubModel', on_delete=models.CASCADE)
    transitioned = models.BooleanField(default=False)

    @property
    def default_recipients(self):
        for create in self.object.create_set.all():
            for recipient in create.recipients.all():
                yield recipient.actor

    @property
    def has_target(self):
        return True

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


class ActivityTransitionMixin:
    @property
    def has_target(self):
        # Without an adopted activity or link there is nothing to transition yet;
        # leave it untransitioned so it is retried once the object is adopted or linked
        return bool(self.object.adopted or getattr(self.object, 'link', None))


class Delete(ActivityTransitionMixin, Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.cancel(save=True)

        if self.object.link:
            self.object.link.delete()


class Start(ActivityTransitionMixin, Transition):
    def transition(self):
        if self.object.adopted:
            if self.object.adopted.status == 'cancelled':
                self.object.adopted.states.auto_approve(save=True)
            else:
                self.object.adopted.states.publish(save=True)

        if self.object.link:
            self.object.link.states.start(save=True)


class Cancel(ActivityTransitionMixin, Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.cancel(save=True)

        if self.object.link:
            self.object.link.states.cancel(save=True)


class Finish(ActivityTransitionMixin, Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.succeed(save=True)

        if self.object.link:
            self.object.link.states.succeed(save=True)


class Lock(ActivityTransitionMixin, Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.lock(save=True)
