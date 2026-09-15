from bluebottle.activity_pub.models.transitions import Transition
from bluebottle.activity_pub.models.events import DoGoodEvent, SubEvent


class Remove(Transition):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(self.object, DoGoodEvent) and self.object.activity_type == 'PeriodicActivity':
            self.__class__ = RegistrationRemove
        if isinstance(self.object, SubEvent):
            if self.object.parent.activity_type == 'DateActivity':
                self.__class__ = DateSlotRemove
            else:
                self.__class__ = ScheduleSlotRemove

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
