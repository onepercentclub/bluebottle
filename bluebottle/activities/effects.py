from django.template.loader import render_to_string
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from bluebottle.activities.models import (
    Contributor, Organizer, EffortContribution, Activity, Team, Invite
)
from bluebottle.fsm.effects import Effect, TransitionEffect


class CreateOrganizer(Effect):
    "Create an organizer for the activity"

    display = False

    def post_save(self, **kwargs):
        Organizer.objects.get_or_create(
            activity=self.instance,
            defaults={'user': self.instance.owner}
        )

    def __str__(self):
        return str(_('Create organizer'))


class CreateOrganizerContribution(Effect):
    "Create an effort contribution for the organizer or participant of the activity"

    display = False

    def pre_save(self, effects):
        self.contribution = EffortContribution(
            contributor=self.instance,
            contribution_type=EffortContribution.ContributionTypeChoices.organizer
        )
        effects.extend(self.contribution.execute_triggers())

    def post_save(self, **kwargs):
        self.contribution.contributor_id = self.contribution.contributor.pk
        self.contribution.save()

    def __str__(self):
        return str(_('Create effort contribution'))


class SetContributionDateEffect(Effect):
    "Set the contribution date"

    conditions = []
    display = False
    template = 'admin/create_preparation_time_contribution.html'

    def pre_save(self, **kwargs):
        if self.instance.contribution_type == 'organizer':
            self.instance.start = now()

    def __str__(self):
        return _('Set the contribution date.')


class CreateTeamEffect(Effect):
    "Create a team"

    display = True
    title = _('Create a team')
    template = 'admin/create_team.html'

    @property
    def is_valid(self):
        return (
            super().is_valid and
            not self.instance.team and
            self.instance.activity.team_activity == Activity.TeamActivityChoices.teams
        )

    def pre_save(self, **kwargs):
        if self.instance.accepted_invite:
            self.instance.team = self.instance.accepted_invite.contributor.team

    def post_save(self, **kwargs):
        if not self.instance.team:
            self.instance.team = Team.objects.create(
                owner=self.instance.user,
                activity=self.instance.activity,
            )
            self.instance.save()


class BaseTeamContributionTransitionEffect(Effect):
    display = False

    def __eq__(self, other):
        return (
            isinstance(other, BaseTeamContributionTransitionEffect) and
            self.transition == other.transition and
            self.instance == other.instance
        )

    @classmethod
    def render(cls, effects):
        effect = effects[0]
        users = [member.user for member in effect.instance.members]
        context = {
            'users': users,
            'transition': cls.transition.name
        }
        return render_to_string(cls.template, context)

    @property
    def contributions(self):
        for contributor in self.instance.members.all():
            for contribution in contributor.contributions.all():
                yield contribution

    @property
    def is_valid(self):
        return (
            super().is_valid and
            any(
                self.transition in contribution.states.possible_transitions() for
                contribution in self.contributions
            ) and
            any(
                all(condition(contribution) for condition in self.contribution_conditions)
                for contribution in self.contributions
            )
        )

    def pre_save(self, effects):
        self.transitioned_contributions = []
        for contribution in self.contributions:
            effect = TransitionEffect(self.transition)(contribution)

            if effect.is_valid:
                self.transitioned_contributions.append(contribution)
                effect.pre_save(effects=effects)
                effects.append(effect)

                contribution.execute_triggers(effects=effects)

    def post_save(self):
        for contribution in self.transitioned_contributions:
            try:
                contribution.contributor.refresh_from_db()
                contribution.save()
            except Contributor.DoesNotExist:
                # Contributor does not exist anymore. Do not save contribution
                pass


def TeamContributionTransitionEffect(transition, contribution_conditions=None):
    _transition = transition
    _contribution_conditions = contribution_conditions or []

    class _TeamContributionTransitionEffect(BaseTeamContributionTransitionEffect):
        transition = _transition
        contribution_conditions = _contribution_conditions

    return _TeamContributionTransitionEffect


class CreateInviteEffect(Effect):
    "Create an invite for the contributor"

    display = False

    def pre_save(self, **kwargs):
        if not self.instance.invite_id:
            self.instance.invite = Invite()
            self.instance.invite.save()

    def __str__(self):
        return str(_('Create invite'))


class CreateInviteForOwnerEffect(Effect):
    "Create an invite for the new owner"

    display = False

    def pre_save(self, **kwargs):
        participant = self.instance.members.filter(user=self.instance.owner).first()
        if participant:
            participant.invite = Invite()
            participant.invite.save()

    def __str__(self):
        return str(_('Create invite  or owner'))


class ResetTeamParticipantsEffect(Effect):
    "Remove all contributors from the team"
    display = True

    def post_save(self, **kwargs):
        for contributor in self.instance.members.exclude(user=self.instance.owner):
            contributor.delete()

    def __str__(self):
        return str(_('Reset Team'))


class DeleteRelatedContributionsEffect(Effect):
    "Delete the related contributions when participant is deleted manually"
    display = True

    def pre_save(self, **kwargs):
        self.instance.contributions.all().delete()

    def __str__(self):
        return str(_("Delete related contributions"))
