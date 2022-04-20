from django.utils.timezone import now
from django.template.loader import render_to_string

from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.effects import Effect, TransitionEffect
from bluebottle.activities.models import Organizer, EffortContribution, Activity, Team, Invite


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
            self.instance.activity.team_activity == Activity.TeamActivityChoices.teams
        )

    def post_save(self, **kwargs):
        if self.instance.accepted_invite:
            self.instance.team = self.instance.accepted_invite.contributor.team
            self.instance.save()

        if not self.instance.team:
            self.instance.team = Team.objects.create(
                owner=self.instance.user,
                activity=self.instance.activity
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
        self.transitioned_conributions = []
        for contribution in self.contributions:
            effect = TransitionEffect(self.transition)(contribution)

            if effect.is_valid:
                self.transitioned_conributions.append(contribution)
                effect.pre_save(effects=effects)
                effects.append(effect)

                contribution.execute_triggers(effects=effects)

    def post_save(self):
        for contribution in self.transitioned_conributions:
            contribution.save()


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
