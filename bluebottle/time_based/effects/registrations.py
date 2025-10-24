from dateutil.relativedelta import relativedelta
from django.utils.timezone import now
from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.models import PeriodicSlot, Team, DateRegistration


class CreateParticipantEffect(Effect):
    title = _('Create participant for this registration')
    template = 'admin/create_participant.html'

    def post_save(self, **kwargs):
        self.instance.participants.create(
            activity=self.instance.activity,
            user=self.instance.user,
            registration=self.instance,
        )

    def is_valid(self):
        return not self.instance.participants.exists()


class CreateSlotParticipantEffect(Effect):
    title = _('Create slot participant for this registration')
    template = 'admin/create_participant.html'

    def post_save(self, **kwargs):
        if self.instance.activity.slots.count() == 1:
            slot = self.instance.activity.slots.first()
            if not slot.participants.filter(user=self.instance.user).exists():
                self.instance.participants.create(
                    activity=self.instance.activity,
                    user=self.instance.user,
                    slot=slot,
                    registration=self.instance,
                )

    def is_valid(self):
        return not self.instance.activity.slots.count() == 1


class CreateTeamMemberParticipantEffect(Effect):
    title = _('Create participant for this team member')
    template = 'admin/create_participant.html'

    def post_save(self, **kwargs):
        team_captain = self.instance.team.participants.first()
        self.instance.participants.create(
            activity=self.instance.activity,
            user=self.instance.user,
            slot=team_captain.slot,
            registration=self.instance,
        )

    def is_valid(self):
        return not self.instance.participants.exists()


class CreateInitialPeriodicParticipantEffect(Effect):
    title = _("Create initial periodic participant for this registration")
    template = "admin/create_participant.html"

    def post_save(self, **kwargs):
        self.instance.participants.create(
            activity=self.instance.activity,
            user=self.instance.user,
            registration=self.instance,
        )

    def is_valid(self):
        return not self.instance.participants.exists()


class AdjustInitialPeriodicParticipantEffect(Effect):
    title = _("Adjust initial periodic participant and connect to slot")
    template = "admin/adjust_participant.html"

    def post_save(self, **kwargs):
        activity = self.instance.activity
        slot = activity.slots.last()
        if not slot:
            slot = PeriodicSlot.objects.create(
                activity=activity,
                start=now(),
                end=now() + relativedelta(**{activity.period: 1}),
                status='running',
                duration=activity.duration
            )
        participant = self.instance.participants.first()
        if participant:
            participant.slot = slot
            participant.save()
            participant.contributions.update(start=slot.start)
        else:
            self.instance.participants.create(
                activity=activity,
                user=self.instance.user,
                slot=slot,
                registration=self.instance,
            )

    def is_valid(self):
        return not self.instance.participants.filter(slot__isnull=False).exists()


class CreateTeamEffect(Effect):
    title = _('Create team for this registration')
    template = 'admin/create_team.html'

    def post_save(self, **kwargs):
        self.instance.team = Team.objects.create(
            activity=self.instance.activity,
            user=self.instance.user,
            registration=self.instance,
        )

    def is_valid(self):
        return not self.instance.team


class DeleteRegistrationEffect(Effect):

    title = _('Delete registration if it no longer has participants')
    template = 'admin/delete_registration.html'

    def post_save(self, **kwargs):
        try:
            registration = self.instance.registration
            if not registration.participants.exists():
                registration.delete()
        except DateRegistration.DoesNotExist:
            pass

    def is_valid(self):
        if not self.instance.registration_id:
            return False
        registration = self.instance.registration
        return not registration.participants.exists()
