from datetime import datetime, date

from django.db.models import ObjectDoesNotExist
from django.utils.timezone import get_current_timezone, now, make_aware
from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.effects.effects import CreatePeriodicParticipantsEffect
from bluebottle.time_based.models import (
    TimeContribution,
    ContributionTypeChoices,
    DeadlineRegistration,
    DeadlineParticipant,
    ScheduleRegistration,
    ScheduleParticipant, ScheduleSlot, DateRegistration,
)


class CreateTimeContributionEffect(Effect):
    title = _('Create contribution')
    template = 'admin/create_deadline_time_contribution.html'

    def post_save(self, **kwargs):
        activity = self.instance.activity
        tz = get_current_timezone()
        if hasattr(self.instance, "slot") and self.instance.slot:
            contribution_date = self.instance.slot.start
        elif activity.start and activity.start > date.today():
            contribution_date = make_aware(
                datetime.combine(activity.start, datetime.min.replace(hour=12).time()),
                tz
            )
        elif activity.deadline and activity.deadline < date.today():
            contribution_date = make_aware(
                datetime.combine(activity.deadline, datetime.min.replace(hour=12).time()),
                tz
            )
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
        return _("Create contribution")


class CreateRegisteredTimeContributionEffect(Effect):
    title = _('Create contribution')
    template = 'admin/create_deadline_time_contribution.html'

    def post_save(self, **kwargs):
        activity = self.instance.activity

        contribution = TimeContribution(
            contributor=self.instance,
            contribution_type=ContributionTypeChoices.period,
            value=activity.duration,
            start=activity.start or now()
        )

        contribution.execute_triggers(**self.options)
        contribution.save()

    def __str__(self):
        return _("Create contribution")


class CreateScheduleContributionEffect(Effect):
    title = _("Create contribution")
    template = "admin/create_deadline_time_contribution.html"

    def post_save(self, **kwargs):
        try:
            self.instance.contributions.get(
                timecontribution__contribution_type="period"
            )
        except ObjectDoesNotExist:
            slot = self.instance.slot
            if slot and slot.start and slot.end:
                contribution = TimeContribution(
                    contributor=self.instance,
                    contribution_type=ContributionTypeChoices.period,
                    value=slot.duration,
                    start=slot.start,
                    end=slot.end,
                    status=(
                        "succeeded"
                        if slot.end < now()
                        else "new"
                    ),
                )

            else:
                contribution = TimeContribution(
                    contributor=self.instance,
                    contribution_type=ContributionTypeChoices.period,
                    value=self.instance.activity.duration,
                    start=now(),
                    end=now() + self.instance.activity.duration,
                    status="new",
                )

            contribution.execute_triggers(**self.options)
            contribution.save()

    def __str__(self):
        return _('Create contribution')


class CreateRegistrationEffect(Effect):
    title = _('Create registration for this participant')
    template = 'admin/create_deadline_registration.html'

    def without_registration(self):
        return not self.instance.registration

    def get_registration_model(self):
        if isinstance(self.instance, DeadlineParticipant):
            return DeadlineRegistration
        if isinstance(self.instance, ScheduleParticipant):
            return ScheduleRegistration
        raise ValueError(f'No registration defined for participant model {self.instance.__class__.__name__}')

    def post_save(self, **kwargs):
        registration = self.get_registration_model().objects.create(
            activity=self.instance.activity,
            user=self.instance.user,
            status='accepted'
        )
        self.instance.registration = registration
        self.instance.save()

    conditions = [
        without_registration
    ]


class CreateDateRegistrationEffect(Effect):
    title = _('Create or assign registration for this participant')
    template = 'admin/create_date_registration.html'

    def pre_save(self, **kwargs):

        if not self.instance.activity_id:
            # we need this for inline admin, so we can add users to a slot
            self.instance.activity = self.instance.slot.activity
        self.instance.registration = self.instance.activity.registrations.filter(user=self.instance.user).first()

    def post_save(self, **kwargs):
        if not self.instance.registration:
            self.instance.registration = DateRegistration.objects.create(
                activity=self.instance.activity,
                user=self.instance.user,
            )

            self.instance.save()


class CreatePeriodicPreparationTimeContributionEffect(CreatePeriodicParticipantsEffect):
    title = _("Create preparation time contribution")
    template = "admin/create_preparation_time_contribution.html"

    def is_first_participant(self):
        """First participant"""
        return (
            self.instance.registration
            and self.instance.registration.participants.count() == 0
        )

    conditions = [is_first_participant]

    def post_save(self, **kwargs):
        activity = self.instance.activity
        if activity.preparation:
            start = self.instance.created
            contribution = TimeContribution(
                contributor=self.instance,
                contribution_type=ContributionTypeChoices.preparation,
                value=activity.preparation,
                start=start,
            )
            contribution.save()


class DeleteRelatedRegistrationEffect(Effect):
    title = _('Delete related registration')
    template = 'admin/delete_registration.html'

    def post_delete(self, **kwargs):
        self.instance.registration.delete()

    def is_valid(self):
        return self.instance.registration.participants.count() == 1

    def __str__(self):
        return _('Delete related registration')


class CreateScheduleSlotEffect(Effect):
    title = _('Create slot for this participant')
    template = 'admin/create_schedule_slot.html'

    def without_slot(self):
        return not self.instance.slot_id

    def post_save(self, **kwargs):
        activity = self.instance.activity
        self.instance.slot = ScheduleSlot.objects.create(
            activity=activity,
            is_online=activity.is_online,
            location_id=activity.location_id,
            location_hint=activity.location_hint,
            duration=activity.duration,
            online_meeting_url=activity.online_meeting_url,
        )
        self.instance.save()

    conditions = [without_slot]
