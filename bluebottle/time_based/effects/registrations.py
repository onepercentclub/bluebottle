from dateutil.relativedelta import relativedelta
from django.utils.timezone import now
from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.models import PeriodicSlot, Team


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
        slot = self.instance.activity.slots.last()
        if not slot:
            slot = PeriodicSlot.objects.create(
                activity=self.instance,
                start=now(),
                end=now() + relativedelta(**{self.instance.period: 1}),
                status='running',
                duration=self.instance.duration
            )
        participant = self.instance.participants.first()
        if participant:
            participant.slot = slot
            participant.save()
            participant.contributions.update(start=slot.start)
        else:
            self.instance.participants.create(
                activity=self.instance.activity,
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
