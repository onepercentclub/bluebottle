from datetime import datetime, date

from django.utils.timezone import get_current_timezone, now
from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
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

    def post_save(self, **kwargs):
        registration, _created = DeadlineRegistration.objects.get_or_create(
            activity=self.instance.activity,
            user=self.instance.user,
            status='accepted'
        )
        if not self.instance.registration:
            self.instance.registration = registration
            self.instance.save()

    def is_valid(self):
        return not self.instance.registration
