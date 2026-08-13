from django.utils.timezone import now
from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect, TransitionEffect
from bluebottle.time_based.states.slots import DateActivitySlotStateMachine


class CreateTeamSlotParticipantsEffect(Effect):
    title = _('Create participants for this team slot')
    template = 'admin/create_team_slot_participants.html'

    def post_save(self, **kwargs):
        for team_member in self.instance.team.team_members.filter(status__in=['new', 'accepted']).all():
            slot = self.instance
            slot.participants.get_or_create(
                user=team_member.user,
                activity=slot.activity,
            )


class SetContributionsStartEffect(Effect):
    title = _('Set contributions start date')
    template = 'admin/time_based/set_contributions_start.html'

    def is_valid(self):
        return not self.instance.start

    def post_save(self, **kwargs):
        if not self.instance.start:
            for participant in self.instance.participants.all():
                participant.contributions.update(start=now())


class LockActivityEffect(Effect):
    title = _('Lock activity')
    display = False

    def is_valid(self):
        return True

    def post_save(self, **kwargs):
        if (
            all(slot.status == 'full' for slot in self.instance.activity.slots.all()) and
            self.instance.activity.status not in ('full', 'registration_closed')
        ):
            self.instance.activity.states.lock(save=True)


class ReopenRegistrationClosedSlotsEffect(Effect):
    """
    Reopen registration_closed slots after the activity reopens, then recalculate
    whether the activity should be full.

    Slot lock triggers can mark the activity full while sibling slots are still
    registration_closed, so capacity is recalculated after those slots are saved.
    """
    display = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slots = []
        self.reopened_slots = []
        try:
            self.slots = list(self.instance.slots.all())
        except (AttributeError, TypeError, ValueError):
            self.slots = []

    def pre_save(self, effects):
        self.reopened_slots = []
        for slot in self.slots:
            if slot.status != 'registration_closed':
                continue
            effect = TransitionEffect(DateActivitySlotStateMachine.reopen)(
                slot, parent=self.instance, **self.options
            )
            if effect.is_valid and effect not in effects:
                effect.pre_save(effects=effects)
                effects.append(effect)
            slot.execute_triggers(effects=effects)
            self.reopened_slots.append(slot)

    def post_save(self, **kwargs):
        if not self.reopened_slots:
            return

        for slot in self.reopened_slots:
            slot.save(run_triggers=False)

        activity = self.instance
        if activity.status not in ('open', 'full'):
            return

        has_open = any(slot.status == 'open' for slot in self.slots)
        if has_open and activity.status == 'full':
            activity.states.unlock(save=True)
            return

        joinable = [
            slot for slot in self.slots
            if slot.status not in ('cancelled', 'deleted', 'draft', 'finished')
        ]
        if (
            activity.status == 'open' and
            joinable and
            all(slot.status == 'full' for slot in joinable)
        ):
            activity.states.lock(save=True)
