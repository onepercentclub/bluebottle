from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.module_loading import import_string

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models.actors import Organization
from bluebottle.activity_pub.models.base import ActivityPubModel
from bluebottle.activity_pub.models.events import GoodDeed, CollectCampaign, DoGoodEvent, SubEvent
from bluebottle.activity_pub.models.activities import Activity

from bluebottle.utils.utils import get_subclasses


class Join(Activity):

    """Sent by a follower when a user joins an Event"""
    object = models.ForeignKey(ActivityPubModel, on_delete=models.CASCADE)
    motivation = models.TextField(null=True, blank=True)
    instrument = models.ForeignKey(
        'activity_pub.Team',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='joins',
        help_text=_('Team used when joining a team-schedule activity.'),
    )

    platform = models.ForeignKey(Organization, null=True, on_delete=models.CASCADE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for subclass in get_subclasses(BaseJoin):
            if subclass.matches(self.object):
                self.__class__ = subclass

        self.contributor_model = import_string(self.__class__.contributor_model)


class BaseJoin(Join):
    @classmethod
    def matches(cls, object):
        return False

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.is_local:
            # The join is from a non-local platform. Adopt the actor
            adapter.adopt(self.actor)

            if self.contributor:
                # There already is a contributor. Reapply that contributor
                self.reapply()
            else:
                # Create a new contributor
                self.apply()

    class Meta:
        proxy = True

    @property
    def contributor(self):
        return self.contributor_model.objects.filter(
            activity=self.object.origin, remote_user=self.actor.adopted
        ).first()

    def reapply(self):
        self.contributor.states.reapply(save=True)

    def apply(self):
        """Create a new contributor for the activity"""
        self.actor.refresh_from_db()
        self.contributor_model.objects.create(
            activity=self.object.origin,
            remote_user=self.actor.adopted
        )

    @property
    def default_recipients(self):
        if not self.actor.is_local:
            yield self.actor.source
        else:
            yield self.object.source


class DeedJoin(BaseJoin):
    @classmethod
    def matches(cls, object):
        return isinstance(object, GoodDeed)

    class Meta:
        proxy = True

    contributor_model = 'bluebottle.deeds.models.DeedParticipant'


class CollectCampaignJoin(BaseJoin):
    @classmethod
    def matches(cls, object):
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
        self.actor.refresh_from_db()
        registration_model = import_string(self.registration_model)
        registration_model.objects.create(
            activity=self.object.origin,
            remote_user=self.actor.adopted,
            answer=self.motivation
        )


class DeadlineJoin(RegistrationJoin):
    @classmethod
    def matches(cls, object):
        return isinstance(object, DoGoodEvent) and object.activity_type == 'DeadlineActivity'

    class Meta:
        proxy = True

    registration_model = 'bluebottle.time_based.models.DeadlineRegistration'
    contributor_model = 'bluebottle.time_based.models.DeadlineParticipant'


class PeriodicJoin(RegistrationJoin):
    @classmethod
    def matches(cls, object):
        return isinstance(object, DoGoodEvent) and object.activity_type == 'PeriodicActivity'

    class Meta:
        proxy = True

    def reapply(self):
        """For periodic activities re-joining an activity means we have to start the registration again"""
        self.registration.states.start(save=True)

    registration_model = 'bluebottle.time_based.models.PeriodicRegistration'
    contributor_model = 'bluebottle.time_based.models.PeriodicParticipant'


class DateJoin(RegistrationJoin):
    @classmethod
    def matches(cls, object):
        return isinstance(object, DoGoodEvent) and object.activity_type == 'DateActivity'

    class Meta:
        proxy = True

    registration_model = 'bluebottle.time_based.models.DateRegistration'
    contributor_model = 'bluebottle.time_based.models.DateParticipant'


class ScheduleJoin(RegistrationJoin):
    @classmethod
    def matches(cls, object):
        return isinstance(object, DoGoodEvent) and object.activity_type == 'ScheduleActivity'

    class Meta:
        proxy = True

    registration_model = 'bluebottle.time_based.models.ScheduleRegistration'
    contributor_model = 'bluebottle.time_based.models.ScheduleParticipant'


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
    def matches(cls, object):
        return (
            isinstance(object, SubEvent) and object.parent.activity_type == 'PeriodicActivity'
        )

    class Meta:
        proxy = True

    contributor_model = 'bluebottle.time_based.models.PeriodicParticipant'
    registration_model = 'bluebottle.time_based.models.PeriodicRegistration'

    def apply(self):
        """
        The supplier creates the slot and adds the user to that slot.
        This will adopt that event for the local user
        """
        if not self.object.is_local:
            slot = adapter.adopt(self.object)

            __import__('ipdb').set_trace()
            self.contributor_model.objects.create(
                activity=self.object.parent.adopted,
                slot=slot,
                registration=self.registration,
                user=self.actor.origin,
            )


class ScheduleSlotJoin(SlotJoin):
    @classmethod
    def matches(cls, object):
        return (
            isinstance(object, SubEvent) and object.parent.activity_type == 'ScheduleActivity'
        )

    class Meta:
        proxy = True

    contributor_model = 'bluebottle.time_based.models.ScheduleParticipant'
    registration_model = 'bluebottle.time_based.models.ScheduleRegistration'


class DateSlotJoin(SlotJoin):
    @classmethod
    def matches(cls, object):
        return (
            isinstance(object, SubEvent) and object.parent.activity_type == 'DateActivity'
        )

    class Meta:
        proxy = True

    contributor_model = 'bluebottle.time_based.models.DateParticipant'
    registration_model = 'bluebottle.time_based.models.DateRegistration'

    @property
    def contributor(self):
        """ Return the remote contributor, since the Join was created by the consumer"""
        return self.contributor_model.objects.filter(
            activity=self.object.parent.origin, remote_user=self.actor.adopted
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
