from django.utils.translation import gettext as _
from django.contrib.contenttypes.models import ContentType

from bluebottle.fsm.effects import Effect
from bluebottle.impact.models import ImpactGoal
from bluebottle.activities.models import EffortContribution, Organizer


class UpdateImpactGoalEffect(Effect):
    title = _('Update impact goals')
    display = False

    def post_save(self, **kwargs):
        activity = self.instance.contributor.activity

        goals = ImpactGoal.objects.filter(activity=activity)

        for goal in goals:
            amount = goal.target / activity.target

            goal.realized_from_contributions = amount * len(
                EffortContribution.objects.exclude(
                    contributor__polymorphic_ctype=ContentType.objects.get_for_model(Organizer)
                ).filter(
                    contributor__activity=activity,
                    status__in=['succeeded', 'new', ]
                )
            )
            goal.save()

    @property
    def is_valid(self):
        return getattr(self.instance.contributor.activity, 'enable_impact', False)


class UpdateImpactGoalsForActivityEffect(Effect):
    title = _('Update impact goals')
    display = False

    def post_save(self, **kwargs):
        activity = self.instance

        goals = ImpactGoal.objects.filter(activity=activity)

        for goal in goals:
            amount = goal.target / activity.target

            if activity.enable_impact:
                goal.realized_from_contributions = amount * len(
                    EffortContribution.objects.exclude(
                        contributor__polymorphic_ctype=ContentType.objects.get_for_model(Organizer)
                    ).filter(
                        contributor__activity=activity,
                        status__in=['succeeded', 'new', ]
                    )
                )
            else:
                goal.realized_from_contributions = 0

            goal.save()
