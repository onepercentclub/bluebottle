from django.db import models

from bluebottle.activity_pub.models.activities import Activity
from bluebottle.activity_pub.models.actors import Team
from bluebottle.activity_pub.models.events import SubEvent, DoGoodEvent
from bluebottle.fsm.state import TransitionNotPossible


def _end_remote_contributor(contributor):
    """Withdraw a remote contributor on the supplier after Leave."""
    try:
        if hasattr(contributor.states, 'withdraw'):
            contributor.states.withdraw(save=True)
            return True
    except TransitionNotPossible:
        pass
    return False


class Transition(Activity):
    object = models.ForeignKey('activity_pub.ActivityPubModel', on_delete=models.CASCADE)
    transitioned = models.BooleanField(default=False)

    @property
    def default_recipients(self):
        for create in self.object.create_set.all():
            for recipient in create.recipients.all():
                yield recipient.actor

    def save(self, *args, **kwargs):
        if not self.is_local and not self.transitioned:
            if self.transition():
                self.transitioned = True

        super().save(*args, **kwargs)

    def transition(self):
        raise NotImplementedError()


class Delete(Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.cancel(save=True)
            return True

        if self.object.link:
            self.object.link.delete()
            return True


class Start(Transition):
    def transition(self):
        if self.object.adopted:
            try:
                self.object.adopted.states.publish(save=True)
                return True
            except TransitionNotPossible:
                pass

        if self.object.link:
            try:
                self.object.link.states.start(save=True)
                return True
            except TransitionNotPossible:
                pass


class Cancel(Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.cancel(save=True)
            return True

        if self.object.link:
            self.object.link.states.cancel(save=True)
            return True


class Finish(Transition):
    def transition(self):
        if self.object.adopted:
            try:
                self.object.adopted.states.succeed(save=True)
            except TransitionNotPossible:
                pass

            return True

        if self.object.link:
            self.object.link.states.succeed(save=True)
            return True


class Lock(Transition):
    def transition(self):
        if self.object.adopted:
            self.object.adopted.states.lock(save=True)
            return True


class Leave(Transition):
    """Sent when a user leaves a synced activity or team."""

    @property
    def default_recipients(self):
        obj = self.object
        if isinstance(obj, Team):
            event = obj.attributed_to
            create = event.create_set.first() if event else None
        elif isinstance(obj, SubEvent):
            parent = obj.parent
            create = parent.create_set.first() if parent else None
        else:
            create = obj.create_set.first()
        if create:
            yield create.actor

    def transition(self):
        if isinstance(self.object, Team):
            team = (
                self.object.origin if self.object.is_local else self.object.adopted
            )
            if not team:
                return False
            member = team.team_members.filter(
                remote_user=self.actor.adopted
            ).first()
            if member:
                return _end_remote_contributor(member)
            return False

        if not self.object.is_local:
            return False

        if isinstance(self.object, SubEvent):
            slot = self.object.origin
            if not slot:
                return False
            contributor = slot.participants.filter(
                remote_user=self.actor.adopted
            ).first()
            if not contributor:
                return False
            return _end_remote_contributor(contributor)

        if isinstance(self.object, DoGoodEvent) and self.object.activity_type == 'PeriodicActivity':
            registration = self.object.origin.registrations.get(
                remote_user=self.actor.adopted
            )
            registration.states.stop(save=True)
        elif (
            isinstance(self.object, DoGoodEvent)
            and self.object.is_team_activity
        ):
            registration = self.object.origin.registrations.get(
                remote_user=self.actor.adopted
            )
            for team in registration.teams.all():
                _end_remote_contributor(team)
        else:
            contributor = self.object.origin.contributors.get(
                remote_user=self.actor.adopted
            )
            return _end_remote_contributor(contributor)

        return True
