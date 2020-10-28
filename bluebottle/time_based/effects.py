from django.utils.translation import ugettext as _

from bluebottle.fsm.effects import Effect
from bluebottle.time_based.models import Duration


def is_overall(effect):
    return effect.instance.activity.duration_period == 'overall'


class CreateOveralDurationEffect(Effect):
    conditions = [is_overall]
    title = _('Create contribution duration')

    def post_save(self, **kwargs):
        Duration.objects.create(
            contribution=self.instance,
            value=self.instance.activity.duration,
            period='overall'
        )

    def __str__(self):
        return _('Create contribution duration')
