from django.utils.translation import gettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.impact.models import ImpactGoal


class UpdateImpactGoalEffect(Effect):
    title = _('Update impact goals')
    display = False

    def post_save(self, **kwargs):
        activity = self.instance.contributor.activity

        goals = ImpactGoal.objects.filter(activity=activity)

        for goal in goals:
            goal.update()
            goal.save()

    @property
    def is_valid(self):
        return self.instance.contributor and getattr(self.instance.contributor.activity, 'enable_impact', False)


class UpdateImpactGoalsForActivityEffect(Effect):
    title = _('Update impact goals')
    display = False

    def post_save(self, **kwargs):
        activity = self.instance

        goals = ImpactGoal.objects.filter(activity=activity)

        for goal in goals:
            goal.update()
            goal.save()
