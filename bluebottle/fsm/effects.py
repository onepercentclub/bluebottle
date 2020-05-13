from django.utils.translation import ugettext_lazy as _


class Effect(object):
    effects = []
    save = False
    post_save = False
    conditions = []
    display = True

    def __init__(self, instance):
        self.instance = instance

    def __eq__(self, other):
        return self.instance == other.instance and type(self) == type(other)

    def do(self, post_save, **kwargs):
        if self.is_valid and self.post_save == post_save:
            self.execute(**kwargs)
            if self.save:
                self.instance.save(perform_effects=False)

    def all_effects(self, result=None):
        result = result or []

        if self.is_valid:
            result.append(self)

            for effect in self.effects:
                if effect.is_valid and effect not in result:
                    for sub_effect in effect.all_effects(result):
                        if sub_effect.is_valid and sub_effect not in result:
                            result.append(sub_effect)

        return result

    def execute(self, **kwargs):
        pass

    @property
    def is_valid(self):
        return True


class BaseTransitionEffect(Effect):
    field = 'states'

    @property
    def machine(self):
        return getattr(self.instance, self.field)

    @property
    def transition(self):
        return self.machine.transitions[self.name]

    @property
    def is_valid(self):
        return (
            all(condition(self.machine) for condition in self.conditions) and
            self.transition in self.machine.possible_transitions()
        )

    @property
    def effects(self):
        for effect_class in self.transition.effects:
            yield effect_class(self.instance)

    def execute(self, **kwargs):
        self.transition.execute(self.machine, effects=False)

    def __eq__(self, other):
        return (
            isinstance(other, BaseTransitionEffect) and
            self.transition == other.transition and
            self.instance == other.instance
        )

    def __repr__(self):
        return '<Effect: {}>'.format(self.transition)

    def __unicode__(self):
        return _('Transition %s to %s') % (unicode(self.instance), unicode(self.transition.target))


def TransitionEffect(transition_name, field='states', conditions=None, save=False, post_save=False):
    _field = field
    _conditions = conditions
    _save = save
    _post_save = post_save

    class _TransitionEffect(BaseTransitionEffect):
        name = transition_name
        field = _field
        conditions = _conditions or []
        save = _save
        post_save = _post_save

    return _TransitionEffect


class BaseRelatedTransitionEffect(Effect):
    post_save = True
    display = False

    transition_effect_class = None

    @property
    def machine(self):
        return getattr(self.instance, self.field)

    @property
    def is_valid(self):
        return all(condition(self.machine) for condition in self.conditions)

    @property
    def instances(self):
        value = getattr(self.instance, self.relation)

        if value:
            try:
                for instance in value.all():
                    yield instance
            except AttributeError:
                try:
                    for instance in value:
                        yield instance
                except TypeError:
                    yield value

    @property
    def effects(self):
        for instance in self.instances:
            yield self.transition_effect_class(instance)

    def do(self, post_save, **kwargs):
        if self.is_valid and self.post_save == post_save:
            for effect in self.effects:
                effect.do(post_save, **kwargs)

    def all_effects(self, result=None):
        result = super(BaseRelatedTransitionEffect, self).all_effects(result)
        if self.is_valid:
            for effect in self.effects:
                if effect not in result and effect.is_valid:
                    result.append(effect)

        return result


def RelatedTransitionEffect(_relation, transition_name, field='states', conditions=None):
    _transition_effect_class = TransitionEffect(transition_name, field, save=True, post_save=True)
    _conditions = conditions or []

    class _RelatedTransitionEffect(BaseRelatedTransitionEffect):
        transition_effect_class = _transition_effect_class
        relation = _relation
        conditions = _conditions
        field = 'states'

    return _RelatedTransitionEffect
