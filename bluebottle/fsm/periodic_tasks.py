from django.utils.translation import ugettext_lazy as _


class ModelPeriodicTask(object):

    def __init__(self, model, field='states'):
        self.model = model
        self.field = field

    def get_queryset(self):
        raise NotImplementedError

    effects = []

    def execute(self):
        for instance in self.get_queryset():
            for effect_class in self.effects:
                effect = effect_class(instance)
                if effect.is_valid:
                    effect.execute()
                    instance.save()

    def __unicode__(self):
        return unicode(_("Periodic task") + ": " + self.__class__.__name__)
