from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.db.models import F
from django.template.loader import render_to_string
from django.utils.timezone import get_current_timezone, now
from django.utils.translation import gettext as _

from bluebottle.follow.models import unfollow
from bluebottle.fsm.effects import Effect
from bluebottle.time_based.models import (
    ContributionTypeChoices,
    PeriodicSlot,
    TimeContribution,
    PeriodicParticipant
)


class CreateSlotTimeContributionEffect(Effect):
    title = _('Create contribution')
    template = 'admin/create_slot_time_contribution.html'

    def post_save(self, **kwargs):
        slot = self.instance.slot
        if slot.start and slot.duration:
            end = slot.start + slot.duration
            contribution = TimeContribution(
                contributor=self.instance.participant,
                contribution_type=ContributionTypeChoices.date,
                slot_participant=self.instance,
                value=slot.duration,
                start=slot.start,
                end=end
            )
            contribution.save()


class CreatePreparationTimeContributionEffect(Effect):
    title = _('Create preparation time contribution')
    template = 'admin/create_preparation_time_contribution.html'

    def post_save(self, **kwargs):
        activity = self.instance.activity
        if activity.preparation:
            start = now()
            contribution = TimeContribution(
                contributor=self.instance,
                contribution_type=ContributionTypeChoices.preparation,
                value=activity.preparation,
                start=start,
            )
            contribution.save()


class CreateSchedulePreparationTimeContributionEffect(Effect):
    title = _("Create preparation time contribution")
    template = "admin/create_preparation_time_contribution.html"

    def post_save(self, **kwargs):
        activity = self.instance.activity
        start = self.instance.slot.start if self.instance.slot and self.instance.slot.start else now()
        if activity.preparation:
            contribution = TimeContribution(
                contributor=self.instance,
                contribution_type=ContributionTypeChoices.preparation,
                value=activity.preparation,
                start=start,
            )
            contribution.save()


class RelatedPreparationTimeContributionEffect(Effect):
    title = _("Create preparation time contribution")
    template = "admin/create_preparation_time_contribution.html"
    display = False

    def post_save(self, **kwargs):
        if self.instance.preparation:
            TimeContribution.objects.filter(
                contribution_type=ContributionTypeChoices.preparation,
                contributor__activity=self.instance,
            ).update(value=self.instance.preparation)

            for participant in self.instance.participants.exclude(
                contributions__timecontribution__contribution_type=ContributionTypeChoices.preparation
            ):
                contribution = TimeContribution(
                    contributor=participant,
                    contribution_type=ContributionTypeChoices.preparation,
                    value=self.instance.preparation,
                    start=now(),
                )
                contribution.save()
        else:
            TimeContribution.objects.filter(
                contribution_type=ContributionTypeChoices.preparation,
                contributor__activity=self.instance,
            ).delete()


class UpdateSlotTimeContributionEffect(Effect):
    title = _('Update related contributions')
    template = 'admin/update_slot_time_contribution.html'

    def post_save(self, **kwargs):
        slot = self.instance
        for participant in slot.accepted_participants.all():
            for contribution in participant.contributions.all():
                contribution.start = slot.start
                contribution.save()


class CreateOverallTimeContributionEffect(Effect):
    title = _('Create contribution')
    template = 'admin/create_period_time_contribution.html'

    def post_save(self, **kwargs):
        activity = self.instance.activity
        tz = get_current_timezone()
        if activity.start and activity.start > date.today():
            contribution_date = tz.localize(datetime.combine(activity.start, datetime.min.replace(hour=12).time()))
        elif activity.deadline and activity.deadline < date.today():
            contribution_date = tz.localize(datetime.combine(activity.deadline, datetime.min.replace(hour=12).time()))
        else:
            contribution_date = now()

        contribution = TimeContribution(
            contributor=self.instance,
            contribution_type=ContributionTypeChoices.period,
            value=activity.duration,
            start=contribution_date
        )
        contribution.execute_triggers(**self.options)
        contribution.save()

    def __str__(self):
        return _('Create overall contribution')

    @property
    def is_valid(self):
        return super().is_valid and self.instance.activity.duration_period == 'overall'


