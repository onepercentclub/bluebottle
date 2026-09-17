from bluebottle.activity_pub.models.transitions import Transition
from bluebottle.activity_pub.models.events import DoGoodEvent, SubEvent
from bluebottle.activity_pub.models.actors import Team

from bluebottle.utils.utils import get_subclasses


class Leave(Transition):
    """Sent when a user leaves a synced activity or team."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for subclass in get_subclasses(self.__class__):
            if subclass.matches(self.object, self.actor):
                self.__class__ = subclass

    def transition(self):
        self.contributor.states.withdraw(save=True)

        return True

    @property
    def contributor(self):
        return self.object.origin.contributors.get(
            remote_user=self.actor.adopted
        )

    @property
    def default_recipients(self):
        yield self.object.source


class RegistrationLeave(Leave):
    @classmethod
    def matches(cls, object, actor):
        return isinstance(object, DoGoodEvent) and object.activity_type == 'PeriodicActivity'

    class Meta:
        proxy = True

    @property
    def contributor(self):
        return self.object.origin.registrations.get(
            remote_user=self.actor.adopted
        )

    def transition(self):
        self.contributor.states.stop(save=True)

        return True


class TeamLeave(Leave):
    @classmethod
    def matches(cls, object, actor):
        return isinstance(actor, Team)

    class Meta:
        proxy = True

    @property
    def default_recipients(self):
        return self.object.activity.source


class TeamMemberLeave(Leave):
    @classmethod
    def matches(self, object, actor):
        return (
            isinstance(object, DoGoodEvent) and
            object.activity_type == 'ScheduleActivity' and
            isinstance(actor, Team)
        )

    class Meta:
        proxy = True

    @property
    def default_recipients(self):
        return self.object.activity.source


class SlotParticipantLeave(Leave):
    @classmethod
    def matches(self, object, actor):
        return isinstance(object, SubEvent)

    class Meta:
        proxy = True

    @property
    def default_recipients(self):
        return self.object.partent.source
