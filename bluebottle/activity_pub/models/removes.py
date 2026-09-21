from bluebottle.activity_pub.models.transitions import Transition
from bluebottle.activity_pub.models.events import DoGoodEvent, SubEvent
from bluebottle.activity_pub.models.actors import Team

from bluebottle.utils.utils import get_subclasses


class Remove(Transition):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for subclass in get_subclasses(self.__class__):
            if subclass.matches(self.object, self.actor):
                self.__class__ = subclass

    @classmethod
    def matches(cls, object, actor):
        return False

    @property
    def local_contributor(self):
        return self.object.origin.contributors.get(remote_user=self.actor.adopted)

    @property
    def remote_contributor(self):
        return self.object.adopted.contributors.get(user=self.actor.origin)

    @property
    def contributor(self):
        if self.object.is_local:
            return self.local_contributor
        else:
            return self.remote_contributor

    def transition(self):
        contributor = self.contributor
        contributor.states.remove()
        contributor.execute_triggers(ap_prevent_recursion=True)
        contributor.save()

        return True

    @property
    def local_recipients(self):
        __import__('ipdb').set_trace()
        yield self.actor.source

    @property
    def remote_recipients(self):
        yield self.object.source

    @property
    def default_recipients(self):
        if self.object.is_local:
            return self.local_recipients
        else:
            return self.remote_recipients


class RegistrationRemove(Remove):
    @classmethod
    def matches(cls, object, actor):
        return isinstance(object, DoGoodEvent) and object.activity_type == 'PeriodicActivity'

    class Meta:
        proxy = True

    @property
    def local_contributor(self):
        return self.object.origin.registrations.get(remote_user=self.actor.adopted)

    @property
    def remote_contributor(self):
        return self.object.adopted.registrations.get(user=self.actor.origin)


class SlotRemove(Remove):
    class Meta:
        proxy = True

    @property
    def remote_recipients(self):
        yield self.object.parent.source


class DateSlotRemove(Remove):
    @classmethod
    def matches(cls, object, actor):
        return isinstance(object, SubEvent) and object.parent.activity_type == 'DateActivity'

    class Meta:
        proxy = True

    @property
    def local_contributor(self):
        return self.object.parent.origin.contributors.get(
            dateparticipant__slot=self.object.origin,
            remote_user=self.actor.adopted
        )

    @property
    def remote_contributor(self):
        return self.object.parent.adopted.contributors.get(
            dateparticipant__slot=self.object.adopted,
            user=self.actor.origin
        )


class ScheduleSlotRemove(Remove):
    @classmethod
    def matches(cls, object, actor):
        return isinstance(object, SubEvent) and not object.parent.activity_type == 'DateActivity'

    class Meta:
        proxy = True

    @property
    def local_contributor(self):
        return self.object.parent.origin.contributors.get(
            scheduleparticipant__slot=self.object.origin,
            remote_user=self.actor.adopted
        )

    @property
    def remote_contributor(self):
        return self.object.parent.adopted.contributors.get(
            scheduleparticipant__slot=self.object.adopted,
            user=self.actor.origin
        )


class TeamRemove(Remove):
    @classmethod
    def matches(cls, object, actor):
        return isinstance(actor, Team)

    class Meta:
        proxy = True

    @property
    def local_contributor(self):
        return self.actor.adopted

    @property
    def remote_contributor(self):
        return self.actor.origin

    @property
    def local_recipients(self):
        yield self.actor.captain.source

    @property
    def remote_recipients(self):
        yield self.object.source