class SetEndDateEffect(Effect):
    title = _('End the activity')
    template = 'admin/set_end_date.html'

    def pre_save(self, **kwargs):
        self.instance.deadline = date.today() - timedelta(days=1)


class ClearDeadlineEffect(Effect):
    title = _('Clear the deadline of the activity')
    template = 'admin/clear_deadline.html'

    def pre_save(self, **kwargs):
        self.instance.deadline = None


class RescheduleOverallPeriodActivityDurationsEffect(Effect):
    display = False

    def post_save(self, **kwargs):
        if self.instance.duration_period == 'overall':
            tz = get_current_timezone()

            if self.instance.start:
                start = tz.localize(datetime.combine(self.instance.start, datetime.min.time()))
            else:
                start = F('start')

            if self.instance.deadline:
                end = tz.localize(datetime.combine(self.instance.deadline, datetime.min.time()))
            else:
                end = None

            self.instance.durations.update(
                start=start,
                end=end,
                value=self.instance.duration
            )


class RescheduleSlotDurationsEffect(Effect):
    display = False

    def post_save(self, **kwargs):
        if self.instance.start and self.instance.duration:
            self.instance.durations.update(
                start=self.instance.start,
                end=self.instance.start + self.instance.duration,
                value=self.instance.duration
            )


class BaseActiveDurationsTransitionEffect(Effect):
    display = True
    template = 'admin/transition_durations.html'

    @classmethod
    def render(cls, effects):
        effect = effects[0]
        users = [duration.contributor.user for duration in effect.instance.active_durations]
        context = {
            'users': users,
            'transition': cls.transition.name
        }
        return render_to_string(cls.template, context)

    @property
    def is_valid(self):
        return (
            super().is_valid and
            any(
                self.transition in duration.states.possible_transitions() for
                duration in self.instance.active_durations
            )
        )

    def pre_save(self, effects):
        self.transitioned_durations = []
        for duration in self.instance.active_durations:
            if self.transition in duration.states.possible_transitions():
                self.transitioned_durations.append(duration)
                self.transition.execute(duration.states)

    def post_save(self):
        for duration in self.transitioned_durations:
            duration.save()


def ActiveTimeContributionsTransitionEffect(transition, conditions=None):
    _transition = transition
    _conditions = conditions or []

    class _ActiveDurationsTransitionEffect(BaseActiveDurationsTransitionEffect):
        transition = _transition
        conditions = _conditions

    return _ActiveDurationsTransitionEffect


class UnlockUnfilledSlotsEffect(Effect):
    """
    Open up slots that are no longer full
    """

    template = 'admin/unlock_activity_slots.html'

    @property
    def display(self):
        return len(self.slots)

    @property
    def slots(self):
        slots = self.instance.activity.slots.filter(status='full')
        return [slot for slot in slots.all() if slot.accepted_participants.count() < slot.capacity]

    def post_save(self, **kwargs):
        for slot in self.slots:
            slot.states.unlock(save=True)

    def __repr__(self):
        return '<Effect: Unlock unfilled slots for {activity}>'.format(activity=self.instance.activity)

    def __str__(self):
        return _('Unlock unfilled slots for {activity}').format(activity=self.instance.activity)


class LockFilledSlotsEffect(Effect):
    """
    Lock slots that will be full
    """

    template = 'admin/lock_activity_slots.html'

    @property
    def display(self):
        return len(self.slots)

    @property
    def slots(self):
        slots = self.instance.activity.slots.filter(status='open')
        return [
            slot for slot in slots.all()
            if slot.capacity and slot.accepted_participants.count() >= slot.capacity
        ]

    def post_save(self, **kwargs):
        for slot in self.slots:
            slot.states.lock(save=True)

    def __repr__(self):
        return '<Effect: Lock filled slots for by {}>'.format(self.instance.activity)

    def __str__(self):
        return _('Lock filled slots for {activity}').format(activity=self.instance.activity)


