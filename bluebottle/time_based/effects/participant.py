from datetime import datetime, date

from django.utils.timezone import get_current_timezone, now
from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.effects.effects import CreatePeriodicParticipantsEffect
from bluebottle.time_based.models import TimeContribution, ContributionTypeChoices, DeadlineRegistration


class CreateTimeContributionEffect(Effect):
    title = _('Create contribution')
    template = 'admin/create_deadline_time_contribution.html'

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
        return _('Create contribution')


class CreateRegistrationEffect(Effect):
    title = _('Create registration for this participant')
    template = 'admin/create_deadline_participant.html'

    def without_registration(self):
        return not self.instance.registration

    def post_save(self, **kwargs):
        registration = DeadlineRegistration.objects.create(
            activity=self.instance.activity,
            user=self.instance.user,
            status='accepted'
        )
        self.instance.registration = registration
        self.instance.save()

    conditions = [
        without_registration
    ]


class CreatePeriodicPreparationTimeContributionEffect(CreatePeriodicParticipantsEffect):
    title = _("Create preparation time contribution")
    template = "admin/create_preparation_time_contribution.html"

    def is_first_participant(self):
        return (
            self.instance.registration
            and self.instance.registration.participants.count() == 0
        )

    conditions = [is_first_participant]

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
