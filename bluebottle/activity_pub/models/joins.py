from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils.module_loading import import_string

from bluebottle.activities.models import Organizer

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models.actors import Organization, Team
from bluebottle.activity_pub.models.base import ActivityPubModel
from bluebottle.activity_pub.models.events import GoodDeed, CollectCampaign, DoGoodEvent, SubEvent
from bluebottle.activity_pub.models.activities import Activity


from bluebottle.utils.utils import get_subclasses


class Join(Activity):

    """Sent by a follower when a user joins an Event"""
    object = models.ForeignKey(ActivityPubModel, on_delete=models.CASCADE)
    motivation = models.TextField(null=True, blank=True)

    platform = models.ForeignKey(Organization, null=True, on_delete=models.CASCADE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for subclass in get_subclasses(BaseJoin):
            if subclass.matches(self.object, self.actor):
                self.__class__ = subclass

        if self.__class__ == Join:
            raise TypeError(f'Cannot find proxy model for: {self.object}, {self.actor}')

        self.contributor_model = import_string(self.__class__.contributor_model)


class BaseJoin(Join):
    readd_transition = 'readd'

    @classmethod
    def matches(cls, object, actor):
        return False

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.is_local:
            # The join is from a non-local platform. Adopt the actor
            if self.contributor:
                # There already is a contributor. Reapply that contributor
                self.reapply()
            else:
                # Create a new contributor
                self.apply()

    class Meta:
        proxy = True

    @property
    def local_contributor(self):
        adapter.adopt(self.actor)
        self.actor.refresh_from_db()
        return self.object.origin.contributors.not_instance_of(Organizer).get(
            remote_user=self.actor.adopted
        )

    @property
    def remote_contributor(self):
        return self.object.adopted.contributors.not_instance_of(Organizer).get(
            user=self.actor.origin
        )

    @property
    def contributor(self):
        try:
            if self.object.is_local:
                return self.local_contributor
            else:
                return self.remote_contributor
        except ObjectDoesNotExist:
            pass

    def reapply(self):
        if self.contributor.status == 'withdrawn':
            self.contributor.states.reapply(save=True, local=True)
        else:
            getattr(self.contributor.states, self.readd_transition)(save=True, local=True)

    def apply(self):
        """Create a new contributor for the activity"""
        actor = adapter.adopt(self.actor)
        self.contributor_model.objects.create(
            activity=self.object.origin,
            remote_user=actor
        )

    @property
    def default_recipients(self):
        if not self.actor.is_local:
            yield self.actor.source
        else:
            yield self.object.source


class DeedJoin(BaseJoin):
    readd_transition = 're_accept'

    @classmethod
    def matches(cls, object, actor):
        return isinstance(object, GoodDeed)

    class Meta:
        proxy = True

    contributor_model = 'bluebottle.deeds.models.DeedParticipant'


class CollectCampaignJoin(BaseJoin):
    readd_transition = 're_accept'

    @classmethod
    def matches(cls, object, actor):
        return isinstance(object, CollectCampaign)

    class Meta:
        proxy = True

    contributor_model = 'bluebottle.collect.models.CollectContributor'


class RegistrationJoin(BaseJoin):
    class Meta:
        proxy = True

    @property
    def registration(self):
        registration_model = import_string(self.registration_model)
        return registration_model.objects.filter(
            activity=self.object.origin, remote_user=self.actor.adopted
        ).first()

    def apply(self):
        """ Instead of creating a participant, we create a registration"""
        actor = adapter.adopt(self.actor)
        registration_model = import_string(self.registration_model)
        registration_model.objects.create(
            activity=self.object.origin,
            remote_user=actor,
            answer=self.motivation
        )


class DeadlineJoin(RegistrationJoin):
    @classmethod
    def matches(cls, object, actor):
        return isinstance(object, DoGoodEvent) and object.activity_type == 'DeadlineActivity'

    class Meta:
        proxy = True

    registration_model = 'bluebottle.time_based.models.DeadlineRegistration'
    contributor_model = 'bluebottle.time_based.models.DeadlineParticipant'


class PeriodicJoin(RegistrationJoin):
    @classmethod
    def matches(cls, object, actor):
        return isinstance(object, DoGoodEvent) and object.activity_type == 'PeriodicActivity'

    class Meta:
        proxy = True

    def reapply(self):
        """Resume after stop, or restore after remove."""
        registration = self.contributor
        if registration.status == 'removed':
            registration.states.restore(save=True, local=True)
        else:
            registration.states.start(save=True, local=True)

    @property
    def local_contributor(self):
        adapter.adopt(self.actor)
        self.actor.refresh_from_db()
        return self.object.origin.registrations.get(
            remote_user=self.actor.adopted
        )

    @property
    def remote_contributor(self):
        return self.object.adopted.registrations.get(
            user=self.actor.origin
        )

    registration_model = 'bluebottle.time_based.models.PeriodicRegistration'
    contributor_model = 'bluebottle.time_based.models.PeriodicRegistration'


class DateJoin(RegistrationJoin):
    @classmethod
    def matches(cls, object, actor):
        return isinstance(object, DoGoodEvent) and object.activity_type == 'DateActivity'

    class Meta:
        proxy = True

    registration_model = 'bluebottle.time_based.models.DateRegistration'
    contributor_model = 'bluebottle.time_based.models.DateParticipant'


class ScheduleJoin(RegistrationJoin):
    @classmethod
    def matches(cls, object, actor):
        return (
            isinstance(object, DoGoodEvent) and
            not object.is_team_activity and
            object.activity_type == 'ScheduleActivity'
        )

    class Meta:
        proxy = True

    registration_model = 'bluebottle.time_based.models.ScheduleRegistration'
    contributor_model = 'bluebottle.time_based.models.ScheduleParticipant'


class TeamJoin(BaseJoin):
    @classmethod
    def matches(cls, object, actor):
        return isinstance(actor, Team)

    @property
    def remote_contributor(self):
        """ Return the remote contributor, since the Join was created by the consumer"""
        adapter.adopt(self.actor.captain)
        return self.actor.adopted

    @property
    def local_contributor(self):
        """ Return the local contributor, since the Join was created by the supplier"""
        adapter.adopt(self.actor.captain)

        return self.actor.adopted

    def apply(self):
        """ Instead of creating a participant, we create a registration"""
        remote_user = adapter.adopt(self.actor.captain)
        registration_model = import_string(self.registration_model)
        registration = registration_model.objects.create(
            activity=self.object.origin,
            remote_user=remote_user,
            answer=self.motivation
        )

        adapter.adopt(self.actor, activity=registration.activity)

    def reapply(self):
        if self.contributor.status == 'removed':
            self.contributor.states.readd(save=True, local=True)
        else:
            self.contributor.states.rejoin(save=True, local=True)

    @property
    def default_recipients(self):
        if not self.actor.is_local:
            yield self.actor.adopted.activity.activity_pub_model.source
        else:
            yield self.object.source

    class Meta:
        proxy = True

    registration_model = 'bluebottle.time_based.models.TeamScheduleRegistration'
    contributor_model = 'bluebottle.time_based.models.Team'


class TeamMemberJoin(BaseJoin):
    @classmethod
    def matches(cls, object, actor):
        return isinstance(object, Team)

    @property
    def default_recipients(self):
        if not self.actor.is_local:
            yield self.actor.source
        else:
            yield self.object.origin.activity.origin.source

    @property
    def local_contributor(self):
        adapter.adopt(self.actor)
        return self.contributor_model.objects.filter(
            team=self.object.origin,
            user=self.actor.origin
        ).first()

    @property
    def remote_contributor(self):
        return self.contributor_model.objects.filter(
            team=self.object.adopted,
            remote_user=self.actor.adopted
        ).first()

    def apply(self):
        """ Instead of creating a participant, we create a registration"""
        remote_user = adapter.adopt(self.actor)

        self.contributor_model.objects.create(
            team=self.object.adopted,
            remote_user=remote_user
        )

    def reapply(self):
        if self.contributor.status == 'withdrawn':
            self.contributor.states.reapply(save=True, local=True)
        else:
            self.contributor.states.readd(save=True, local=True)

    class Meta:
        proxy = True

    contributor_model = 'bluebottle.time_based.models.TeamMember'


class SlotJoin(BaseJoin):
    @property
    def registration(self):
        registration_model = import_string(self.registration_model)
        return registration_model.objects.get(
            user=self.actor.origin,
            activity=self.object.parent.adopted
        )

    def apply(self):
        """
        The supplier creates the slot and adds the user to that slot.
        This will adopt that event for the local user
        """
        if not self.object.is_local:
            slot = adapter.adopt(self.object)

            try:
                # Try to see if a contributor exists without a slot and update that
                contributor = self.contributor_model.objects.get(
                    activity=self.object.parent.adopted,
                    user=self.actor.origin
                )
                contributor.slot = slot
                contributor.save()

            except self.contributor_model.DoesNotExist:
                self.contributor_model.objects.create(
                    activity=self.object.parent.adopted,
                    slot=slot,
                    registration=self.registration,
                    user=self.actor.origin,
                )

    class Meta:
        proxy = True

    @property
    def default_recipients(self):
        if not self.actor.is_local:
            yield self.actor.source
        else:
            yield self.object.parent.source


class PeriodicSlotJoin(SlotJoin):
    @classmethod
    def matches(cls, object, actor):
        return (
            isinstance(object, SubEvent) and object.parent.activity_type == 'PeriodicActivity'
        )

    class Meta:
        proxy = True

    contributor_model = 'bluebottle.time_based.models.PeriodicParticipant'
    registration_model = 'bluebottle.time_based.models.PeriodicRegistration'

    @property
    def remote_contributor(self):
        slot = adapter.adopt(self.object)

        return self.object.parent.adopted.contributors.not_instance_of(Organizer).get(
            user=self.actor.origin,
            periodicparticipant__slot=slot
        )

    def apply(self):
        """
        The supplier creates the slot and adds the user to that slot.
        This will adopt that event for the local user
        """
        if not self.object.is_local:
            slot = adapter.adopt(self.object)

            self.contributor_model.objects.create(
                activity=self.object.parent.adopted,
                slot=slot,
                registration=self.registration,
                user=self.actor.origin,
            )


class ScheduleSlotJoin(SlotJoin):
    @classmethod
    def matches(cls, object, actor):
        return (
            isinstance(object, SubEvent) and object.parent.activity_type == 'ScheduleActivity' and
            not isinstance(actor, Team)
        )

    class Meta:
        proxy = True

    contributor_model = 'bluebottle.time_based.models.ScheduleParticipant'
    registration_model = 'bluebottle.time_based.models.ScheduleRegistration'

    @property
    def remote_contributor(self):
        slot = adapter.adopt(self.object)

        return self.object.parent.adopted.contributors.not_instance_of(Organizer).get(
            user=self.actor.origin,
            scheduleparticipant__slot=slot
        )

    @property
    def local_contributor(self):
        adapter.adopt(self.actor)
        return self.object.parent.origin.contributors.not_instance_of(Organizer).get(
            user=self.actor.origin,
            scheduleparticipant__slot=self.object.origin
        )


class TeamScheduleSlotJoin(SlotJoin):
    contributor = None

    @classmethod
    def matches(cls, object, actor):
        return (
            isinstance(object, SubEvent) and object.parent.activity_type == 'ScheduleActivity' and
            isinstance(actor, Team)
        )

    @property
    def default_recipients(self):
        if not self.actor.is_local:
            yield self.actor.captain.source
        else:
            yield self.object.parent.source

    def apply(self):
        """
        The supplier creates the slot and adds the team to that slot.
        This will adopt the slot and add the team to it.
        """
        if not self.object.is_local:
            adapter.adopt(self.object, team=self.actor.origin)

    class Meta:
        proxy = True

    contributor_model = 'bluebottle.time_based.models.TeamScheduleParticipant'


class DateSlotJoin(SlotJoin):
    @classmethod
    def matches(cls, object, actor):
        return (
            isinstance(object, SubEvent) and object.parent.activity_type == 'DateActivity'
        )

    class Meta:
        proxy = True

    contributor_model = 'bluebottle.time_based.models.DateParticipant'
    registration_model = 'bluebottle.time_based.models.DateRegistration'

    @property
    def local_contributor(self):
        adapter.adopt(self.actor)
        return self.object.parent.origin.contributors.filter(
            remote_user=self.actor.adopted, dateparticipant__slot=self.object.origin
        ).first()

    @property
    def remote_contributor(self):
        return self.object.parent.adopted.contributors.filter(
            user=self.actor.origin, dateparticipant__slot=self.object.adopted
        ).first()

    @property
    def registration(self):
        """Retrieve the registration for the remote user, since the Join was created by the consumer"""
        registration_model = import_string(self.registration_model)
        return registration_model.objects.get(
            remote_user=self.actor.adopted,
            activity=self.object.parent.origin
        )

    def apply(self):
        """For date activities the consumer adds the user to the activity and we replicate that here"""
        self.contributor_model.objects.create(
            activity=self.object.parent.origin,
            remote_user=self.actor.adopted,
            slot=self.object.origin,
            registration=self.registration
        )