class CreateFirstSlotEffect(Effect):

    template = 'admin/time_based/periodic/create_first_slot.html'

    def is_valid(self):
        return self.instance.slots.count() == 0

    def post_save(self):
        tz = get_current_timezone()
        start = tz.localize(
            datetime.combine(self.instance.start, datetime.min.time())
        ) if self.instance.start else now()

        PeriodicSlot.objects.create(
            activity=self.instance,
            start=start,
            end=start + relativedelta(**{self.instance.period: 1}),
            duration=self.instance.duration
        )


class CreateNextSlotEffect(Effect):

    def post_save(self):
        activity = self.instance.activity
        if activity.status == 'open':

            slot = PeriodicSlot.objects.create(
                activity=activity,
                start=self.instance.end,
                end=self.instance.end + relativedelta(**{activity.period: 1}),
                duration=activity.duration
            )

            slot.states.start(save=True)


class CreatePeriodicParticipantsEffect(Effect):

    def post_save(self):
        for registration in self.instance.activity.registrations.filter(
            status="accepted"
        ):
            PeriodicParticipant.objects.create(
                user=registration.user,
                slot=self.instance,
                activity=self.instance.activity,
                registration=registration,
            )


class RescheduleScheduleSlotContributions(Effect):
    template = 'admin/time_based/periodic/reschedule_schedule_slot.html'

    def post_save(self):
        for participant in self.instance.participants.all():
            for contribution in participant.contributions.all():
                contribution.start = self.instance.start
                if self.instance.duration and self.instance.start:
                    contribution.end = self.instance.start + self.instance.duration
                else:
                    contribution.end = None
                contribution.value = self.instance.duration
                contribution.save()


class RescheduleDateSlotContributions(Effect):
    template = 'admin/time_based/dateactivityslot/reschedule_date_slot.html'

    def post_save(self):
        for slot_participant in self.instance.slot_participants.all():
            for contribution in slot_participant.contributions.all():
                contribution.start = self.instance.start
                if self.instance.duration and self.instance.start:
                    contribution.end = self.instance.start + self.instance.duration
                else:
                    contribution.end = None
                contribution.value = self.instance.duration
                contribution.save()


class CheckPreparationTimeContributionEffect(Effect):
    """
    Check the status of preparation time contribution
    """

    template = 'admin/check_preparation_time_contribution.html'

    def post_save(self, **kwargs):
        participant = self.instance.participant
        participant.refresh_from_db()
        has_registrations = participant.slot_participants.filter(
            status__in=['registered']
        ).exists()
        prep_time = participant.contributions.filter(
            timecontribution__contribution_type=ContributionTypeChoices.preparation
        ).first()
        if prep_time:
            if not has_registrations and prep_time.status in ['succeeded', 'new']:
                prep_time.states.fail(save=True)
            elif (
                participant.status in ['new', 'accepted', 'succeeded'] and
                has_registrations and
                prep_time.status == 'failed'
            ):
                prep_time.states.succeed(save=True)

    def is_valid(self):
        participant = self.instance.participant
        has_prep_time = participant.contributions.filter(
            timecontribution__contribution_type=ContributionTypeChoices.preparation
        ).exists()
        return has_prep_time

    def __repr__(self):
        return '<Effect: Check preparation time contribution>'

    def __str__(self):
        return _('Check preparation time contribution for {participant}').format(participant=self.instance.user)


class SlotParticipantUnFollowActivityEffect(Effect):
    "Unfollow the activity"

    template = "admin/unfollow_effect.html"

    def post_save(self, **kwargs):
        if self.instance.user:
            unfollow(self.instance.user, self.instance.activity)

    def __repr__(self):
        return "<Effect: Unfollow {} by {}>".format(
            self.instance.activity, self.instance.user
        )

    def __str__(self):
        user = self.instance.user
        if not self.instance.user.id:
            user = self.instance.user.full_name
        return _("Unfollow {activity} by {user}").format(
            activity=self.instance.activity, user=user
        )

    @property
    def is_valid(self):
        return (
            self.instance.participant.slot_participants.filter(
                status__in=("registered", "succeeded")
            ).count()
            == 1
        )
