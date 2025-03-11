from builtins import str
from builtins import object
from django.utils.translation import gettext_lazy as _
from future.utils import python_2_unicode_compatible
from bluebottle.celery import app


@python_2_unicode_compatible
class ModelPeriodicTask(object):

    def __init__(self, model, field='states'):
        self.model = model
        self.field = field

    def get_queryset(self):
        raise NotImplementedError

    effects = []

    def execute(self):
        for instance in self.get_queryset():
            accumulated_effects = []

            for effect_class in self.effects:
                effect = effect_class(instance)
                if effect.is_valid and effect not in accumulated_effects:
                    effect.pre_save(effects=accumulated_effects)
                    if effect.post_save:
                        instance._postponed_effects.insert(0, effect)
                    accumulated_effects.append(effect)

            instance.save()

    def __str__(self):
        return str(_("Periodic task") + ": " + self.__class__.__name__)


@app.task
def execute_tasks(model):
    from bluebottle.clients.models import Client
    from bluebottle.clients.utils import LocalTenant

    for tenant in Client.objects.all():
        with LocalTenant(tenant, clear_tenant=True):
            for task in model.get_periodic_tasks():
                print(tenant, task)
                task.execute()
